import asyncio

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.lifecycle import ProjectLifecycleService
from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.services.candidate_tests import CandidateTestService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def test_projects_list_is_empty_without_fixture_projects(isolated_database) -> None:
    client = client_for(str(isolated_database.url))

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_projects_list_returns_derived_lifecycle_summary_for_each_project(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    first = client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "c04-first"},
        json={"name": "Garden", "original_idea": "A quiet garden game"},
    ).json()
    second = client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "c04-second"},
        json={"name": "Arena", "original_idea": "A small arena game"},
    ).json()

    with Session(isolated_database) as session:
        service = ProjectLifecycleService(session)
        service.submit_design(first["id"], draft_payload())
        service.confirm_design(first["id"])
        revision = service.create_gamespec_revision(first["id"], valid_gamespec())
        service.confirm_gamespec_revision(first["id"], revision.id)
        build = service.start_build(first["id"])
        candidate = service.finish_build(build.id, "succeeded", summary="ready", artifact_path="dist/index.html")
        candidate.artifact_checksum = "a" * 64
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        service.record_human_play_review(candidate.id, decision="accepted")
        playable = service.promote_candidate(
            candidate.id,
            git_commit="abc123",
        )
        release = service.publish_version(playable.id)
        playable_id = playable.id
        release_id = release.id
        session.commit()

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    projects = response.json()
    assert [project["id"] for project in projects] == [first["id"], second["id"]]
    published = projects[0]
    assert published["stage"] == "published"
    assert published["current_playable"] == {
        "id": playable_id,
        "number": 1,
        "artifact_path": "dist/index.html",
    }
    assert published["latest_release"] == {
        "id": release_id,
        "number": 1,
        "status": "published",
        "playable_version_id": playable_id,
    }
    assert published["updated_at"]
    assert projects[1]["stage"] == "design_draft"
    assert projects[1]["current_playable"] is None
    assert projects[1]["latest_release"] is None


def test_project_detail_returns_not_found_envelope_for_unknown_project(isolated_database) -> None:
    client = client_for(str(isolated_database.url))

    response = client.get("/api/v1/projects/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
