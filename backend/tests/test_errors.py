from fastapi import Request
from fastapi.testclient import TestClient

from app.main import create_app


def test_validation_errors_use_safe_envelope() -> None:
    app = create_app()

    @app.post("/__test__/validated")
    def validated(request: Request, required: int) -> dict[str, int]:
        return {"required": required}

    response = TestClient(app).post("/__test__/validated", json={})

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["request_id"]
    assert "traceback" not in response.text.lower()


def test_application_errors_use_safe_envelope() -> None:
    app = create_app()

    @app.get("/__test__/error")
    def error() -> None:
        raise ValueError("internal secret")

    response = TestClient(app, raise_server_exceptions=False).get("/__test__/error")

    assert response.status_code == 500
    body = response.json()["error"]
    assert body["code"] == "internal_error"
    assert body["message"] == "Internal server error"
    assert body["request_id"]
    assert "internal secret" not in response.text
