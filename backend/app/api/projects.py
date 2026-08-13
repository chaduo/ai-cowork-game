from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project
from app.errors import ApiError
from app.services.lifecycle import ProjectLifecycleService, ProjectStage

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    original_idea: str = Field(min_length=1)


class ProjectResponse(BaseModel):
    id: str
    name: str
    original_idea: str
    stage: ProjectStage


def _response(session: Session, project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        original_idea=project.original_idea,
        stage=ProjectLifecycleService(session).derive_project_stage(project.id),
    )


def _session(request: Request) -> Session:
    engine = request.app.state.engine
    return Session(engine)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ProjectResponse:
    if not payload.original_idea.strip():
        raise ApiError("validation_error", "Request validation failed", [{"field": "original_idea", "message": "must not be blank"}], 422)
    with _session(request) as session:
        if idempotency_key:
            existing = session.scalar(select(Project).where(Project.idempotency_key == idempotency_key))
            if existing:
                return _response(session, existing)
        service = ProjectLifecycleService(session)
        project = service.create_project(payload.name.strip(), payload.original_idea.strip())
        project.idempotency_key = idempotency_key
        session.commit()
        return _response(session, project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, request: Request) -> ProjectResponse:
    with _session(request) as session:
        project = session.get(Project, project_id)
        if project is None:
            raise ApiError("project_not_found", "Project not found", [], 404)
        return _response(session, project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(request: Request) -> list[ProjectResponse]:
    with _session(request) as session:
        projects = session.scalars(select(Project).order_by(Project.updated_at.desc())).all()
        return [_response(session, project) for project in projects]
