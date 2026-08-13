import json

from sqlalchemy.orm import Session

from app.models import GameSpecRevision, Project
from app.services.lifecycle import ProjectLifecycleService


def test_project_design_and_gamespec_confirmation_derive_stages(isolated_database) -> None:
    with Session(isolated_database) as session:
        service = ProjectLifecycleService(session)
        project = service.create_project("Garden", "A quiet garden game")
        assert service.derive_project_stage(project.id).value == "design_draft"

        service.submit_design(project.id, {"loop": "plant"})
        assert service.derive_project_stage(project.id).value == "design_review"
        service.confirm_design(project.id)

        revision = service.create_gamespec_revision(project.id, {"genre": "sim"})
        assert revision.revision_number == 1
        assert service.derive_project_stage(project.id).value == "gamespec_review"
        service.confirm_gamespec_revision(project.id, revision.id)
        assert service.derive_project_stage(project.id).value == "ready_to_build"


def test_confirmed_gamespec_revision_is_immutable_and_superseded_by_next_confirmation(isolated_database) -> None:
    with Session(isolated_database) as session:
        service = ProjectLifecycleService(session)
        project = service.create_project("Garden", "A quiet garden game")
        service.submit_design(project.id, {"loop": "plant"})
        service.confirm_design(project.id)
        first = service.create_gamespec_revision(project.id, {"genre": "sim"})
        service.confirm_gamespec_revision(project.id, first.id)
        second = service.create_gamespec_revision(project.id, {"genre": "rpg"})
        service.confirm_gamespec_revision(project.id, second.id)

        session.expire_all()
        stored_first = session.get(GameSpecRevision, first.id)
        stored_second = session.get(GameSpecRevision, second.id)
        assert json.loads(stored_first.content_json)["genre"] == "sim"
        assert stored_first.status == "superseded"
        assert stored_second.status == "confirmed"
