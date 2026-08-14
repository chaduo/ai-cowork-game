from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_migrations_are_repeatable_and_create_no_domain_tables(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    assert "alembic_version" in inspect(engine).get_table_names()


def test_c05_migration_creates_design_revision_and_source_columns(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'c05-migration.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    inspector = inspect(create_engine(database_url))
    assert "game_design_revisions" in inspector.get_table_names()
    assert {"current_revision_id", "confirmed_revision_id"} <= {
        column["name"] for column in inspector.get_columns("game_designs")
    }
    assert "source_design_revision_id" in {
        column["name"] for column in inspector.get_columns("game_spec_revisions")
    }


def test_c05_migration_backfills_existing_design_as_revision(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'c05-backfill.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "0006_candidate_test_gate")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO projects (id, name, original_idea, created_at, updated_at) VALUES ('p-c05', 'Garden', 'Idea', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO game_designs (id, project_id, content_json, status, created_at, updated_at) VALUES ('d-c05', 'p-c05', '{\"loop\":\"plant\"}', 'confirmed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))

    command.upgrade(config, "head")

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT id, status, content_json FROM game_design_revisions WHERE project_id = 'p-c05'")).one()
        pointer = connection.execute(text("SELECT current_revision_id, confirmed_revision_id FROM game_designs WHERE id = 'd-c05'")).one()
    assert revision.status == "confirmed"
    assert revision.content_json == '{"loop":"plant"}'
    assert pointer.current_revision_id == revision.id
    assert pointer.confirmed_revision_id == revision.id
