from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.test_c05_design_api import draft_payload
from tests.test_c05_gamespec_contract import valid_gamespec


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def create_project(client: TestClient) -> dict:
    return client.post(
        "/api/v1/projects",
        headers={"Idempotency-Key": "c05-gamespec"},
        json={"name": "Garden", "original_idea": "A quiet garden game"},
    ).json()


def confirm_design(client: TestClient, project_id: str) -> None:
    assert client.put(f"/api/v1/projects/{project_id}/design", json=draft_payload()).status_code == 200
    assert client.post(f"/api/v1/projects/{project_id}/design/confirm").status_code == 200


def test_gamespec_revision_is_saved_and_restored(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)
    confirm_design(client, project["id"])

    saved = client.put(f"/api/v1/projects/{project['id']}/gamespec", json=valid_gamespec())

    assert saved.status_code == 200
    assert saved.json()["revision_number"] == 1
    assert saved.json()["status"] == "draft"
    assert saved.json()["spec"] == valid_gamespec()
    assert saved.json()["source_design_revision_id"]

    restored = client_for(str(isolated_database.url)).get(f"/api/v1/projects/{project['id']}/gamespec")
    assert restored.status_code == 200
    assert restored.json()["revision_id"] == saved.json()["revision_id"]
    assert restored.json()["spec"] == valid_gamespec()


def test_gamespec_rejects_missing_relationship_field(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)
    confirm_design(client, project["id"])
    invalid = valid_gamespec()
    del invalid["characters"]["favor_rules"]

    response = client.put(f"/api/v1/projects/{project['id']}/gamespec", json=invalid)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_gamespec_confirm_requires_confirmed_design_and_supersedes_prior_revision(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)

    client.put(f"/api/v1/projects/{project['id']}/gamespec", json=valid_gamespec())
    blocked = client.post(f"/api/v1/projects/{project['id']}/gamespec/confirm")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "design_confirmation_required"

    confirm_design(client, project["id"])
    first = client.post(f"/api/v1/projects/{project['id']}/gamespec/confirm")
    assert first.status_code == 200
    first_id = first.json()["revision_id"]

    changed = valid_gamespec()
    changed["title"] = "Garden v2"
    second_draft = client.put(f"/api/v1/projects/{project['id']}/gamespec", json=changed)
    second = client.post(f"/api/v1/projects/{project['id']}/gamespec/confirm")

    assert second.status_code == 200
    assert second.json()["revision_number"] == 2
    assert second.json()["revision_id"] != first_id
    assert client.get(f"/api/v1/projects/{project['id']}/gamespec").json()["spec"]["title"] == "Garden v2"
    assert second_draft.json()["status"] == "draft"
