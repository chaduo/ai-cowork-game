from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

from app.config import Settings
from app.db import create_engine_for


@pytest.fixture
def isolated_database(tmp_path: Path) -> Engine:
    database_url = f"sqlite:///{tmp_path / 'isolated.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    engine = create_engine_for(Settings(database_url=database_url))
    yield engine
    engine.dispose()
