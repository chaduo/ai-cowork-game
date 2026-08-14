from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_healthz_returns_ok_payload(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    client = TestClient(create_app(Settings(database_url=database_url)))

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-cowork-game-api",
        "version": "0.1.0",
    }


def test_healthz_reports_database_unavailable(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'missing-parent' / 'app.db'}"
    client = TestClient(create_app(Settings(database_url=database_url)), raise_server_exceptions=False)

    response = client.get("/healthz")

    assert response.status_code == 503
    body = response.json()["error"]
    assert body["code"] == "dependency_unavailable"
    assert body["request_id"]
