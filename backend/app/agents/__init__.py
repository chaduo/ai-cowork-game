"""Provider-neutral runtime interfaces and deterministic test implementations."""

from app.agents.fake_game_agent import FakeGameAgent
from app.agents.game_agent import GameAgent

__all__ = ["FakeGameAgent", "GameAgent"]
