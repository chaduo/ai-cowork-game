import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.config import Settings
from app.main import create_app
from app.models import Build, BuildCandidate, PlayableVersion, Run
from app.services.candidate_tests import CandidateTestService
from app.services.lifecycle import ProjectLifecycleService
from tests.test_c05_gamespec_contract import valid_gamespec
from tests.test_c05_design_api import draft_payload


def _promoted_app(isolated_database, tmp_path: Path):
    app = create_app(Settings(database_url=str(isolated_database.url)))
    with Session(app.state.engine) as session:
        lifecycle = ProjectLifecycleService(session)
        project = lifecycle.create_project("Preview", "A real playable preview")
        lifecycle.submit_design(project.id, draft_payload())
        lifecycle.confirm_design(project.id)
        revision = lifecycle.create_gamespec_revision(project.id, valid_gamespec())
        lifecycle.confirm_gamespec_revision(project.id, revision.id)
        workspace = tmp_path / "run-workspace"
        workspace.mkdir()
        (workspace / "index.html").write_text(
            "<!doctype html><script>window.__GAME_TEST__={version:1,ready:true}</script>",
            encoding="utf-8",
        )
        build = Build(
            project_id=project.id,
            gamespec_revision_id=revision.id,
            status="succeeded",
            operation="create",
        )
        session.add(build)
        session.flush()
        run = Run(
            id="preview-run",
            build_id=build.id,
            status="succeeded",
            workspace_path=str(workspace),
            workspace_status="prepared",
        )
        session.add(run)
        candidate = BuildCandidate(
            project_id=project.id,
            build_id=build.id,
            status="succeeded",
            test_gate_status="untested",
            artifact_path="index.html",
            artifact_checksum="a" * 64,
            summary="preview candidate",
        )
        session.add(candidate)
        session.flush()
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        lifecycle.record_human_play_review(candidate.id, decision="accepted", notes="Looks good")
        version = lifecycle.promote_candidate(candidate.id, git_commit="preview-commit")
        session.commit()
        return app, project.id, version.id


def test_preview_returns_promoted_html_artifact(isolated_database, tmp_path: Path) -> None:
    app, project_id, version_id = _promoted_app(isolated_database, tmp_path)

    response = TestClient(app).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/preview"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "window.__GAME_TEST__" in response.text


def test_preview_rejects_missing_artifact(isolated_database, tmp_path: Path) -> None:
    app, project_id, version_id = _promoted_app(isolated_database, tmp_path)
    (tmp_path / "run-workspace" / "index.html").unlink()

    response = TestClient(app).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/preview"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "preview_not_found"
    assert str(tmp_path) not in response.text


def test_preview_rejects_version_from_another_project(isolated_database, tmp_path: Path) -> None:
    app, project_id, version_id = _promoted_app(isolated_database, tmp_path)
    with Session(app.state.engine) as session:
        other = ProjectLifecycleService(session).create_project("Other", "Other project")
        session.commit()
        other_id = other.id

    response = TestClient(app).get(
        f"/api/v1/projects/{other_id}/playable-versions/{version_id}/preview"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "playable_version_not_found"
    assert project_id not in response.text


def test_preview_rejects_workspace_escape(isolated_database, tmp_path: Path) -> None:
    app, project_id, version_id = _promoted_app(isolated_database, tmp_path)
    with Session(app.state.engine) as session:
        version = session.get(PlayableVersion, version_id)
        version.artifact_path = "../outside.html"
        session.commit()

    response = TestClient(app).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/preview"
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "preview_path_rejected"
    assert str(tmp_path) not in response.text
