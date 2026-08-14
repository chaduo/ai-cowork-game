from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Run, RunEventRecord
from app.contracts.game_agent import ContractError, PendingDecision, RunEvent
from app.repositories.runs import RunRepository


def test_c07_migration_creates_runs_and_run_events_tables(isolated_database) -> None:
    tables = set(inspect(isolated_database).get_table_names())

    assert {"runs", "run_events", "run_pending_decisions"}.issubset(tables)
    assert "decision_id" in {column["name"] for column in inspect(isolated_database).get_columns("run_events")}


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


def event(run_id: str, sequence: int, *, kind: str = "progress", progress: float | None = 0.5, artifact_ref: str | None = None, error: ContractError | None = None, message: str = "working", decision_id: str | None = None) -> RunEvent:
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
        decision_id=decision_id,
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


def test_waiting_for_input_is_persisted_and_survives_restart_recovery(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-input", "build-input")
        decision = PendingDecision(
            decision_id="decision-1",
            prompt="选择继续方式",
            input_type="choice",
            options=["继续", "调整"],
        )
        repository.mark_waiting_for_input(
            "run-input",
            event("run-input", 1, kind="build.needs_input", progress=None, message=decision.prompt, decision_id=decision.decision_id),
            decision,
        )
        session.commit()

        assert repository.get_run("run-input").status == "waiting_for_input"
        assert repository.get_pending_decision("run-input").decision_id == "decision-1"
        assert repository.recover_orphaned_runs() == 0


def test_continuation_resolves_decision_on_same_run_and_is_idempotent(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-input", "build-input")
        decision = PendingDecision(decision_id="decision-1", prompt="选择继续方式", input_type="choice", options=["继续"])
        repository.mark_waiting_for_input(
            "run-input",
            event("run-input", 1, kind="build.needs_input", progress=None, decision_id=decision.decision_id),
            decision,
        )
        resumed = repository.continue_run("run-input", "decision-1", "继续")
        again = repository.continue_run("run-input", "decision-1", "继续")

        assert resumed.id == again.id == "run-input"
        assert repository.get_run("run-input").status == "running"
        assert repository.get_pending_decision("run-input") is None
        assert [item.sequence for item in repository.list_events("run-input")] == [1, 2]
        assert repository.list_events("run-input")[1].kind == "build.continued"


def test_continuation_rejects_wrong_decision_or_run(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-input", "build-input")
        decision = PendingDecision(decision_id="decision-1", prompt="选择继续方式")
        repository.mark_waiting_for_input(
            "run-input",
            event("run-input", 1, kind="build.needs_input", progress=None, decision_id=decision.decision_id),
            decision,
        )

        with pytest.raises(ValueError, match="decision"):
            repository.continue_run("run-input", "missing-decision", "继续")


def test_terminal_cancel_closes_pending_decision_without_promoting_run(isolated_database) -> None:
    with Session(isolated_database) as session:
        repository = RunRepository(session)
        repository.create_run("run-cancel-input", "build-input")
        decision = PendingDecision(decision_id="decision-cancel", prompt="选择继续方式")
        repository.mark_waiting_for_input(
            "run-cancel-input",
            event("run-cancel-input", 1, kind="build.needs_input", progress=None, decision_id=decision.decision_id),
            decision,
        )
        repository.request_cancel("run-cancel-input")
        repository.finish_run(
            "run-cancel-input",
            "cancelled",
            event(
                "run-cancel-input",
                3,
                kind="cancelled",
                progress=None,
                error=ContractError(code="cancelled", message="stopped"),
            ),
        )

        assert repository.get_run("run-cancel-input").status == "cancelled"
        assert repository.get_pending_decision("run-cancel-input") is None
