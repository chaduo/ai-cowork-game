from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app
from app.services.checkpoint import CheckpointService
from app.services.project_git import ProjectGitService
from tests.test_c20_checkpoint import _candidate_with_artifact, _confirmed_project


def _seed_playable(isolated_database, tmp_path: Path, files: dict[str, bytes]):
    git = ProjectGitService(repo_root=tmp_path / "project-repos")
    with Session(isolated_database) as session:
        project_id, _, _ = _confirmed_project(session)
        candidate = _candidate_with_artifact(
            session,
            project_id,
            tmp_path / "workspaces" / project_id,
            files["index.html"],
            extra_files={path: content for path, content in files.items() if path != "index.html"},
        )
        version = CheckpointService(session, git=git).promote(
            candidate.id,
            test_report_id="report",
            verdict="pass",
        )
        session.commit()
        return project_id, version.id, version.git_commit, git


def _client(isolated_database, git: ProjectGitService) -> TestClient:
    app = create_app(Settings(database_url=str(isolated_database.url)))
    app.state.project_git = git
    return TestClient(app)


def test_lists_real_assets_from_immutable_playable_commit(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, commit, git = _seed_playable(isolated_database, tmp_path, {
        "index.html": b"<html></html>",
        "assets/hero.png": b"\x89PNG image",
        "assets/icon.svg": b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
        "audio/theme.ogg": b"OggS audio",
        "fonts/game.woff2": b"wOF2 font",
        "main.js": b"console.log('game')",
    })

    response = _client(isolated_database, git).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets"
    )

    assert response.status_code == 200
    assert response.json()["version_id"] == version_id
    assert response.json()["git_commit"] == commit
    assert [(item["path"], item["kind"], item["mime_type"]) for item in response.json()["assets"]] == [
        ("assets/hero.png", "image", "image/png"),
        ("assets/icon.svg", "image", "image/svg+xml"),
        ("audio/theme.ogg", "audio", "audio/ogg"),
        ("fonts/game.woff2", "font", "font/woff2"),
    ]
    assert response.json()["assets"][0]["content_url"].endswith(
        f"/assets/content?path={quote('assets/hero.png', safe='')}"
    )


def test_serves_image_bytes_with_immutable_headers(isolated_database, tmp_path: Path) -> None:
    png = b"\x89PNG image bytes"
    project_id, version_id, commit, git = _seed_playable(isolated_database, tmp_path, {
        "index.html": b"<html></html>",
        "assets/hero.png": png,
    })

    response = _client(isolated_database, git).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content",
        params={"path": "assets/hero.png"},
    )

    assert response.status_code == 200
    assert response.content == png
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert commit in response.headers["etag"]


def test_svg_content_has_restrictive_policy(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, _, git = _seed_playable(isolated_database, tmp_path, {
        "index.html": b"<html></html>",
        "icon.svg": b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
    })

    response = _client(isolated_database, git).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content",
        params={"path": "icon.svg"},
    )

    assert response.status_code == 200
    assert response.headers["content-security-policy"] == "default-src 'none'; style-src 'unsafe-inline'; sandbox"


def test_html_only_playable_has_honest_empty_inventory(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, _, git = _seed_playable(isolated_database, tmp_path, {
        "index.html": b"<html><canvas></canvas></html>",
    })

    response = _client(isolated_database, git).get(
        f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets"
    )

    assert response.status_code == 200
    assert response.json()["assets"] == []


def test_asset_content_rejects_unsafe_or_non_asset_paths(isolated_database, tmp_path: Path) -> None:
    project_id, version_id, _, git = _seed_playable(isolated_database, tmp_path, {
        "index.html": b"<html></html>",
        "assets/hero.png": b"png",
        "main.js": b"javascript",
    })
    client = _client(isolated_database, git)

    for path in ("../assets/hero.png", "/assets/hero.png", "main.js", "https://example.test/a.png"):
        response = client.get(
            f"/api/v1/projects/{project_id}/playable-versions/{version_id}/assets/content",
            params={"path": path},
        )
        assert response.status_code in {400, 404}
        assert response.json()["error"]["code"] == "playable_asset_not_found"


def test_asset_routes_enforce_project_version_ownership(isolated_database, tmp_path: Path) -> None:
    first_project, first_version, _, first_git = _seed_playable(isolated_database, tmp_path / "first", {
        "index.html": b"<html></html>",
        "secret.png": b"first project image",
    })
    second_project, _, _, _ = _seed_playable(isolated_database, tmp_path / "second", {
        "index.html": b"<html></html>",
    })

    response = _client(isolated_database, first_git).get(
        f"/api/v1/projects/{second_project}/playable-versions/{first_version}/assets"
    )

    assert first_project != second_project
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "playable_version_not_found"
