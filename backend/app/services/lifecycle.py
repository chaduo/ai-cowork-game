from enum import StrEnum
import json

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.contracts.design import DesignReadiness
from app.contracts.gamespec import CreatorGameSpec, RuntimeBuildSpec
from app.models import (
    Build,
    BuildCandidate,
    GameDesign,
    GameDesignRevision,
    GameSpecRevision,
    HumanPlayReview,
    PlayableVersion,
    Project,
    Release,
    TestReport,
    utc_now,
)


class ProjectStage(StrEnum):
    DESIGN_DRAFT = "design_draft"
    DESIGN_REVIEW = "design_review"
    GAMESPEC_REVIEW = "gamespec_review"
    READY_TO_BUILD = "ready_to_build"
    BUILDING = "building"
    CANDIDATE_REVIEW = "candidate_review"
    PLAYABLE = "playable"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DesignNotReadyError(ValueError):
    def __init__(self, readiness: DesignReadiness) -> None:
        self.readiness = readiness
        blockers = readiness.blockers or readiness.unresolved_decisions or ["design_not_ready"]
        super().__init__(f"design is not ready: {', '.join(blockers)}")


class ProjectLifecycleService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_project(self, name: str, original_idea: str) -> Project:
        if not name.strip() or not original_idea.strip():
            raise ValueError("name and original_idea are required")
        project = Project(name=name.strip(), original_idea=original_idea)
        self.session.add(project)
        self.session.flush()
        return project

    def submit_design(self, project_id: str, content: dict) -> GameDesign:
        project = self._project(project_id)
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        latest = self.session.scalar(
            select(GameDesignRevision)
            .where(GameDesignRevision.project_id == project.id)
            .order_by(GameDesignRevision.revision_number.desc())
        )
        if latest is not None and latest.status == "draft":
            latest.status = "superseded"
            latest.superseded_at = utc_now()
        readiness = DesignReadiness.model_validate(content.get("readiness", {}))
        revision = GameDesignRevision(
            project_id=project.id,
            revision_number=(latest.revision_number + 1 if latest else 1),
            content_json=json.dumps(content, ensure_ascii=False),
            readiness_json=json.dumps(readiness.model_dump(mode="json"), ensure_ascii=False),
            status="draft",
        )
        self.session.add(revision)
        self.session.flush()
        if design is None:
            design = GameDesign(project_id=project.id, content_json=json.dumps(content, ensure_ascii=False), status="submitted")
            self.session.add(design)
        else:
            design.content_json = json.dumps(content, ensure_ascii=False)
            design.status = "submitted"
        design.current_revision_id = revision.id
        self.session.flush()
        return design

    def confirm_design(self, project_id: str) -> GameDesign:
        design = self._design(project_id)
        if design.status == "confirmed" and design.current_revision_id == design.confirmed_revision_id:
            return design
        if design.status != "submitted":
            raise ValueError("design must be submitted before confirmation")
        revision = self.session.get(GameDesignRevision, design.current_revision_id) if design.current_revision_id else None
        if revision is None:
            raise ValueError("current design revision not found")
        readiness = DesignReadiness.model_validate(json.loads(revision.readiness_json))
        if readiness.status != "ready" or readiness.blockers or readiness.unresolved_decisions:
            raise DesignNotReadyError(readiness)
        for prior in self.session.scalars(
            select(GameDesignRevision).where(
                GameDesignRevision.project_id == project_id,
                GameDesignRevision.status == "confirmed",
                GameDesignRevision.id != revision.id,
            )
        ):
            prior.status = "superseded"
            prior.superseded_at = utc_now()
        revision.status = "confirmed"
        revision.confirmed_at = utc_now()
        design.status = "confirmed"
        design.confirmed_at = utc_now()
        design.confirmed_revision_id = revision.id
        design.content_json = revision.content_json
        self.session.flush()
        return design

    def create_gamespec_revision(self, project_id: str, content: dict) -> GameSpecRevision:
        project = self._project(project_id)
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        source_design_revision_id = (
            design.confirmed_revision_id
            if design is not None and design.status == "confirmed"
            else None
        )
        latest = self.session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project_id)
            .order_by(GameSpecRevision.revision_number.desc())
        )
        revision = GameSpecRevision(
            project_id=project_id,
            revision_number=(latest.revision_number + 1 if latest else 1),
            content_json=json.dumps(content, ensure_ascii=False),
            source_design_revision_id=source_design_revision_id,
            status="draft",
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def confirm_gamespec_revision(self, project_id: str, revision_id: str) -> GameSpecRevision:
        revision = self.session.get(GameSpecRevision, revision_id)
        if revision is None or revision.project_id != project_id:
            raise ValueError("gamespec revision not found")
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project_id))
        if design is None or design.status != "confirmed" or not design.confirmed_revision_id:
            raise ValueError("GameSpec confirmation requires confirmed Game Design")
        if revision.source_design_revision_id is None:
            revision.source_design_revision_id = design.confirmed_revision_id
        for prior in self.session.scalars(
            select(GameSpecRevision).where(
                GameSpecRevision.project_id == project_id,
                GameSpecRevision.status == "confirmed",
                GameSpecRevision.id != revision_id,
            )
        ):
            prior.status = "superseded"
            prior.superseded_at = utc_now()
        revision.status = "confirmed"
        revision.confirmed_at = utc_now()
        self.session.flush()
        return revision

    def validate_gamespec_revision(self, revision_id: str) -> CreatorGameSpec:
        revision = self.session.get(GameSpecRevision, revision_id)
        if revision is None:
            raise ValueError("GameSpec revision not found")
        try:
            return CreatorGameSpec.model_validate_json(revision.content_json)
        except ValidationError as error:
            raise ValueError(f"GameSpec schema is invalid: {error}") from error

    def runtime_build_spec(self, project_id: str) -> RuntimeBuildSpec:
        project = self._project(project_id)
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "confirmed":
            raise ValueError("build requires confirmed Game Design")
        revision = self.session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project.id, GameSpecRevision.status == "confirmed")
            .order_by(GameSpecRevision.revision_number.desc())
        )
        if revision is None:
            raise ValueError("build requires a confirmed GameSpec")
        return self.validate_gamespec_revision(revision.id).to_runtime_build_spec()

    def derive_project_stage(self, project_id: str) -> ProjectStage:
        project = self._project(project_id)
        if project.archived_at:
            return ProjectStage.ARCHIVED
        if project.active_build_id:
            return ProjectStage.BUILDING
        # An unpromoted Candidate is still the user's next decision, even when
        # the project already has an older stable Playable. The current
        # Playable remains safe, but it must not hide the pending Human Gate.
        candidate = self.session.scalar(
            select(BuildCandidate)
            .where(BuildCandidate.project_id == project.id, BuildCandidate.status == "succeeded")
            .order_by(BuildCandidate.created_at.desc())
        )
        if candidate:
            return ProjectStage.CANDIDATE_REVIEW
        if project.current_playable_version_id:
            published = self.session.scalar(
                select(Release).where(Release.playable_version_id == project.current_playable_version_id)
            )
            if published:
                return ProjectStage.PUBLISHED
            return ProjectStage.PLAYABLE
        revision = self.session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project.id)
            .order_by(GameSpecRevision.revision_number.desc())
        )
        if revision and revision.status == "confirmed":
            return ProjectStage.READY_TO_BUILD
        if revision:
            return ProjectStage.GAMESPEC_REVIEW
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design and design.status in {"submitted", "rejected"}:
            return ProjectStage.DESIGN_REVIEW
        return ProjectStage.DESIGN_DRAFT

    def record_human_play_review(
        self,
        candidate_id: str,
        *,
        decision: str,
        notes: str = "",
        amendment_status: str = "not_required",
        drift_status: str = "clear",
    ) -> HumanPlayReview:
        candidate = self.session.get(BuildCandidate, candidate_id)
        if candidate is None:
            raise ValueError("candidate not found")
        if candidate.status == "promoted":
            raise ValueError("Human Play Review is immutable after promotion")
        if candidate.status != "succeeded":
            raise ValueError("Human Play Review requires a succeeded candidate")
        if decision not in {"pending", "accepted", "rejected"}:
            raise ValueError("invalid Human Play Review decision")
        if amendment_status not in {"not_required", "confirmed", "unconfirmed"}:
            raise ValueError("invalid amendment status")
        if drift_status not in {"clear", "unresolved"}:
            raise ValueError("invalid drift status")
        review = self.session.scalar(select(HumanPlayReview).where(HumanPlayReview.candidate_id == candidate.id))
        if review is None:
            review = HumanPlayReview(candidate_id=candidate.id)
            self.session.add(review)
        review.decision = decision
        review.notes = notes.strip()
        review.amendment_status = amendment_status
        review.drift_status = drift_status
        review.reviewed_at = utc_now() if decision != "pending" else None
        self.session.flush()
        return review

    def human_play_review(self, candidate_id: str) -> HumanPlayReview | None:
        return self.session.scalar(select(HumanPlayReview).where(HumanPlayReview.candidate_id == candidate_id))

    def promote_candidate(
        self,
        candidate_id: str,
        *,
        git_commit: str | None = None,
        # Kept as ignored compatibility parameters for pre-C14 callers. Gate
        # truth always comes from persisted TestReport and Candidate fields.
        test_report_id: str | None = None,
        verdict: str | None = None,
        artifact_checksum: str | None = None,
    ) -> PlayableVersion:
        candidate = self.session.get(BuildCandidate, candidate_id)
        if candidate is None:
            raise ValueError("candidate not found")
        if candidate.status == "promoted":
            version = self.session.scalar(select(PlayableVersion).where(PlayableVersion.candidate_id == candidate.id))
            if version is None:
                raise ValueError("promoted candidate is missing its playable version")
            return version
        if candidate.status != "succeeded":
            raise ValueError("only a succeeded candidate can be promoted")
        report = self.session.scalar(select(TestReport).where(TestReport.candidate_id == candidate.id))
        if report is None or report.platform_verdict != "PASSED":
            raise ValueError("promotion requires a persisted PASSED test report")
        if candidate.test_gate_status != "ready":
            raise ValueError("promotion requires a ready candidate test gate")
        review = self.human_play_review(candidate.id)
        if review is None or review.decision != "accepted":
            raise ValueError("promotion requires an accepted Human Play Review")
        if review.amendment_status not in {"not_required", "confirmed"}:
            raise ValueError("promotion is blocked by an unconfirmed Amendment")
        if review.drift_status != "clear":
            raise ValueError("promotion is blocked by unresolved semantic drift")
        if not candidate.artifact_path:
            raise ValueError("promotion requires an artifact path")
        if not candidate.artifact_checksum:
            raise ValueError("promotion requires an artifact checksum")
        if not git_commit or not git_commit.strip():
            raise ValueError("promotion requires a git commit")
        project = self._project(candidate.project_id)
        latest_number = self.session.scalar(
            select(PlayableVersion.number)
            .where(PlayableVersion.project_id == project.id)
            .order_by(PlayableVersion.number.desc())
        ) or 0
        version = PlayableVersion(
            project_id=project.id,
            candidate_id=candidate.id,
            number=latest_number + 1,
            parent_version_id=project.current_playable_version_id,
            test_report_id=report.id,
            git_commit=git_commit.strip(),
            artifact_path=candidate.artifact_path or "",
            artifact_checksum=candidate.artifact_checksum,
        )
        self.session.add(version)
        self.session.flush()
        candidate.status = "promoted"
        project.current_playable_version_id = version.id
        self.session.flush()
        return version

    def restore_playable_version(self, project_id: str, version_id: str) -> BuildCandidate:
        version = self.session.get(PlayableVersion, version_id)
        if version is None:
            raise ValueError("playable version not found")
        if version.project_id != project_id:
            raise ValueError("playable version does not belong to project")
        existing = self.session.scalar(
            select(BuildCandidate)
            .where(
                BuildCandidate.project_id == project_id,
                BuildCandidate.source_playable_version_id == version.id,
                BuildCandidate.status != "promoted",
            )
            .order_by(BuildCandidate.created_at.desc())
        )
        if existing is not None:
            return existing
        source_candidate = self.session.get(BuildCandidate, version.candidate_id)
        if source_candidate is None:
            raise ValueError("playable version source candidate not found")
        source_build = self.session.get(Build, source_candidate.build_id)
        if source_build is None:
            raise ValueError("playable version source build not found")
        project = self._project(project_id)
        attempt = (self.session.scalar(
            select(Build.attempt)
            .where(Build.project_id == project_id)
            .order_by(Build.attempt.desc())
        ) or 0) + 1
        now = utc_now()
        build = Build(
            project_id=project_id,
            gamespec_revision_id=source_build.gamespec_revision_id,
            parent_build_id=source_build.id,
            attempt=attempt,
            status="succeeded",
            operation="restore",
            request_text=f"Restore Playable v{version.number}",
            baseline_playable_version_id=project.current_playable_version_id,
            started_at=now,
            ended_at=now,
        )
        self.session.add(build)
        self.session.flush()
        candidate = BuildCandidate(
            project_id=project_id,
            build_id=build.id,
            status="succeeded",
            test_gate_status="untested",
            source_playable_version_id=version.id,
            artifact_path=version.artifact_path,
            artifact_checksum=version.artifact_checksum,
            summary=f"Restore candidate from Playable v{version.number}",
        )
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def publish_version(self, version_id: str) -> Release:
        version = self.session.get(PlayableVersion, version_id)
        if version is None:
            raise ValueError("playable version not found")
        existing = self.session.scalar(select(Release).where(Release.playable_version_id == version.id))
        if existing:
            return existing
        project = self._project(version.project_id)
        if project.current_playable_version_id != version.id:
            raise ValueError("only the current playable version can be published")
        latest_number = self.session.scalar(
            select(Release.number)
            .where(Release.project_id == project.id)
            .order_by(Release.number.desc())
        ) or 0
        release = Release(project_id=project.id, playable_version_id=version.id, number=latest_number + 1)
        self.session.add(release)
        self.session.flush()
        return release

    def recover_orphaned_builds(self) -> int:
        builds = list(self.session.scalars(select(Build).where(Build.status.in_(("pending", "running", "cancelling")))))
        recovered = 0
        for build in builds:
            build.status = "orphaned"
            build.failure_code = "backend_restart"
            build.failure_message = "Build interrupted by backend restart"
            build.ended_at = utc_now()
            project = self._project(build.project_id)
            if project.active_build_id == build.id:
                project.active_build_id = None
            recovered += 1
        self.session.flush()
        return recovered

    def start_build(
        self,
        project_id: str,
        revision_id: str | None = None,
        *,
        build_id: str | None = None,
        operation: str = "create",
        request_text: str = "",
    ) -> Build:
        project = self._project(project_id)
        if project.archived_at:
            raise ValueError("archived project cannot start a build")
        if project.active_build_id:
            raise ValueError("active build already exists")
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project.id))
        if design is None or design.status != "confirmed":
            raise ValueError("build requires confirmed Game Design")
        revision = self.session.get(GameSpecRevision, revision_id) if revision_id else self.session.scalar(
            select(GameSpecRevision).where(
                GameSpecRevision.project_id == project_id,
                GameSpecRevision.status == "confirmed",
            ).order_by(GameSpecRevision.revision_number.desc())
        )
        if revision is None or revision.project_id != project_id or revision.status != "confirmed":
            raise ValueError("build requires a confirmed gamespec revision")
        self.validate_gamespec_revision(revision.id)
        build = Build(
            id=build_id or None,
            project_id=project_id,
            gamespec_revision_id=revision.id,
            status="running",
            operation=operation,
            request_text=request_text,
            baseline_playable_version_id=project.current_playable_version_id,
            started_at=utc_now(),
        )
        self.session.add(build)
        self.session.flush()
        project.active_build_id = build.id
        self.session.flush()
        return build

    def finish_build(
        self,
        build_id: str,
        status: str,
        *,
        summary: str,
        artifact_path: str | None = None,
        artifact_checksum: str | None = None,
        failure_code: str | None = None,
        diagnostics_json: str | None = None,
        build_context_id: str | None = None,
    ) -> BuildCandidate:
        if status not in {"succeeded", "failed", "cancelled", "timed_out", "invalid_output", "unsupported", "orphaned"}:
            raise ValueError("invalid terminal build status")
        build = self.session.get(Build, build_id)
        if build is None:
            raise ValueError("build not found")
        existing = self.session.scalar(select(BuildCandidate).where(BuildCandidate.build_id == build.id))
        if existing:
            if build.status != status:
                raise ValueError("build already finished with a different status")
            if build_context_id and existing.build_context_id not in {None, build_context_id}:
                raise ValueError("build candidate already belongs to another context")
            if build_context_id and existing.build_context_id is None:
                existing.build_context_id = build_context_id
            return existing
        if build.status not in {"running", "pending", "cancelling"}:
            raise ValueError("build is not active")
        build.status = status
        build.ended_at = utc_now()
        build.failure_code = failure_code
        build.failure_message = summary if status != "succeeded" else None
        project = self._project(build.project_id)
        if project.active_build_id == build.id:
            project.active_build_id = None
        candidate = BuildCandidate(
            project_id=build.project_id,
            build_id=build.id,
            status=status,
            build_context_id=build_context_id,
            summary=summary,
            artifact_path=artifact_path,
            artifact_checksum=artifact_checksum,
            diagnostics_json=diagnostics_json,
        )
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def cancel_build(self, build_id: str, *, summary: str = "Build cancelled") -> BuildCandidate:
        return self.finish_build(build_id, "cancelled", summary=summary, failure_code="cancelled")

    def retry_build(self, build_id: str) -> Build:
        prior = self.session.get(Build, build_id)
        if prior is None:
            raise ValueError("build not found")
        if prior.status not in {"failed", "cancelled", "orphaned"}:
            raise ValueError("only a terminal failed build can be retried")
        project = self._project(prior.project_id)
        if project.active_build_id:
            raise ValueError("active build already exists")
        attempt = (self.session.scalar(
            select(Build.attempt)
            .where(Build.project_id == project.id)
            .order_by(Build.attempt.desc())
        ) or 0) + 1
        retry = Build(
            project_id=project.id,
            gamespec_revision_id=prior.gamespec_revision_id,
            parent_build_id=prior.id,
            attempt=attempt,
            status="running",
            operation=prior.operation,
            request_text=prior.request_text,
            baseline_playable_version_id=prior.baseline_playable_version_id,
            started_at=utc_now(),
        )
        self.session.add(retry)
        self.session.flush()
        project.active_build_id = retry.id
        self.session.flush()
        return retry

    def _project(self, project_id: str) -> Project:
        project = self.session.get(Project, project_id)
        if project is None:
            raise ValueError("project not found")
        return project

    def _design(self, project_id: str) -> GameDesign:
        design = self.session.scalar(select(GameDesign).where(GameDesign.project_id == project_id))
        if design is None:
            raise ValueError("design not found")
        return design
