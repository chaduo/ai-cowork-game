from pathlib import Path

from app.config import Settings
from app.db import create_engine_for


def test_sqlite_engine_can_open_configured_database(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'connection.db'}"
    engine = create_engine_for(Settings(database_url=database_url))

    with engine.connect() as connection:
        value = connection.exec_driver_sql("select 1").scalar_one()

    engine.dispose()
    assert value == 1
