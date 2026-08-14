from collections.abc import AsyncIterator
from typing import Protocol

from app.contracts.game_agent import AgentRunHandle, GameBuildRequest, GameBuildResult, RunEvent


class GameAgent(Protocol):
    """The only runtime surface BuildService is allowed to consume."""

    async def start(self, request: GameBuildRequest) -> AgentRunHandle:
        ...

    def stream_events(self, handle: AgentRunHandle, after_sequence: int = 0) -> AsyncIterator[RunEvent]:
        ...

    async def result(self, handle: AgentRunHandle) -> GameBuildResult:
        ...

    async def cancel(self, handle: AgentRunHandle) -> None:
        ...
