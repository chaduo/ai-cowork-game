from datetime import datetime

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import (
    Build,
    BuildCandidate,
    GameDesign,
    GameSpecRevision,
    PlayableVersion,
    Project,
    Release,
    ResourceExtractionBatch,
)
from app.services.checkpoint import CheckpointService
from app.services.lifecycle import ProjectLifecycleService


router = APIRouter(prefix="/api/v1/projects", tags=["releases"])


class ResourceBatchSummary(BaseModel):
    status: str
    candidate_count: int


class ReleaseResponse(BaseModel):
    id: str
    project_id: str
    playable_version_id: str
    number: int
    status: str
    name: str
    description: str
    game_design_revision_id: str | None
    gamespec_revision_id: str | None
    artifact_path: str | None
    artifact_checksum: str | None
    git_commit: str | None
    published_at: datetime
    resource_batch: ResourceBatchSummary


class PublishReviewResponse(BaseModel):
    project_id: str
    eligible: bool
    reason: str | None
    next_release_number: int
    playable_version_id: str | None
    playable_number: int | None
    game_design_revision_id: str | None
    gamespec_revision_id: str | None
    artifact_path: str | None
    artifact_checksum: str | None
    git_commit: str | None
    existing_release: ReleaseResponse | None


class PublishReleaseRequest(BaseModel):
    playable_version_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise ApiError("project_not_found", "Project not found", [], 404)
    return project


def _batch(session: Session, release: Release) -> ResourceExtractionBatch:
    return ProjectLifecycleService(session).ensure_resource_extraction_batch(release)


def _release_response(session: Session, release: Release) -> ReleaseResponse:
    batch = _batch(session, release)
    return ReleaseResponse(
        id=release.id,
        project_id=release.project_id,
        playable_version_id=release.playable_version_id,
        number=release.number,
        status=release.status,
        name=release.name or f"Release v{release.number}",
        description=release.description or "",
        game_design_revision_id=release.game_design_revision_id,
        gamespec_revision_id=release.gamespec_revision_id,
        artifact_path=release.artifact_path,
        artifact_checksum=release.artifact_checksum,
        git_commit=release.git_commit,
        published_at=release.published_at,
        resource_batch=ResourceBatchSummary(
            status=batch.status,
            candidate_count=batch.candidate_count,
        ),
    )


def _latest_release(session: Session, project_id: str) -> Release | None:
    return session.scalar(
        select(Release)
        .where(Release.project_id == project_id)
        .order_by(Release.number.desc())
    )


def _next_release_number(session: Session, project_id: str) -> int:
    latest = _latest_release(session, project_id)
    return (latest.number + 1) if latest else 1


def _review(session: Session, project: Project) -> PublishReviewResponse:
    next_number = _next_release_number(session, project.id)
    version = session.get(PlayableVersion, project.current_playable_version_id) if project.current_playable_version_id else None
    existing = session.scalar(
        select(Release).where(Release.playable_version_id == version.id)
    ) if version else None
    design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
    design_revision_id = design.confirmed_revision_id if design else None
    gamespec_revision_id: str | None = None
    if version:
        candidate = session.get(BuildCandidate, version.candidate_id)
        build = session.get(Build, candidate.build_id) if candidate else None
        gamespec_revision_id = build.gamespec_revision_id if build else None

    reason: str | None = None
    eligible = True
    if version is None:
        eligible = False
        reason = "no_current_playable"
    elif not version.git_commit or not version.artifact_path or not version.artifact_checksum:
        eligible = False
        reason = "incomplete_artifact_provenance"
    elif existing is not None:
        eligible = False
        reason = "already_published"

    return PublishReviewResponse(
        project_id=project.id,
        eligible=eligible,
        reason=reason,
        next_release_number=next_number,
        playable_version_id=version.id if version else None,
        playable_number=version.number if version else None,
        game_design_revision_id=design_revision_id,
        gamespec_revision_id=gamespec_revision_id,
        artifact_path=version.artifact_path if version else None,
        artifact_checksum=version.artifact_checksum if version else None,
        git_commit=version.git_commit if version else None,
        existing_release=_release_response(session, existing) if existing else None,
    )


@router.get("/{project_id}/publish-review", response_model=PublishReviewResponse)
def get_publish_review(project_id: str, request: Request) -> PublishReviewResponse:
    with _session(request) as session:
        return _review(session, _project(session, project_id))


@router.get("/{project_id}/releases", response_model=list[ReleaseResponse])
def list_releases(project_id: str, request: Request) -> list[ReleaseResponse]:
    with _session(request) as session:
        project = _project(session, project_id)
        releases = session.scalars(
            select(Release)
            .where(Release.project_id == project.id)
            .order_by(Release.number.desc())
        ).all()
        response = [_release_response(session, release) for release in releases]
        session.commit()
        return response


@router.get("/{project_id}/releases/{release_id}", response_model=ReleaseResponse)
def get_release(project_id: str, release_id: str, request: Request) -> ReleaseResponse:
    with _session(request) as session:
        _project(session, project_id)
        release = session.get(Release, release_id)
        if release is None or release.project_id != project_id:
            raise ApiError("release_not_found", "Release not found", [], 404)
        response = _release_response(session, release)
        session.commit()
        return response


@router.post("/{project_id}/releases", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
def publish_release(project_id: str, payload: PublishReleaseRequest, request: Request) -> ReleaseResponse:
    with _session(request) as session:
        project = _project(session, project_id)
        existing = session.scalar(
            select(Release).where(
                Release.project_id == project.id,
                Release.playable_version_id == payload.playable_version_id,
            )
        )
        if existing is not None:
            response = _release_response(session, existing)
            session.commit()
            return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(mode="json"))

        try:
            version = session.get(PlayableVersion, payload.playable_version_id)
            if version is None or version.project_id != project.id:
                raise ValueError("playable version not found for project")
            if not version.git_commit or not version.artifact_path or not version.artifact_checksum:
                raise ValueError("playable version has incomplete artifact provenance")
            candidate = session.get(BuildCandidate, version.candidate_id)
            build = session.get(Build, candidate.build_id) if candidate else None
            if candidate is None or build is None:
                raise ValueError("playable version source build not found")
            design = session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
            release = ProjectLifecycleService(session).publish_version(payload.playable_version_id)
            release.name = payload.name.strip()
            release.description = payload.description.strip()
            release.game_design_revision_id = design.confirmed_revision_id if design else None
            release.gamespec_revision_id = build.gamespec_revision_id
            release.artifact_path = version.artifact_path
            release.artifact_checksum = version.artifact_checksum
            release.git_commit = version.git_commit
            session.flush()
            checkpoint = CheckpointService(
                session,
                git=getattr(request.app.state, "project_git", None),
            )
            checkpoint.publish(payload.playable_version_id)
            session.commit()
            return _release_response(session, release)
        except ValueError as cause:
            session.rollback()
            raise ApiError("release_publish_failed", str(cause), [], 409) from cause
