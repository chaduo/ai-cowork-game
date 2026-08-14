from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import Connection
from sqlalchemy.engine import Engine


@contextmanager
def transaction_scope(engine: Engine) -> Iterator[Connection]:
    with engine.begin() as connection:
        yield connection
