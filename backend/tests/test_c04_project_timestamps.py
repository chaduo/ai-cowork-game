from app.main import create_app
from app.config import Settings
from fastapi.testclient import TestClient


def test_project_response_exposes_creation_timestamp(isolated_database) -> None:
    client = TestClient(create_app(Settings(database_url=str(isolated_database.url))))

    created = client.post(
        "/api/v1/projects",
        json={"name": "竞技场守卫", "original_idea": "守住竞技场"},
    )

    assert created.status_code == 201
    body = created.json()
    assert body["created_at"]
    assert body["updated_at"]

    listed = client.get("/api/v1/projects").json()
    assert listed[0]["created_at"] == body["created_at"]
