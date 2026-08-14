import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.config import Settings
from app.main import create_app
from app.services.candidate_tests import CandidateTestService
from tests.test_c12_candidate_test_gate import confirmed_project, create_candidate


def seeded_app(isolated_database):
    app = create_app(Settings(database_url=str(isolated_database.url)))
    with Session(app.state.engine) as session:
        project = confirmed_project(session)
        candidate = create_candidate(session, project)
        session.commit()
        return app, project.id, candidate.id


def test_candidate_test_api_persists_report_and_retrieval_is_idempotent(isolated_database) -> None:
    app, project_id, candidate_id = seeded_app(isolated_database)
    app.state.candidate_test_runner = FakeCandidateTestRunner("pass")
    client = TestClient(app)

    tested = client.post(f"/api/v1/candidates/{candidate_id}/test")
    repeated = client.post(f"/api/v1/candidates/{candidate_id}/test")
    fetched = client.get(f"/api/v1/candidates/{candidate_id}/test-report")

    assert tested.status_code == repeated.status_code == 200
    assert tested.json()["candidate_id"] == candidate_id
    assert tested.json()["test_gate_status"] == "ready"
    assert tested.json()["report"]["platform_verdict"] == "pass"
    assert len(tested.json()["report"]["evidence"]) == 5
    assert repeated.json()["report"]["id"] == tested.json()["report"]["id"]
    assert fetched.json()["report"]["id"] == tested.json()["report"]["id"]


def test_candidate_test_api_exposes_invalid_gate_without_promoting(isolated_database) -> None:
    app, _, candidate_id = seeded_app(isolated_database)
    app.state.candidate_test_runner = FakeCandidateTestRunner("runtime_only_pass")
    response = TestClient(app).post(f"/api/v1/candidates/{candidate_id}/test")

    assert response.status_code == 200
    assert response.json()["test_gate_status"] == "invalid"
    assert response.json()["report"]["platform_verdict"] == "invalid"


def test_candidate_repair_link_api_preserves_parent_and_attempt(isolated_database) -> None:
    app = create_app(Settings(database_url=str(isolated_database.url)))
    with Session(app.state.engine) as session:
        project = confirmed_project(session)
        parent = create_candidate(session, project)
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("console_failure")).test_candidate(parent.id))
        replacement = create_candidate(session, project)
        session.commit()
        parent_id, replacement_id = parent.id, replacement.id
    client = TestClient(app)

    response = client.post(
        f"/api/v1/candidates/{parent_id}/repair-link",
        json={"replacement_candidate_id": replacement_id},
    )

    assert response.status_code == 200
    assert response.json()["parent_candidate_id"] == parent_id
    assert response.json()["attempt"] == 2


def test_unknown_candidate_returns_error_envelope(isolated_database) -> None:
    app = create_app(Settings(database_url=str(isolated_database.url)))
    response = TestClient(app).get("/api/v1/candidates/missing/test-report")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "candidate_not_found"
