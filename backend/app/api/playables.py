from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Request, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.agents.workspace import WorkspaceEscapeError, WorkspaceManager
from app.models import Build, BuildCandidate, HumanPlayReview, PlayableVersion, Project, Run
from app.services.lifecycle import ProjectLifecycleService
from app.services.checkpoint import CheckpointService
from app.services.playable_assets import PlayableAssetService


router = APIRouter(prefix="/api/v1", tags=["playable-versions"])


class HumanPlayReviewRequest(BaseModel):
    decision: Literal["pending", "accepted", "rejected"]
    notes: str = Field(default="", max_length=4000)
    amendment_status: Literal["not_required", "confirmed", "unconfirmed"] = "not_required"
    drift_status: Literal["clear", "unresolved"] = "clear"


class HumanPlayReviewResponse(BaseModel):
    id: str
    candidate_id: str
    decision: str
    notes: str
    amendment_status: str
    drift_status: str
    reviewed_at: datetime | None


class PromoteRequest(BaseModel):
    git_commit: str = Field(min_length=1, max_length=128)


class PlayableVersionResponse(BaseModel):
    version_id: str
    project_id: str
    candidate_id: str
    number: int
    parent_version_id: str | None
    test_report_id: str
    git_commit: str
    artifact_path: str
    artifact_checksum: str
    created_at: datetime
    is_current: bool = False


class RestoreCandidateResponse(BaseModel):
    candidate_id: str
    project_id: str
    build_id: str
    status: str
    test_gate_status: str
    source_playable_version_id: str
    artifact_path: str | None
    artifact_checksum: str | None


class PlayableAssetResponse(BaseModel):
    path: str
    name: str
    kind: Literal["image", "audio", "font"]
    mime_type: str
    size_bytes: int
    content_url: str


class PlayableAssetInventoryResponse(BaseModel):
    version_id: str
    git_commit: str
    assets: list[PlayableAssetResponse]


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _playable_version(session: Session, project_id: str, version_id: str) -> PlayableVersion:
    version = session.get(PlayableVersion, version_id)
    if version is None or version.project_id != project_id:
        raise ApiError("playable_version_not_found", "Playable Version not found", [], 404)
    return version


@router.get(
    "/projects/{project_id}/playable-versions/{version_id}/assets",
    response_model=PlayableAssetInventoryResponse,
)
def list_playable_assets(project_id: str, version_id: str, request: Request) -> PlayableAssetInventoryResponse:
    with _session(request) as session:
        version = _playable_version(session, project_id, version_id)
        service = PlayableAssetService(request.app.state.project_git)
        try:
            assets = service.list_assets(version)
        except (OSError, ValueError) as cause:
            raise ApiError("playable_assets_unavailable", "Playable assets are not available", [], 409) from cause
        base = f"/api/v1/projects/{quote(project_id, safe='')}/playable-versions/{quote(version_id, safe='')}/assets/content"
        return PlayableAssetInventoryResponse(
            version_id=version.id,
            git_commit=version.git_commit,
            assets=[PlayableAssetResponse(
                path=asset.path,
                name=asset.name,
                kind=asset.kind,
                mime_type=asset.mime_type,
                size_bytes=asset.size_bytes,
                content_url=f"{base}?path={quote(asset.path, safe='')}",
            ) for asset in assets],
        )


@router.get("/projects/{project_id}/playable-versions/{version_id}/assets/content")
def get_playable_asset_content(project_id: str, version_id: str, path: str, request: Request) -> Response:
    with _session(request) as session:
        version = _playable_version(session, project_id, version_id)
        try:
            asset, content = PlayableAssetService(request.app.state.project_git).read_asset(version, path)
        except (OSError, ValueError) as cause:
            raise ApiError("playable_asset_not_found", "Playable asset not found", [], 404) from cause
        headers = {
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": f'"{version.git_commit}:{sha256(path.encode()).hexdigest()}"',
            "X-Content-Type-Options": "nosniff",
        }
        if asset.mime_type == "image/svg+xml":
            headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
        return Response(content=content, media_type=asset.mime_type, headers=headers)


