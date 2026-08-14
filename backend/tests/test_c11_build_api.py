from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.fake_game_agent import FakeGameAgent
from app.config import Settings
from app.main import create_app
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def client_and_project(database_url: str):
    app = create_app(Settings(database_url=database_url))
    with Session(app.state.engine) as session:
        lifecycle = ProjectLifecycleService(session)
        project = lifecycle.create_project("Garden", "A quiet garden game")
        lifecycle.submit_design(project.id, draft_payload())
        lifecycle.confirm_design(project.id)
        revision = lifecycle.create_gamespec_revision(project.id, valid_gamespec())
        lifecycle.confirm_gamespec_revision(project.id, revision.id)
        session.commit()
        project_id = project.id
    return TestClient(app), project_id, app


def test_build_api_creates_stable_job_and_query_returns_candidate(isolated_database) -> None:
    client, project_id, _ = client_and_project(str(isolated_database.url))

    first = client.post(
        f"/api/v1/projects/{project_id}/builds",
        json={"build_id": "api-build-1", "run_id": "api-run-1"},
    )
    duplicate = client.post(
        f"/api/v1/projects/{project_id}/builds",
        json={"build_id": "api-build-1", "run_id": "api-run-1"},
    )
    queried = client.get("/api/v1/builds/api-build-1")

    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert first.json()["build_id"] == duplicate.json()["build_id"] == "api-build-1"
    assert first.json()["run_id"] == duplicate.json()["run_id"] == "api-run-1"
    assert queried.json()["status"] == "succeeded"
    assert queried.json()["candidate_id"]
    assert queried.json()["artifact_path"] == "dist/index.html"


def test_build_api_failure_and_retry_keep_failure_diagnostics(isolated_database) -> None:
    client, project_id, app = client_and_project(str(isolated_database.url))
    app.state.game_agent = FakeGameAgent({"modify": "failed"})

    failed = client.post(f"/api/v1/projects/{project_id}/builds", json={"operation": "modify"})
    assert failed.status_code == 201
    assert failed.json()["status"] == "failed"
    assert failed.json()["diagnostics"]

    retried = client.post(f"/api/v1/builds/{failed.json()['build_id']}/retry")
    assert retried.status_code == 201
    assert retried.json()["attempt"] == 2
    assert retried.json()["parent_build_id"] == failed.json()["build_id"]


def test_build_api_rejects_unconfirmed_project(isolated_database) -> None:
    app = create_app(Settings(database_url=str(isolated_database.url)))
    with Session(app.state.engine) as session:
        project = ProjectLifecycleService(session).create_project("Draft", "Not ready")
        session.commit()
        project_id = project.id
    response = TestClient(app).post(f"/api/v1/projects/{project_id}/builds", json={})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "build_start_failed"
