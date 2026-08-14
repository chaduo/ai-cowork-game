import json
from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.design import CreatorGameDesignDraft
from app.errors import ApiError
from app.models import GameDesign, Project
from app.services.lifecycle import ProjectLifecycleService

router = APIRouter(prefix="/api/v1/projects", tags=["design"])


class DesignResponse(BaseModel):
    project_id: str
    design_id: str | None
    status: str
    confirmed_at: datetime | None
    draft: CreatorGameDesignDraft


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
