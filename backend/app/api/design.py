import json
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.design import CreatorGameDesignDraft
from app.contracts.gamespec import CreatorGameSpec
from app.errors import ApiError
from app.models import GameDesign, GameSpecRevision, Project
from app.services.lifecycle import ProjectLifecycleService

router = APIRouter(prefix="/api/v1/projects", tags=["design"])


class DesignResponse(BaseModel):
    project_id: str
    design_id: str | None
    status: str
    confirmed_at: datetime | None
    draft: CreatorGameDesignDraft


class GameSpecResponse(BaseModel):
    project_id: str
    revision_id: str
    revision_number: int
    status: str
    confirmed_at: datetime | None
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


def _response(project: Project, design: GameDesign | None) -> DesignResponse:
    draft = _default_draft(project) if design is None else CreatorGameDesignDraft.model_validate(json.loads(design.content_json))
    return DesignResponse(
        project_id=project.id,
        design_id=design.id if design else None,
        status=design.status if design else "draft",
        confirmed_at=design.confirmed_at if design else None,
        draft=draft,
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
        validation_errors=[],
        spec=spec,
    )


@router.get("/{project_id}/design", response_model=DesignResponse)
def get_design(project_id: str, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        return _response(project, design)


@router.put("/{project_id}/design", response_model=DesignResponse)
def save_design(project_id: str, payload: CreatorGameDesignDraft, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = ProjectLifecycleService(session).submit_design(project.id, payload.model_dump(mode="json"))
        session.commit()
        return _response(project, design)


@router.post("/{project_id}/design/confirm", response_model=DesignResponse)
def confirm_design(project_id: str, request: Request) -> DesignResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "submitted":
            raise ApiError("design_confirmation_required", "Save the Game Design before confirming it", [], 409)
        confirmed = ProjectLifecycleService(session).confirm_design(project.id)
        session.commit()
        return _response(project, confirmed)


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
        session.commit()
        return _gamespec_response(project, confirmed)
