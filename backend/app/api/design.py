import json
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.design import CreatorGameDesignDraft, DesignReadiness
from app.contracts.design_brainstorm import BrainstormInput, BrainstormQuestion
from app.agents.game_design_planner import GameDesignPlannerError, GameDesignProviderNotConfigured
from app.contracts.gamespec import CreatorGameSpec
from app.errors import ApiError
from app.models import GameDesign, GameDesignRevision, GameSpecRevision, Project
from app.services.checkpoint import CheckpointService
from app.services.lifecycle import DesignNotReadyError, ProjectLifecycleService
from app.services.game_design_brainstorm import apply_brainstorm_input, evaluate_first_playable_readiness

router = APIRouter(prefix="/api/v1/projects", tags=["design"])


class DesignResponse(BaseModel):
    project_id: str
    design_id: str | None
    revision_id: str | None
    revision_number: int | None
    confirmed_revision_id: str | None
    confirmed_revision_number: int | None
    status: str
    confirmed_at: datetime | None
    git_commit: str | None = None  # C20: immutable checkpoint of the confirmed GDD
    readiness: DesignReadiness
    draft: CreatorGameDesignDraft
    next_question: BrainstormQuestion | None = None


class GameSpecResponse(BaseModel):
    project_id: str
    revision_id: str
    revision_number: int
    status: str
    confirmed_at: datetime | None
    git_commit: str | None = None  # C20: immutable checkpoint of the confirmed GameSpec
    source_design_revision_id: str | None
    validation_errors: list[dict]
    spec: CreatorGameSpec


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise ApiError("project_not_found", "Project not found", [], 404)
    return project


def _default_draft(project: Project) -> CreatorGameDesignDraft:
    return CreatorGameDesignDraft(
        original_idea=project.original_idea,
        project_title=project.name,
        scenario_id="generic",
        summary={
            "title": project.name,
            "summary": project.original_idea,
            "highlights": [],
            "core_loop": [],
            "progression": [],
        },
    )


def _response(session: Session, project: Project, design: GameDesign | None) -> DesignResponse:
    current_revision = None
    confirmed_revision = None
    if design is not None:
        if design.current_revision_id:
            current_revision = session.get(GameDesignRevision, design.current_revision_id)
        if current_revision is None:
            current_revision = session.scalar(
                select(GameDesignRevision)
                .where(GameDesignRevision.project_id == project.id)
                .order_by(GameDesignRevision.revision_number.desc())
            )
        if design.confirmed_revision_id:
            confirmed_revision = session.get(GameDesignRevision, design.confirmed_revision_id)
    draft = _default_draft(project) if current_revision is None else CreatorGameDesignDraft.model_validate(json.loads(current_revision.content_json))
    readiness = DesignReadiness() if current_revision is None else DesignReadiness.model_validate(json.loads(current_revision.readiness_json))
    return DesignResponse(
        project_id=project.id,
        design_id=design.id if design else None,
        revision_id=current_revision.id if current_revision else None,
        revision_number=current_revision.revision_number if current_revision else None,
        confirmed_revision_id=confirmed_revision.id if confirmed_revision else None,
        confirmed_revision_number=confirmed_revision.revision_number if confirmed_revision else None,
        status=design.status if design else "draft",
        confirmed_at=design.confirmed_at if design else None,
        git_commit=confirmed_revision.git_commit if confirmed_revision else None,
        readiness=readiness,
        draft=draft,
        next_question=draft.clarification.current_question,
    )


def _gamespec_response(project: Project, revision: GameSpecRevision) -> GameSpecResponse:
    try:
        spec = CreatorGameSpec.model_validate_json(revision.content_json)
    except ValidationError as error:
        raise ApiError("gamespec_invalid", "GameSpec is not valid", error.errors(), 422) from error
    return GameSpecResponse(
        project_id=project.id,
        revision_id=revision.id,
        revision_number=revision.revision_number,
        status=revision.status,
        confirmed_at=revision.confirmed_at,
        git_commit=revision.git_commit,
        source_design_revision_id=revision.source_design_revision_id,
        validation_errors=[],
        spec=spec,
    )


