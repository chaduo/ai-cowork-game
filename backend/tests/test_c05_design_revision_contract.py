from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

from tests.test_c05_design_api import create_project, draft_payload


def client_for(database_url: str) -> TestClient:
    return TestClient(create_app(Settings(database_url=database_url)))


def test_design_save_returns_revision_and_readiness_metadata(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)

    response = client.put(f"/api/v1/projects/{project['id']}/design", json=draft_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["revision_id"]
    assert body["revision_number"] == 1
    assert body["readiness"]["status"] == "ready"


def test_design_confirmation_is_blocked_until_readiness_is_ready(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)
    payload = draft_payload()
    payload["readiness"] = {
        "status": "blocked",
        "blockers": ["还没有决定核心循环"],
        "unresolved_decisions": ["core-loop"],
        "checked_at": None,
    }

    saved = client.put(f"/api/v1/projects/{project['id']}/design", json=payload)
    blocked = client.post(f"/api/v1/projects/{project['id']}/design/confirm")

    assert saved.status_code == 200
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "design_not_ready"
    assert client.get(f"/api/v1/projects/{project['id']}/design").json()["confirmed_revision_id"] is None


def test_edit_after_confirm_creates_new_revision_and_preserves_confirmed_pointer(isolated_database) -> None:
    client = client_for(str(isolated_database.url))
    project = create_project(client)
    first_draft = client.put(f"/api/v1/projects/{project['id']}/design", json=draft_payload()).json()
    first_confirmed = client.post(f"/api/v1/projects/{project['id']}/design/confirm").json()
    changed = draft_payload()
    changed["project_title"] = "Garden v2"

    second = client.put(f"/api/v1/projects/{project['id']}/design", json=changed)

    assert second.status_code == 200
    body = second.json()
    assert body["revision_id"] != first_draft["revision_id"]
    assert body["revision_number"] == 2
    assert body["confirmed_revision_id"] == first_confirmed["revision_id"]
    assert body["draft"]["project_title"] == "Garden v2"


def test_gamespec_revision_records_confirmed_gdd_source(isolated_database) -> None:
    from tests.test_c05_gamespec_api import confirm_design
    from tests.test_c05_gamespec_contract import valid_gamespec

    client = client_for(str(isolated_database.url))
    project = create_project(client)
    confirm_design(client, project["id"])
    design = client.get(f"/api/v1/projects/{project['id']}/design").json()

    saved = client.put(f"/api/v1/projects/{project['id']}/gamespec", json=valid_gamespec())

    assert saved.status_code == 200
    assert saved.json()["source_design_revision_id"] == design["revision_id"]
