from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Run, RunEventRecord
from app.contracts.game_agent import ContractError, RunEvent
from app.repositories.runs import RunRepository


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


def event(run_id: str, sequence: int, *, kind: str = "progress", progress: float | None = 0.5, artifact_ref: str | None = None, error: ContractError | None = None, message: str = "working") -> RunEvent:
    return RunEvent(
        run_id=run_id,
        sequence=sequence,
        stage="building",
        kind=kind,
        message=message,
        progress=progress,
        artifact_ref=artifact_ref,
        error=error,
        timestamp=datetime.now(timezone.utc),
    )


def test_repository_create_run_is_idempotent_and_replays_exact_sequence(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        first = repository.create_run("run-1", "build-1")
        second = repository.create_run("run-1", "build-1")
        repository.append_event(event("run-1", 1))
        repository.append_event(event("run-1", 2, progress=1, kind="completed", artifact_ref="dist/index.html"))

        assert first.id == second.id == "run-1"
        assert [item.sequence for item in repository.list_events("run-1", after_sequence=0)] == [1, 2]
        assert [item.sequence for item in repository.list_events("run-1", after_sequence=1)] == [2]


def test_repository_rejects_sequence_gaps_and_events_after_terminal(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-1", "build-1")
        with pytest.raises(ValueError, match="sequence"):
            repository.append_event(event("run-1", 2))

        repository.append_event(event("run-1", 1))
        repository.finish_run("run-1", "succeeded", event("run-1", 2, kind="completed", progress=1, artifact_ref="dist/index.html"))
        with pytest.raises(ValueError, match="terminal"):
            repository.append_event(event("run-1", 3))


def test_repository_sanitizes_diagnostics_before_persisting(isolated_database) -> None:
    secret_message = "Bearer abc123 token=super-secret sk-test-secret"
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-1", "build-1")
        stored = repository.append_event(event("run-1", 1, message=secret_message))

        assert "abc123" not in stored.message
        assert "super-secret" not in stored.message
        assert "sk-test-secret" not in stored.message


def test_repository_requires_confirmed_artifact_for_success(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-1", "build-1")
        with pytest.raises(ValueError, match="completed"):
            repository.finish_run("run-1", "succeeded", event("run-1", 1, kind="progress", progress=1))


def test_repository_cancel_waits_for_provider_terminal_confirmation(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-1", "build-1")
        repository.request_cancel("run-1")

        assert repository.get_run("run-1").status == "cancelling"
        repository.finish_run("run-1", "cancelled", event("run-1", 2, kind="cancelled", progress=None, error=ContractError(code="cancelled", message="stopped")))
        assert repository.get_run("run-1").status == "cancelled"


def test_repository_marks_non_terminal_runs_orphaned_without_success(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-1", "build-1")
        repository.create_run("run-2", "build-2")
        repository.finish_run("run-2", "failed", event("run-2", 1, kind="terminal", progress=None, error=ContractError(code="provider_failed", message="failed")))

        assert repository.recover_orphaned_runs() == 1
        assert repository.get_run("run-1").status == "orphaned"
        assert repository.get_run("run-2").status == "failed"