@router.get("/{project_id}/design", response_model=DesignResponse)
def get_design(project_id: str, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        return _response(session, project, design)


@router.put("/{project_id}/design", response_model=DesignResponse)
def save_design(project_id: str, payload: CreatorGameDesignDraft, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = ProjectLifecycleService(session).submit_design(project.id, payload.model_dump(mode="json"))
        session.commit()
        return _response(session, project, design)


@router.post("/{project_id}/design/confirm", response_model=DesignResponse)
def confirm_design(project_id: str, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "submitted":
            raise ApiError("design_confirmation_required", "Save the Game Design before confirming it", [], 409)
        try:
            confirmed = ProjectLifecycleService(session).confirm_design(project.id)
        except DesignNotReadyError as cause:
            raise ApiError(
                "design_not_ready",
                "Resolve the Game Design readiness blockers before confirming",
                cause.readiness.blockers + cause.readiness.unresolved_decisions,
                409,
            ) from cause
        # C20 line-114: record the immutable Git checkpoint for the confirmed GDD.
        if confirmed.confirmed_revision_id:
            CheckpointService(session).confirm_gdd(project.id, confirmed.confirmed_revision_id)
        session.commit()
        return _response(session, project, confirmed)


@router.post("/{project_id}/design/brainstorm", response_model=DesignResponse)
def brainstorm_design(project_id: str, payload: BrainstormInput, request: Request) -> DesignResponse:
    planner = getattr(request.app.state, "game_design_planner", None)
    if planner is None:
        raise ApiError(
            "game_design_provider_not_configured",
            "Game Design provider is not configured",
            [],
            503,
        )
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        current = _response(session, project, design).draft
        base = apply_brainstorm_input(current, payload, turn=current.clarification.question_index + (1 if payload.action in {"answer", "free_text"} else 0))
        try:
            planned = planner.plan_turn(project.id, base, payload)
        except GameDesignProviderNotConfigured as cause:
            raise ApiError("game_design_provider_not_configured", str(cause), [], 503) from cause
        except GameDesignPlannerError as cause:
            raise ApiError("game_design_provider_failed", str(cause), [], 502) from cause
        # Provider text can propose the next question and summary, but it cannot
        # erase the reducer's user-confirmed decisions or decide readiness.
        readiness = evaluate_first_playable_readiness(base)
        next_question = None if readiness.first_playable_ready else planned.next_question
        merged_clarification = planned.draft.clarification.model_copy(
            update={
                "status": "ready" if readiness.first_playable_ready else "clarifying",
                "question_index": base.clarification.question_index,
                "custom_input": base.clarification.custom_input,
                "current_question": next_question,
            }
        )
        merged = planned.draft.model_copy(
            update={
                "original_idea": base.original_idea,
                "decisions": base.decisions,
                "clarification": merged_clarification,
                "readiness": readiness,
            }
        )
        saved = ProjectLifecycleService(session).submit_design(project.id, merged.model_dump(mode="json", exclude_none=True))
        session.commit()
        return _response(session, project, saved)


@router.get("/{project_id}/gamespec", response_model=GameSpecResponse)
def get_gamespec(project_id: str, request: Request) -> GameSpecResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        revision = session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project.id)
            .order_by(GameSpecRevision.revision_number.desc())
        )
        if revision is None:
            raise ApiError("gamespec_not_found", "GameSpec has not been prepared", [], 404)
        return _gamespec_response(project, revision)


@router.put("/{project_id}/gamespec", response_model=GameSpecResponse)
def save_gamespec(project_id: str, payload: CreatorGameSpec, request: Request) -> GameSpecResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        revision = ProjectLifecycleService(session).create_gamespec_revision(
            project.id,
            payload.model_dump(mode="json"),
        )
        session.commit()
        return _gamespec_response(project, revision)


@router.post("/{project_id}/gamespec/confirm", response_model=GameSpecResponse)
def confirm_gamespec(project_id: str, request: Request) -> GameSpecResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "confirmed":
            raise ApiError("design_confirmation_required", "Confirm the Game Design before confirming GameSpec", [], 409)
        revision = session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project.id)
            .order_by(GameSpecRevision.revision_number.desc())
        )
        if revision is None:
            raise ApiError("gamespec_not_found", "GameSpec has not been prepared", [], 404)
        response = _gamespec_response(project, revision)
        confirmed = ProjectLifecycleService(session).confirm_gamespec_revision(project.id, revision.id)
        # C20 line-114: record the immutable Git checkpoint for the confirmed GameSpec.
        CheckpointService(session).confirm_gamespec(project.id, confirmed.id)
        session.commit()
        return _gamespec_response(project, confirmed)