def _serve_candidate_artifact(
    *,
    candidate: BuildCandidate,
    session: Session,
    not_ready_code: str,
) -> FileResponse:
    if candidate.status != "succeeded" or candidate.test_gate_status != "ready":
        raise ApiError(not_ready_code, "Candidate is not ready for human play", [], 409)

    build = session.get(Build, candidate.build_id)
    run = session.scalar(
        select(Run).where(Run.build_id == build.id).order_by(Run.created_at.desc())
    ) if build else None
    if run is None or not run.workspace_path:
        raise ApiError("preview_not_found", "Candidate preview is not available", [], 404)

    root = Path(run.workspace_path)
    try:
        relative_path = WorkspaceManager().validate_member(root, candidate.artifact_path or "")
    except WorkspaceEscapeError as cause:
        raise ApiError(
            "preview_path_rejected",
            "Candidate preview path is not allowed",
            [{"code": cause.code}],
            409,
        ) from cause

    if Path(relative_path).name != "index.html":
        raise ApiError("preview_not_found", "Candidate preview is not available", [], 404)

    artifact = (root.resolve() / relative_path).resolve()
    if not artifact.is_file():
        raise ApiError("preview_not_found", "Candidate preview is not available", [], 404)
    return FileResponse(
        artifact,
        media_type="text/html",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/projects/{project_id}/candidates/{candidate_id}/preview")
def preview_candidate(project_id: str, candidate_id: str, request: Request) -> FileResponse:
    with _session(request) as session:
        candidate = session.get(BuildCandidate, candidate_id)
        if candidate is None or candidate.project_id != project_id:
            raise ApiError("candidate_not_found", "Candidate not found", [], 404)
        return _serve_candidate_artifact(
            candidate=candidate,
            session=session,
            not_ready_code="candidate_preview_not_ready",
        )


@router.get("/projects/{project_id}/playable-versions/{version_id}/preview")
def preview_playable_version(project_id: str, version_id: str, request: Request) -> FileResponse:
    with _session(request) as session:
        version = _playable_version(session, project_id, version_id)

        candidate = session.get(BuildCandidate, version.candidate_id)
        build = session.get(Build, candidate.build_id) if candidate else None
        run = session.scalar(
            select(Run).where(Run.build_id == build.id).order_by(Run.created_at.desc())
        ) if build else None
        if (
            candidate is None
            or candidate.status != "promoted"
            or run is None
            or not run.workspace_path
        ):
            raise ApiError("preview_not_found", "Playable preview is not available", [], 404)

        root = Path(run.workspace_path)
        try:
            relative_path = WorkspaceManager().validate_member(root, version.artifact_path)
        except WorkspaceEscapeError as cause:
            raise ApiError(
                "preview_path_rejected",
                "Playable preview path is not allowed",
                [{"code": cause.code}],
                409,
            ) from cause

        if Path(relative_path).name != "index.html":
            raise ApiError("preview_not_found", "Playable preview is not available", [], 404)

        artifact = (root.resolve() / relative_path).resolve()
        if not artifact.is_file():
            raise ApiError("preview_not_found", "Playable preview is not available", [], 404)
        return FileResponse(
            artifact,
            media_type="text/html",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )


def _candidate(session: Session, candidate_id: str) -> BuildCandidate:
    candidate = session.get(BuildCandidate, candidate_id)
    if candidate is None:
        raise ApiError("candidate_not_found", "Candidate not found", [], 404)
    return candidate


def _review_response(review: HumanPlayReview) -> HumanPlayReviewResponse:
    return HumanPlayReviewResponse(
        id=review.id,
        candidate_id=review.candidate_id,
        decision=review.decision,
        notes=review.notes,
        amendment_status=review.amendment_status,
        drift_status=review.drift_status,
        reviewed_at=review.reviewed_at,
    )


def _restore_response(candidate: BuildCandidate) -> RestoreCandidateResponse:
    return RestoreCandidateResponse(
        candidate_id=candidate.id,
        project_id=candidate.project_id,
        build_id=candidate.build_id,
        status=candidate.status,
        test_gate_status=candidate.test_gate_status,
        source_playable_version_id=candidate.source_playable_version_id or "",
        artifact_path=candidate.artifact_path,
        artifact_checksum=candidate.artifact_checksum,
    )


@router.post("/candidates/{candidate_id}/human-play-review", response_model=HumanPlayReviewResponse)
def record_human_play_review(
    candidate_id: str,
    payload: HumanPlayReviewRequest,
    request: Request,
) -> HumanPlayReviewResponse:
    with _session(request) as session:
        _candidate(session, candidate_id)
        try:
            review = ProjectLifecycleService(session).record_human_play_review(
                candidate_id,
                decision=payload.decision,
                notes=payload.notes,
                amendment_status=payload.amendment_status,
                drift_status=payload.drift_status,
            )
            session.commit()
            return _review_response(review)
        except ValueError as cause:
            session.rollback()
            raise ApiError("human_play_review_failed", str(cause), [], 409) from cause


@router.get("/candidates/{candidate_id}/human-play-review", response_model=HumanPlayReviewResponse)
def get_human_play_review(candidate_id: str, request: Request) -> HumanPlayReviewResponse:
    with _session(request) as session:
        _candidate(session, candidate_id)
        review = ProjectLifecycleService(session).human_play_review(candidate_id)
        if review is None:
            raise ApiError("human_play_review_not_found", "Human Play Review not found", [], 404)
        return _review_response(review)


@router.post("/candidates/{candidate_id}/promote", response_model=PlayableVersionResponse)
def promote_candidate(
    candidate_id: str,
    payload: PromoteRequest,
    request: Request,
) -> PlayableVersionResponse:
    with _session(request) as session:
        _candidate(session, candidate_id)
        try:
            version = CheckpointService(
                session,
                git=request.app.state.project_git,
            ).promote(
                candidate_id,
                test_report_id="persisted",
                verdict="persisted",
            )
            session.commit()
            return PlayableVersionResponse(
                version_id=version.id,
                project_id=version.project_id,
                candidate_id=version.candidate_id,
                number=version.number,
                parent_version_id=version.parent_version_id,
                test_report_id=version.test_report_id,
                git_commit=version.git_commit,
                artifact_path=version.artifact_path,
                artifact_checksum=version.artifact_checksum,
                created_at=version.created_at,
                is_current=True,
            )
        except ValueError as cause:
            session.rollback()
            raise ApiError("candidate_promotion_failed", str(cause), [], 409) from cause


@router.get("/projects/{project_id}/playable-versions", response_model=list[PlayableVersionResponse])
def list_playable_versions(project_id: str, request: Request) -> list[PlayableVersionResponse]:
    with _session(request) as session:
        project = session.get(Project, project_id)
        if project is None:
            raise ApiError("project_not_found", "Project not found", [], 404)
        versions = session.scalars(
            select(PlayableVersion)
            .where(PlayableVersion.project_id == project_id)
            .order_by(PlayableVersion.number.desc())
        ).all()
        return [
            PlayableVersionResponse(
                version_id=version.id,
                project_id=version.project_id,
                candidate_id=version.candidate_id,
                number=version.number,
                parent_version_id=version.parent_version_id,
                test_report_id=version.test_report_id,
                git_commit=version.git_commit,
                artifact_path=version.artifact_path,
                artifact_checksum=version.artifact_checksum,
                created_at=version.created_at,
                is_current=project.current_playable_version_id == version.id,
            )
            for version in versions
        ]


@router.post(
    "/projects/{project_id}/playable-versions/{version_id}/restore",
    response_model=RestoreCandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def restore_playable_version(project_id: str, version_id: str, request: Request) -> RestoreCandidateResponse:
    with _session(request) as session:
        if session.get(Project, project_id) is None:
            raise ApiError("project_not_found", "Project not found", [], 404)
        try:
            candidate = ProjectLifecycleService(session).restore_playable_version(project_id, version_id)
            session.commit()
            return _restore_response(candidate)
        except ValueError as cause:
            session.rollback()
            raise ApiError("playable_restore_failed", str(cause), [], 409) from cause
