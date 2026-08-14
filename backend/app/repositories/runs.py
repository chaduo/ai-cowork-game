import json
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.game_agent import ContractError, RunEvent
from app.models import Run, RunEventRecord, new_id, utc_now


RUN_TERMINAL_STATUSES = frozenset({
    "succeeded",
    "failed",
    "cancelled",
    "timed_out",
    "invalid_output",
    "unsupported",
    "orphaned",
})
RUN_ACTIVE_STATUSES = frozenset({"running", "cancelling"})

_REDACTION_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[^\s,;]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"), "token=[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]+\b"), "[REDACTED]"),
)


def sanitize_text(value: str, *, max_length: int = 4000) -> str:
    sanitized = value
    for pattern, replacement in _REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized[:max_length]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, run_id: str, build_id: str) -> Run:
        existing = self.session.get(Run, run_id)
        if existing is not None:
            if existing.build_id != build_id:
                raise ValueError("run id already belongs to another build")
            return existing
        run = Run(id=run_id, build_id=build_id, status="running", last_sequence=0, started_at=utc_now())
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, run_id: str) -> Run | None:
        return self.session.get(Run, run_id)

    def list_events(self, run_id: str, after_sequence: int = 0) -> list[RunEvent]:
        self._require_run(run_id)
        records = self.session.scalars(
            select(RunEventRecord)
            .where(RunEventRecord.run_id == run_id, RunEventRecord.sequence > after_sequence)
            .order_by(RunEventRecord.sequence.asc())
        ).all()
        return [self._to_contract(record) for record in records]

    def append_event(self, event: RunEvent) -> RunEvent:
        run = self._require_run(event.run_id)
        if run.status not in RUN_ACTIVE_STATUSES:
            raise ValueError("cannot append an event after terminal run state")
        self._assert_next_sequence(run, event.sequence)
        normalized = self._sanitize_event(event)
        record = RunEventRecord(
            id=new_id(),
            run_id=normalized.run_id,
            sequence=normalized.sequence,
            stage=normalized.stage,
            kind=normalized.kind,
            message=normalized.message,
            progress=normalized.progress,
            artifact_ref=normalized.artifact_ref,
            error_json=self._error_json(normalized.error),
            timestamp=normalized.timestamp,
        )
        self.session.add(record)
        run.last_sequence = normalized.sequence
        self.session.flush()
        return normalized

    def finish_run(self, run_id: str, status: str, terminal_event: RunEvent) -> Run:
        if status not in RUN_TERMINAL_STATUSES - {"orphaned"}:
            raise ValueError("invalid terminal run status")
        run = self._require_run(run_id)
        if run.status not in RUN_ACTIVE_STATUSES:
            if run.status == status:
                return run
            raise ValueError("run is already terminal")
        if terminal_event.run_id != run_id:
            raise ValueError("terminal event belongs to another run")
        if status == "succeeded" and (terminal_event.kind != "completed" or not terminal_event.artifact_ref):
            raise ValueError("succeeded run requires a completed event with an artifact")
        if status != "succeeded" and terminal_event.error is None:
            raise ValueError("non-success terminal run requires an error")
        self.append_event(terminal_event)
        run.status = status
        run.ended_at = utc_now()
        if terminal_event.error:
            run.failure_code = terminal_event.error.code
            run.failure_message = sanitize_text(terminal_event.error.message)
        self.session.flush()
        return run

    def request_cancel(self, run_id: str) -> Run:
        run = self._require_run(run_id)
        if run.status == "running":
            now = utc_now()
            self.append_event(RunEvent(
                run_id=run_id,
                sequence=run.last_sequence + 1,
                stage="cancelling",
                kind="cancel_requested",
                message="Cancellation requested",
                progress=None,
                timestamp=now,
            ))
            run.status = "cancelling"
            run.cancel_requested_at = now
            self.session.flush()
        elif run.status not in RUN_ACTIVE_STATUSES:
            return run
        return run

    def recover_orphaned_runs(self) -> int:
        runs = list(self.session.scalars(select(Run).where(Run.status.in_(RUN_ACTIVE_STATUSES))))
        for run in runs:
            now = utc_now()
            self.append_event(RunEvent(
                run_id=run.id,
                sequence=run.last_sequence + 1,
                stage="orphaned",
                kind="orphaned",
                message="Run interrupted before terminal confirmation",
                progress=None,
                error=ContractError(code="provider_disconnected", message="Run did not report a terminal result"),
                timestamp=now,
            ))
            run.status = "orphaned"
            run.failure_code = "provider_disconnected"
            run.failure_message = "Run did not report a terminal result"
            run.ended_at = now
        self.session.flush()
        return len(runs)

    def _require_run(self, run_id: str) -> Run:
        run = self.session.get(Run, run_id)
        if run is None:
            raise ValueError("run not found")
        return run

    @staticmethod
    def _assert_next_sequence(run: Run, sequence: int) -> None:
        expected = run.last_sequence + 1
        if sequence != expected:
            raise ValueError(f"event sequence must be {expected}")

    @staticmethod
    def _sanitize_event(event: RunEvent) -> RunEvent:
        error = event.error
        if error:
            error = error.model_copy(update={
                "message": sanitize_text(error.message),
                "details": [sanitize_text(detail) for detail in error.details],
            })
        return event.model_copy(update={
            "message": sanitize_text(event.message),
            "error": error,
        })

    @staticmethod
    def _error_json(error: ContractError | None) -> str | None:
        return json.dumps(error.model_dump(mode="json"), ensure_ascii=False) if error else None

    @staticmethod
    def _to_contract(record: RunEventRecord) -> RunEvent:
        error = ContractError.model_validate(json.loads(record.error_json)) if record.error_json else None
        return RunEvent(
            run_id=record.run_id,
            sequence=record.sequence,
            stage=record.stage,
            kind=record.kind,
            message=record.message,
            progress=record.progress,
            artifact_ref=record.artifact_ref,
            error=error,
            timestamp=_utc(record.timestamp),
        )
