from datetime import timedelta

from app.main import create_app
from app.config import Settings
from app.models import GameDesign, Project, utc_now
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


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


def test_project_list_sorts_by_derived_latest_activity(isolated_database) -> None:
    client = TestClient(create_app(Settings(database_url=str(isolated_database.url))))
    older = client.post("/api/v1/projects", json={"name": "旧项目", "original_idea": "旧想法"}).json()
    recently_designed = client.post("/api/v1/projects", json={"name": "刚更新", "original_idea": "新想法"}).json()

    now = utc_now()
    with Session(isolated_database) as session:
        older_project = session.get(Project, older["id"])
        recently_designed_project = session.get(Project, recently_designed["id"])
        assert older_project is not None
        assert recently_designed_project is not None
        older_project.updated_at = now - timedelta(days=2)
        recently_designed_project.updated_at = now - timedelta(days=3)
        session.add(GameDesign(
            project_id=recently_designed["id"],
            content_json='{}',
            status="submitted",
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    listed = client.get("/api/v1/projects").json()
    assert [project["id"] for project in listed] == [recently_designed["id"], older["id"]]
