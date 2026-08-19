import asyncio
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.workspace import WorkspaceManager
from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.config import Settings
from app.main import create_app
from app.models import BuildCandidate, Run
from app.services.candidate_tests import CandidateTestService
from app.services.project_git import ProjectGitService
from tests.test_c12_candidate_test_gate import confirmed_project, create_candidate


def seeded_app(isolated_database, tmp_path: Path):
    app = create_app(Settings(database_url=str(isolated_database.url)))
    git = ProjectGitService(repo_root=tmp_path / "project-repos")
    app.state.project_git = git
    app.state.workspace_manager = WorkspaceManager(tmp_path / "restore-workspaces")
    with Session(app.state.engine) as session:
        project = confirmed_project(session)
        candidate = create_candidate(session, project, artifact_path="dist/index.html")
        workspace = tmp_path / "workspace"
        (workspace / "dist").mkdir(parents=True)
        artifact = b"<html><body>real candidate</body></html>"
        (workspace / "dist" / "index.html").write_bytes(artifact)
        session.add(Run(
            id=f"run-{candidate.build_id}",
            build_id=candidate.build_id,
            status="succeeded",
            last_sequence=1,
            workspace_path=str(workspace),
            workspace_status="prepared",
        ))
        candidate.artifact_checksum = hashlib.sha256(artifact).hexdigest()
        candidate.artifact_manifest_json = json.dumps([
            {
                "path": "dist/index.html",
                "kind": "preview_entry",
                "sha256": candidate.artifact_checksum,
                "size_bytes": len(artifact),
            }
        ])
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        session.commit()
        return app, project.id, candidate.id, git


def test_review_promote_and_restore_api_are_explicit_and_idempotent(isolated_database, tmp_path: Path) -> None:
    app, project_id, candidate_id, git = seeded_app(isolated_database, tmp_path)
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
    assert promoted.json()["git_commit"] not in {"abc123", "different"}
    assert git.commit_exists(project_id, promoted.json()["git_commit"])
    history = client.get(f"/api/v1/projects/{project_id}/playable-versions")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["is_current"] is True

    restored = client.post(f"/api/v1/projects/{project_id}/playable-versions/{promoted.json()['version_id']}/restore")
    assert restored.status_code == 201
    assert restored.json()["test_gate_status"] == "untested"
    assert restored.json()["source_playable_version_id"] == promoted.json()["version_id"]

    restored_id = restored.json()["candidate_id"]
    with Session(app.state.engine) as session:
        restored_candidate = session.get(BuildCandidate, restored_id)
        restored_run = session.scalar(select(Run).where(Run.build_id == restored_candidate.build_id))
        assert restored_candidate.artifact_path == "dist/index.html"
        assert restored_candidate.artifact_manifest_json is not None
        assert restored_run is not None and restored_run.workspace_path
        assert (Path(restored_run.workspace_path) / "dist" / "index.html").read_bytes() == b"<html><body>real candidate</body></html>"

    tested = client.post(f"/api/v1/candidates/{restored_id}/test")
    assert tested.status_code == 200
    accepted = client.post(
        f"/api/v1/candidates/{restored_id}/human-play-review",
        json={"decision": "accepted", "notes": "Restored version still works"},
    )
    assert accepted.status_code == 200
    restored_version = client.post(
        f"/api/v1/candidates/{restored_id}/promote",
        json={"git_commit": "ignored-client-placeholder"},
    )
    assert restored_version.status_code == 200
    assert restored_version.json()["number"] == 2
    assert restored_version.json()["parent_version_id"] == promoted.json()["version_id"]


def test_promote_api_returns_gate_error_without_human_review(isolated_database, tmp_path: Path) -> None:
    app, _, candidate_id, _ = seeded_app(isolated_database, tmp_path)
    response = TestClient(app).post(
        f"/api/v1/candidates/{candidate_id}/promote",
        json={"git_commit": "abc123"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "candidate_promotion_failed"
