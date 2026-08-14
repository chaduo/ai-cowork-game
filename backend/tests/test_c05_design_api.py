from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def create_project(client: TestClient) -> dict:
    return client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "c05-design"},
        json={"name": "Garden", "original_idea": "A quiet garden game"},
    ).json()


def draft_payload() -> dict:
    return {
        "schema_version": 1,
        "original_idea": "A quiet garden game",
        "project_title": "Garden",
        "scenario_id": "generic",
        "summary": {
            "title": "Garden",
            "summary": "A quiet garden game.",
            "highlights": ["种植", "探索"],
            "core_loop": ["种植", "收获"],
            "progression": [],
        },
        "decisions": [],
        "clarification": {
            "question_index": 1,
            "status": "clarifying",
            "custom_input": "",
        },
    }


def test_design_draft_can_be_saved_and_restored_after_refresh(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)

    initial = client.get(f"/api/v1/projects/{project['id']}/design")
    assert initial.status_code == 200
    assert initial.json()["status"] == "draft"
    assert initial.json()["draft"]["original_idea"] == "A quiet garden game"

    saved = client.put(f"/api/v1/projects/{project['id']}/design", json=draft_payload())
    assert saved.status_code == 200
    assert saved.json()["status"] == "submitted"

    restored = client_for(str(isolated_database.url)).get(f"/api/v1/projects/{project['id']}/design")
    assert restored.status_code == 200
    assert restored.json()["draft"] == draft_payload()
    assert restored.json()["status"] == "submitted"


def test_design_confirmation_is_independent_and_persistent(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)

    blocked = client.post(f"/api/v1/projects/{project['id']}/design/confirm")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "design_confirmation_required"

    client.put(f"/api/v1/projects/{project['id']}/design", json=draft_payload())
    confirmed = client.post(f"/api/v1/projects/{project['id']}/design/confirm")

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["confirmed_at"]

    restored = client_for(str(isolated_database.url)).get(f"/api/v1/projects/{project['id']}/design")
    assert restored.json()["status"] == "confirmed"


def test_design_api_returns_project_not_found(isolated_database) -> None:
    client = client_for(str(isolated_database.url))

    response = client.get("/api/v1/projects/missing/design")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
