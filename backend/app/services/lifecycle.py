from enum import StrEnum
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GameDesign, GameSpecRevision, Project, utc_now


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
        if design is None:
            design = GameDesign(project_id=project.id, content_json=json.dumps(content), status="submitted")
            self.session.add(design)
        else:
            design.content_json = json.dumps(content)
            design.status = "submitted"
        self.session.flush()
        return design

    def confirm_design(self, project_id: str) -> GameDesign:
        design = self._design(project_id)
        if design.status != "submitted":
            raise ValueError("design must be submitted before confirmation")
        design.status = "confirmed"
        design.confirmed_at = utc_now()
        self.session.flush()
        return design

    def create_gamespec_revision(self, project_id: str, content: dict) -> GameSpecRevision:
        self._project(project_id)
        latest = self.session.scalar(
            select(GameSpecRevision)
            .where(GameSpecRevision.project_id == project_id)
            .order_by(GameSpecRevision.revision_number.desc())
        )
        revision = GameSpecRevision(
            project_id=project_id,
            revision_number=(latest.revision_number + 1 if latest else 1),
            content_json=json.dumps(content),
            status="draft",
        )
        self.session.add(revision)
        self.session.flush()
        return revision

    def confirm_gamespec_revision(self, project_id: str, revision_id: str) -> GameSpecRevision:
        revision = self.session.get(GameSpecRevision, revision_id)
        if revision is None or revision.project_id != project_id:
            raise ValueError("gamespec revision not found")
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

    def derive_project_stage(self, project_id: str) -> ProjectStage:
        project = self._project(project_id)
        if project.archived_at:
            return ProjectStage.ARCHIVED
        if project.active_build_id:
            return ProjectStage.BUILDING
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
