import json
from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.fake_game_agent import FakeGameAgent
from app.errors import ApiError
from app.models import Build, BuildCandidate, Project, Run
from app.services.builds import BuildService


router = APIRouter(prefix="/api/v1", tags=["builds"])


class CreateBuildRequest(BaseModel):
    build_id: str | None = Field(default=None, min_length=1, max_length=36)
    run_id: str | None = Field(default=None, min_length=1, max_length=120)
    operation: str = Field(default="create", min_length=1, max_length=80)
    request_text: str = Field(default="", max_length=4000)


class BuildResponse(BaseModel):
    build_id: str
    run_id: str
    project_id: str
    status: str
    attempt: int
    parent_build_id: str | None = None
    gamespec_revision_id: str
    baseline_playable_version_id: str | None = None
    operation: str
    request_text: str
    started_at: datetime | None
    ended_at: datetime | None
    candidate_id: str | None = None
    artifact_path: str | None = None
    diagnostics: list[dict] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _records(session: Session, build_id: str) -> tuple[Build, Run, BuildCandidate | None]:
    build = session.get(Build, build_id)
    if build is None:
        raise ApiError("build_not_found", "Build not found", [], 404)
    run = session.scalar(select(Run).where(Run.build_id == build.id).order_by(Run.created_at.desc()))
    if run is None:
        raise ApiError("run_not_found", "Run not found", [], 404)
    candidate = session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == build.id))
    return build, run, candidate


def _response(session: Session, build_id: str) -> BuildResponse:
    build, run, candidate = _records(session, build_id)
    diagnostics = []
    if candidate and candidate.diagnostics_json:
        diagnostics = json.loads(candidate.diagnostics_json)
    return BuildResponse(
        build_id=build.id,
        run_id=run.id,
        project_id=build.project_id,
        status=build.status,
        attempt=build.attempt,
        parent_build_id=build.parent_build_id,
        gamespec_revision_id=build.gamespec_revision_id,
        baseline_playable_version_id=build.baseline_playable_version_id,
        operation=build.operation,
        request_text=build.request_text,
        started_at=build.started_at,
        ended_at=build.ended_at,
        candidate_id=candidate.id if candidate else None,
        artifact_path=candidate.artifact_path if candidate else None,
        diagnostics=diagnostics,
        error_code=build.failure_code,
        error_message=build.failure_message,
    )


def _service(request: Request, session: Session) -> BuildService:
    agent = getattr(request.app.state, "game_agent", None)
    if agent is None:
        agent = FakeGameAgent()
    return BuildService(session, agent)


@router.post("/projects/{project_id}/builds", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(project_id: str, payload: CreateBuildRequest, request: Request) -> BuildResponse:
    with _session(request) as session:
        if session.get(Project, project_id) is None:
            raise ApiError("project_not_found", "Project not found", [], 404)
        service = _service(request, session)
        try:
            existing = session.get(Build, payload.build_id) if payload.build_id else None
            job = service.create_build(
                project_id,
                operation=payload.operation,
                request_text=payload.request_text,
                build_id=payload.build_id,
                run_id=payload.run_id,
            )
            session.commit()
            await service.execute_build(job.build_id)
            session.commit()
            response = _response(session, job.build_id)
            if existing is not None:
                return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(mode="json"))
            return response
        except ValueError as cause:
            session.rollback()
            raise ApiError("build_start_failed", str(cause), [], 409) from cause


@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(build_id: str, request: Request) -> BuildResponse:
    with _session(request) as session:
        return _response(session, build_id)


@router.post("/builds/{build_id}/cancel", response_model=BuildResponse)
async def cancel_build(build_id: str, request: Request) -> BuildResponse:
    with _session(request) as session:
        _records(session, build_id)
        service = _service(request, session)
        try:
            await service.cancel_build(build_id)
            session.commit()
            return _response(session, build_id)
        except ValueError as cause:
            session.rollback()
            raise ApiError("build_cancel_failed", str(cause), [], 409) from cause


@router.post("/builds/{build_id}/retry", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def retry_build(build_id: str, request: Request) -> BuildResponse:
    with _session(request) as session:
        _records(session, build_id)
        service = _service(request, session)
        try:
            job = service.retry_build(build_id)
            session.commit()
            await service.execute_build(job.build_id)
            session.commit()
            return _response(session, job.build_id)
        except ValueError as cause:
            session.rollback()
            raise ApiError("build_retry_failed", str(cause), [], 409) from cause
