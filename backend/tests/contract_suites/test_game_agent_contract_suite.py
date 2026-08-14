import asyncio
from collections.abc import Callable

from app.agents.game_agent import GameAgent
from app.contracts.game_agent import GameBuildRequest


def assert_game_agent_contract(
    agent_factory: Callable[[], GameAgent],
    request_factory: Callable[[str], GameBuildRequest],
) -> None:
    """Run provider-neutral assertions against any GameAgent implementation."""

    async def exercise() -> None:
        agent = agent_factory()
        handle = await agent.start(request_factory("create"))
        events = [event async for event in agent.stream_events(handle)]
        result = await agent.result(handle)
        assert result.status == "succeeded"
        assert events
        assert [event.sequence for event in events] == sorted(event.sequence for event in events)
        assert events[-1].progress == 1

        replay = [event async for event in agent.stream_events(handle, after_sequence=events[0].sequence)]
        assert [event.sequence for event in replay] == [event.sequence for event in events[1:]]

        unsupported_handle = await agent.start(request_factory("unsupported-operation"))
        unsupported = await agent.result(unsupported_handle)
        assert unsupported.status == "unsupported"
        assert unsupported.error is not None
        assert unsupported.error.code == "unsupported_operation"

        cancelled_handle = await agent.start(request_factory("create"))
        await agent.cancel(cancelled_handle)
        cancelled = await agent.result(cancelled_handle)
        assert cancelled.status == "cancelled"
        cancelled_events = [event async for event in agent.stream_events(cancelled_handle)]
        assert cancelled_events[-1].kind == "cancelled"

    asyncio.run(exercise())
