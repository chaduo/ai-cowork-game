import asyncio
import json
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.contracts.game_agent import ContractError, PendingDecision, RunEvent
from app.errors import ApiError
from app.models import Run
from app.repositories.runs import RUN_TERMINAL_STATUSES, RunRepository


router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    run_id: str = Field(min_length=1, max_length=120)
    build_id: str = Field(min_length=1, max_length=120)


class RunResponse(BaseModel):
    run_id: str
    build_id: str
    status: str
    last_sequence: int
    started_at: datetime
    ended_at: datetime | None
    cancel_requested_at: datetime | None
    error: ContractError | None = None
    pending_decision: PendingDecision | None = None


class RunInputRequest(BaseModel):
    decision_id: str = Field(min_length=1, max_length=120)
    response: Any


def _session(request: Request) -> Session:
    return Session(request.app.state.engine)


def _error(run: Run) -> ContractError | None:
    if not run.failure_code:
        return None
    return ContractError(code=run.failure_code, message=run.failure_message or run.failure_code)


def _response(repository: RunRepository, run: Run) -> RunResponse:
    return RunResponse(
        run_id=run.id,
        build_id=run.build_id,
        status=run.status,
        last_sequence=run.last_sequence,
        started_at=run.started_at,
        ended_at=run.ended_at,
        cancel_requested_at=run.cancel_requested_at,
        error=_error(run),
        pending_decision=repository.get_pending_decision(run.id),
    )


def _require(repository: RunRepository, run_id: str) -> Run:
    run = repository.get_run(run_id)
    if run is None:
        raise ApiError("run_not_found", "Run not found", [], 404)
    return run


@router.post("", response_model=RunResponse)
def create_run(payload: CreateRunRequest, request: Request) -> JSONResponse:
    with _session(request) as session:
        repository = RunRepository(session)
        existing = repository.get_run(payload.run_id)
        if existing is not None and existing.build_id != payload.build_id:
            raise ApiError("run_conflict", "Run id belongs to another build", [], 409)
        run = repository.create_run(payload.run_id, payload.build_id)
        session.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK if existing is not None else status.HTTP_201_CREATED,
            content=_response(repository, run).model_dump(mode="json"),
        )


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, request: Request) -> RunResponse:
    with _session(request) as session:
        repository = RunRepository(session)
        return _response(repository, _require(repository, run_id))


@router.get("/{run_id}/events", response_model=list[RunEvent])
def list_run_events(run_id: str, request: Request, after_sequence: int = Query(default=0, ge=0)) -> list[RunEvent]:
    with _session(request) as session:
        repository = RunRepository(session)
        _require(repository, run_id)
        return repository.list_events(run_id, after_sequence=after_sequence)


def _sse_line(event: RunEvent) -> str:
    payload = json.dumps(event.model_dump(mode="json"), ensure_ascii=False)
    return f"id: {event.sequence}\nevent: run_event\ndata: {payload}\n\n"


@router.get("/{run_id}/events/stream")
async def stream_run_events(
    run_id: str,
    request: Request,
    after_sequence: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    wait_seconds: float = Query(default=2.0, ge=0.1, le=30.0),
) -> StreamingResponse:
    with _session(request) as session:
        _require(RunRepository(session), run_id)
    try:
        header_sequence = int(last_event_id) if last_event_id is not None else 0
    except ValueError:
        header_sequence = 0
    cursor = max(after_sequence, header_sequence)
    engine = request.app.state.engine
    cursor_ref = [cursor]

    async def generate():
        deadline = time.monotonic() + wait_seconds
        while True:
            with Session(engine) as session:
                repository = RunRepository(session)
                run = repository.get_run(run_id)
                if run is None:
                    return
                events = repository.list_events(run_id, after_sequence=cursor_ref[0])
                terminal = run.status in RUN_TERMINAL_STATUSES
            for event in events:
                cursor_ref[0] = event.sequence
                yield _sse_line(event)
            if terminal or time.monotonic() >= deadline:
                return
            await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{run_id}/cancel", response_model=RunResponse)
def cancel_run(run_id: str, request: Request) -> RunResponse:
    with _session(request) as session:
        repository = RunRepository(session)
        _require(repository, run_id)
        try:
            run = repository.request_cancel(run_id)
        except ValueError as cause:
            raise ApiError("run_cancel_failed", str(cause), [], 409) from cause
        session.commit()
        return _response(repository, run)


@router.post("/{run_id}/input", response_model=RunResponse)
def continue_run(run_id: str, payload: RunInputRequest, request: Request) -> RunResponse:
    with _session(request) as session:
        repository = RunRepository(session)
        _require(repository, run_id)
        try:
            run = repository.continue_run(run_id, payload.decision_id, payload.response)
        except ValueError as cause:
            raise ApiError("run_input_failed", str(cause), [], 409) from cause
        session.commit()
        return _response(repository, run)
