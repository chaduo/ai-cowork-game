from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.contracts.game_agent import ContractError, RunEvent
from app.main import create_app
from app.repositories.runs import RunRepository
from tests.test_c07_run_events import event


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def seed_terminal_run(database_url: str) -> None:
    app = create_app(Settings(database_url=database_url))
    with Session(app.state.engine) as session:
        repository = RunRepository(session)
        repository.create_run("run-api-1", "build-api-1")
        repository.append_event(event("run-api-1", 1, message="started"))
        repository.finish_run(
            "run-api-1",
            "succeeded",
            event("run-api-1", 2, kind="completed", progress=1, artifact_ref="dist/index.html"),
        )
        session.commit()


def test_create_run_is_idempotent_by_stable_run_id(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    payload = {"run_id": "run-api-1", "build_id": "build-api-1"}

    first = client.post("/api/v1/runs", json=payload)
    second = client.post("/api/v1/runs", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["run_id"] == second.json()["run_id"] == "run-api-1"
    assert second.json()["last_sequence"] == 0


def test_run_status_and_json_events_are_persisted_and_ordered(isolated_database) -> None:
    seed_terminal_run(str(isolated_database.url))
    client = client_for(str(isolated_database.url))

    status = client.get("/api/v1/runs/run-api-1")
    replay = client.get("/api/v1/runs/run-api-1/events", params={"after_sequence": 1})

    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"
    assert status.json()["last_sequence"] == 2
    assert [item["sequence"] for item in replay.json()] == [2]
    assert replay.json()[0]["artifact_ref"] == "dist/index.html"


def test_sse_replay_honors_last_event_id_without_duplicate_events(isolated_database) -> None:
    seed_terminal_run(str(isolated_database.url))
    client = client_for(str(isolated_database.url))

    first = client.get("/api/v1/runs/run-api-1/events/stream")
    reconnect = client.get("/api/v1/runs/run-api-1/events/stream", headers={"Last-Event-ID": "1"})

    assert first.status_code == reconnect.status_code == 200
    assert "event: run_event" in first.text
    assert "id: 1" in first.text and "id: 2" in first.text
    assert "id: 1" not in reconnect.text
    assert "id: 2" in reconnect.text


def test_cancel_endpoint_does_not_fabricate_terminal_success(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    client.post("/api/v1/runs", json={"run_id": "run-api-1", "build_id": "build-api-1"})

    response = client.post("/api/v1/runs/run-api-1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelling"
    assert client.get("/api/v1/runs/run-api-1").json()["status"] == "cancelling"


def test_unknown_run_returns_error_envelope(isolated_database) -> None:
    client = client_for(str(isolated_database.url))

    response = client.get("/api/v1/runs/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "run_not_found"
