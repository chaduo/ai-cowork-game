from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_ok_payload() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-cowork-game-api",
        "version": "0.1.0",
    }
