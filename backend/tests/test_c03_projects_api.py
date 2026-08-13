from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def test_create_project_persists_idea_and_returns_stable_id(isolated_database, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", str(isolated_database.url))
    client = client_for(str(isolated_database.url))

    response = client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "idea-1"},
        json={"name": "Garden", "original_idea": "A quiet garden game"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["original_idea"] == "A quiet garden game"
    assert body["stage"] == "design_draft"
    assert client.get(f"/api/v1/projects/{body['id']}").json() == body


def test_same_idempotency_key_returns_same_project_without_duplicate(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    payload = {"name": "Garden", "original_idea": "A quiet garden game"}

    first = client.post("/api/v1/projects", headers={"Idempotency-Key": "repeat-1"}, json=payload)
    second = client.post("/api/v1/projects", headers={"Idempotency-Key": "repeat-1"}, json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_blank_idea_is_rejected(isolated_database) -> None:
    client = client_for(str(isolated_database.url))

    response = client.post("/api/v1/projects", json={"name": "Garden", "original_idea": "   "})

    assert response.status_code == 422


def test_project_list_survives_a_new_client(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    created = client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "list-1"},
        json={"name": "Garden", "original_idea": "A quiet garden game"},
    ).json()

    listed = client.get("/api/v1/projects")

    assert listed.status_code == 200
    assert listed.json()[0]["id"] == created["id"]
    assert listed.json()[0]["original_idea"] == "A quiet garden game"
