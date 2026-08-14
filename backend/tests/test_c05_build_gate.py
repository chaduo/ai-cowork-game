import pytest
from sqlalchemy.orm import Session

from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def confirmed_design_service(session: Session):
    service = ProjectLifecycleService(session)
    project = service.create_project("Garden", "A quiet garden game")
    service.submit_design(project.id, draft_payload())
    service.confirm_design(project.id)
    return service, project


def test_build_requires_confirmed_game_design(isolated_database) -> None:
    with Session(isolated_database) as session:
        service = ProjectLifecycleService(session)
        project = service.create_project("Garden", "A quiet garden game")
        revision = service.create_gamespec_revision(project.id, valid_gamespec())

        with pytest.raises(ValueError, match="confirmed Game Design"):
            service.confirm_gamespec_revision(project.id, revision.id)

        with pytest.raises(ValueError, match="confirmed Game Design"):
            service.start_build(project.id)


def test_build_rejects_invalid_confirmed_gamespec(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_design_service(session)
        invalid = valid_gamespec()
        del invalid["characters"]["relationship_growth"]
        revision = service.create_gamespec_revision(project.id, invalid)
        service.confirm_gamespec_revision(project.id, revision.id)

        with pytest.raises(ValueError, match="schema"):
            service.start_build(project.id)


def test_confirmed_design_and_gamespec_produce_runtime_build_spec_without_workflow_state(isolated_database) -> None:
    with Session(isolated_database) as session:
        service, project = confirmed_design_service(session)
        revision = service.create_gamespec_revision(project.id, valid_gamespec())
        service.confirm_gamespec_revision(project.id, revision.id)

        runtime = service.runtime_build_spec(project.id)
        build = service.start_build(project.id)

        assert runtime.project_title == "多代田园物语"
        assert runtime.characters.relationship_growth
        assert not hasattr(runtime, "recommended")
        assert build.project_id == project.id
