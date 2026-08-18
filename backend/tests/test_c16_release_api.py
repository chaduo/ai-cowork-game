import asyncio
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.agents.fake_candidate_test_runner import FakeCandidateTestRunner
from app.config import Settings
from app.main import create_app
from app.models import PlayableVersion, Project
from app.services.candidate_tests import CandidateTestService
from app.services.lifecycle import ProjectLifecycleService
from app.services.project_git import ProjectGitService
from tests.test_c02_build_service import confirmed_service


def _app_for(isolated_database, *, git: ProjectGitService | None = None):
    app = create_app(Settings(database_url=str(isolated_database.url)))
    if git is not None:
        app.state.project_git = git
    return app


def _project_without_playable(client: TestClient) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "c16-empty"},
        json={"name": "Empty Garden", "original_idea": "No playable yet"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _prepared_project(isolated_database, tmp_path: Path):
    git = ProjectGitService(repo_root=tmp_path / "project-repos")
    with Session(isolated_database) as session:
        lifecycle, project = confirmed_service(session)
        build = lifecycle.start_build(project.id)
        candidate = lifecycle.finish_build(
            build.id,
            "succeeded",
            summary="candidate ready",
            artifact_path="playable/index.html",
        )
        artifact = b"<html><body>C16 release</body></html>"
        candidate.artifact_checksum = hashlib.sha256(artifact).hexdigest()
        asyncio.run(CandidateTestService(session, FakeCandidateTestRunner("pass")).test_candidate(candidate.id))
        lifecycle.record_human_play_review(candidate.id, decision="accepted", notes="ready")

        git.init_project(project.id)
        commit = git.commit(
            project.id,
            message="promote c16 fixture",
            files={"playable/index.html": artifact},
        )
        version = lifecycle.promote_candidate(
            candidate.id,
            git_commit=commit,
            artifact_checksum=candidate.artifact_checksum,
        )
        session.commit()
        return project.id, version.id, git


def test_publish_review_is_not_eligible_without_current_playable(isolated_database) -> None:
    app = _app_for(isolated_database)
    client = TestClient(app)
    project_id = _project_without_playable(client)

    response = client.get(f"/api/v1/projects/{project_id}/publish-review")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": project_id,
        "eligible": False,
        "reason": "no_current_playable",
        "next_release_number": 1,
        "playable_version_id": None,
        "playable_number": None,
        "game_design_revision_id": None,
        "gamespec_revision_id": None,
        "game_design_revision_number": None,
        "gamespec_revision_number": None,
        "artifact_path": None,
        "artifact_checksum": None,
        "git_commit": None,
        "existing_release": None,
    }


def test_publish_creates_immutable_release_and_empty_extraction_batch(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, git = _prepared_project(isolated_database, tmp_path)
    app = _app_for(isolated_database, git=git)
    client = TestClient(app)

    review = client.get(f"/api/v1/projects/{project_id}/publish-review")
    assert review.status_code == 200
    assert review.json()["eligible"] is True
    assert review.json()["playable_version_id"] == version_id
    assert review.json()["next_release_number"] == 1

    published = client.post(
        f"/api/v1/projects/{project_id}/releases",
        json={
            "playable_version_id": version_id,
            "name": "C16 首个正式版本",
            "description": "冻结后的第一版可试玩版本。",
        },
    )
    assert published.status_code == 201
    body = published.json()
    assert body["number"] == 1
    assert body["name"] == "C16 首个正式版本"
    assert body["description"] == "冻结后的第一版可试玩版本。"
    assert body["playable_version_id"] == version_id
    assert body["game_design_revision_id"]
    assert body["gamespec_revision_id"]
    assert body["artifact_path"] == "playable/index.html"
    assert body["git_commit"]
    assert body["resource_batch"] == {"status": "empty", "candidate_count": 0}

    repeated = client.post(
        f"/api/v1/projects/{project_id}/releases",
        json={
            "playable_version_id": version_id,
            "name": "不要覆盖旧名称",
            "description": "不要覆盖旧说明",
        },
    )
    assert repeated.status_code == 200
    assert repeated.json()["id"] == body["id"]
    assert repeated.json()["name"] == "C16 首个正式版本"
    assert repeated.json()["description"] == "冻结后的第一版可试玩版本。"

    restored = TestClient(_app_for(isolated_database, git=git)).get(
        f"/api/v1/projects/{project_id}/releases/{body['id']}"
    )
    assert restored.status_code == 200
    assert restored.json()["id"] == body["id"]
    assert restored.json()["resource_batch"]["candidate_count"] == 0


def test_publish_rejects_missing_provenance_without_touching_playable(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, git = _prepared_project(isolated_database, tmp_path)
    with Session(isolated_database) as session:
        version = session.get(PlayableVersion, version_id)
        assert version is not None
        version.git_commit = ""
        session.commit()

    client = TestClient(_app_for(isolated_database, git=git))
    response = client.post(
        f"/api/v1/projects/{project_id}/releases",
        json={"playable_version_id": version_id, "name": "坏发布", "description": "不应创建"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "release_publish_failed"
    with Session(isolated_database) as session:
        assert session.get(Project, project_id).current_playable_version_id == version_id


def test_publish_rejects_non_current_playable(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, git = _prepared_project(isolated_database, tmp_path)
    with Session(isolated_database) as session:
        project = session.get(Project, project_id)
        assert project is not None
        replacement = PlayableVersion(
            project_id=project_id,
            candidate_id="replacement-candidate",
            number=2,
            test_report_id="replacement-report",
            git_commit="replacement-commit",
            artifact_path="playable/index.html",
            artifact_checksum="b" * 64,
        )
        session.add(replacement)
        session.flush()
        project.current_playable_version_id = replacement.id
        session.commit()

    response = TestClient(_app_for(isolated_database, git=git)).post(
        f"/api/v1/projects/{project_id}/releases",
        json={"playable_version_id": version_id, "name": "旧版本", "description": "不应发布"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "release_publish_failed"
