"""Provider-neutral contract for the Game Design Brainstorm planner."""

from typing import Protocol

from app.contracts.design import CreatorGameDesignDraft
from app.contracts.design_brainstorm import BrainstormInput, BrainstormTurn


class GameDesignPlannerError(RuntimeError):
    """Base class for safe, user-facing planner failures."""


class GameDesignProviderNotConfigured(GameDesignPlannerError):
    pass


class GameDesignProviderError(GameDesignPlannerError):
    pass


class GameDesignPlanner(Protocol):
    def plan_turn(
        self,
        project_id: str,
        draft: CreatorGameDesignDraft,
        user_input: BrainstormInput,
    ) -> BrainstormTurn:
        ...
