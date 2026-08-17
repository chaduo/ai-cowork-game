from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import BuildCandidate, HumanPlayReview, PlayableVersion, Project
from app.services.lifecycle import ProjectLifecycleService


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


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


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
            version = ProjectLifecycleService(session).promote_candidate(
                candidate_id,
                git_commit=payload.git_commit,
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
