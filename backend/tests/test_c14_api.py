import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.config import Settings
from app.main import create_app
from app.models import BuildCandidate
from app.services.candidate_tests import CandidateTestService
from tests.test_c12_candidate_test_gate import confirmed_project, create_candidate


def seeded_app(isolated_database):
    app = create_app(Settings(database_url=str(isolated_database.url)))
    with Session(app.state.engine) as session:
        project = confirmed_project(session)
        candidate = create_candidate(session, project, artifact_path="dist/index.html")
        candidate.artifact_checksum = "c" * 64
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        session.commit()
        return app, project.id, candidate.id


def test_review_promote_and_restore_api_are_explicit_and_idempotent(isolated_database) -> None:
    app, project_id, candidate_id = seeded_app(isolated_database)
    client = TestClient(app)

    review = client.post(
        f"/api/v1/candidates/{candidate_id}/human-play-review",
        json={"decision": "accepted", "notes": "Looks good"},
    )
    assert review.status_code == 200
    assert review.json()["decision"] == "accepted"
    assert client.get(f"/api/v1/candidates/{candidate_id}/human-play-review").json()["candidate_id"] == candidate_id

    promoted = client.post(
        f"/api/v1/candidates/{candidate_id}/promote",
        json={"git_commit": "abc123"},
    )
    repeated = client.post(
        f"/api/v1/candidates/{candidate_id}/promote",
        json={"git_commit": "different"},
    )
    assert promoted.status_code == repeated.status_code == 200
    assert promoted.json()["version_id"] == repeated.json()["version_id"]
    history = client.get(f"/api/v1/projects/{project_id}/playable-versions")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["is_current"] is True

    restored = client.post(f"/api/v1/projects/{project_id}/playable-versions/{promoted.json()['version_id']}/restore")
    assert restored.status_code == 201
    assert restored.json()["test_gate_status"] == "untested"
    assert restored.json()["source_playable_version_id"] == promoted.json()["version_id"]


def test_promote_api_returns_gate_error_without_human_review(isolated_database) -> None:
    app, _, candidate_id = seeded_app(isolated_database)
    response = TestClient(app).post(
        f"/api/v1/candidates/{candidate_id}/promote",
        json={"git_commit": "abc123"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "candidate_promotion_failed"
