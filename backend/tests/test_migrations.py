from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migrations_are_repeatable_and_create_no_domain_tables(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    assert inspect(engine).get_table_names() == ["alembic_version"]
