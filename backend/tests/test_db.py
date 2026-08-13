from pathlib import Path

from app.config import Settings
from app.db import create_engine_for
from sqlalchemy import inspect


def test_sqlite_engine_can_open_configured_database(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'connection.db'}"
    engine = create_engine_for(Settings(database_url=database_url))

    with engine.connect() as connection:
        value = connection.exec_driver_sql("select 1").scalar_one()

    engine.dispose()
    assert value == 1


def test_isolated_database_fixture_has_no_shared_tables(isolated_database) -> None:
    assert inspect(isolated_database).get_table_names() == ["alembic_version"]
