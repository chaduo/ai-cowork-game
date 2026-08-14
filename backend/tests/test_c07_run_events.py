from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Run, RunEventRecord


def test_c07_migration_creates_runs_and_run_events_tables(isolated_database) -> None:
    tables = set(inspect(isolated_database).get_table_names())

    assert {"runs", "run_events"}.issubset(tables)


def test_run_event_sequence_is_unique_per_run(isolated_database) -> None:
    now = datetime.now(timezone.utc)
    with Session(isolated_database) as session:
        session.add(Run(id="run-1", build_id="build-1", status="running", last_sequence=0, started_at=now, created_at=now, updated_at=now))
        session.add(RunEventRecord(
            id="event-1",
            run_id="run-1",
            sequence=1,
            stage="starting",
            kind="started",
            message="started",
            timestamp=now,
        ))
        session.commit()

        session.add(RunEventRecord(
            id="event-2",
            run_id="run-1",
            sequence=1,
            stage="starting",
            kind="started",
            message="duplicate",
            timestamp=now,
        ))
        with pytest.raises(IntegrityError):
            session.commit()
