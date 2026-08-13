from pathlib import Path

import pytest
from sqlalchemy import text

from app.config import Settings
from app.db import create_engine_for
from app.repositories.transaction import transaction_scope


def _engine(tmp_path: Path):
    return create_engine_for(Settings(database_url=f"sqlite:///{tmp_path / 'transactions.db'}"))


def test_successful_transaction_commits(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    with engine.begin() as connection:
        connection.execute(text("create table notes (value text not null)"))

    with transaction_scope(engine) as connection:
        connection.execute(text("insert into notes (value) values ('saved')"))

    with engine.connect() as connection:
        assert connection.execute(text("select value from notes")).scalar_one() == "saved"


def test_failed_transaction_rolls_back(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    with engine.begin() as connection:
        connection.execute(text("create table notes (value text not null)"))

    with pytest.raises(RuntimeError):
        with transaction_scope(engine) as connection:
            connection.execute(text("insert into notes (value) values ('discarded')"))
            raise RuntimeError("stop")

    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from notes")).scalar_one() == 0
