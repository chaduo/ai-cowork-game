"""Deterministic state reducer and readiness rules for Game Design Brainstorm.

The provider proposes language and choices; this module owns the durable state
transition and the finite First Playable gate.  It deliberately has no HTTP or
provider dependencies so that the same rules run in API tests and production.
"""

from __future__ import annotations

from typing import Final
from uuid import uuid4

from app.contracts.design import CreatorGameDesignDraft, DesignDecision, DesignReadiness
from app.contracts.design_brainstorm import BrainstormInput


GAP_ORDER: Final[tuple[str, ...]] = (
    "core_experience",
    "player_action",
    "goal",
    "scope",
    "completion",
    "feedback",
    "progression",
)
FIRST_PLAYABLE_GAPS: Final[tuple[str, ...]] = ("core_experience", "player_action", "goal", "scope", "completion")
TURN_BUDGET: Final[int] = 6


def _category(question_id: str) -> str | None:
    value = question_id.lower().replace("-", "_")
    aliases = {
        "core_experience": ("core", "experience", "主体验", "核心"),
        "scope": ("scope", "v1", "size", "范围", "第一版", "最小", "配置", "规模"),
        "completion": ("complete", "completion", "finish", "win", "success", "完成", "结束", "胜负", "判定", "抓到"),
        "player_action": ("action", "loop", "activity", "行动", "玩法", "操作", "移动", "互动", "冲刺"),
        "goal": ("goal", "motivation", "purpose", "目标", "动机", "继续", "坚持"),
        "feedback": ("feedback", "response", "reward", "反馈", "回馈"),
        "progression": ("progress", "growth", "advance", "成长", "进展"),
    }
    for category, words in aliases.items():
        if any(word in value for word in words):
            return category
    return None


def _confirmed_categories(draft: CreatorGameDesignDraft) -> set[str]:
    categories: set[str] = set()
    for decision in draft.decisions:
        if decision.provenance not in {None, "user_confirmed"}:
            continue
        category = _category(f"{decision.question_id} {decision.question}")
        if category:
            categories.add(category)
    # The Original Idea is itself user input. When it explicitly states the
    # player's objective, do not force a redundant AI question just because no
    # provider-generated decision has been assigned the generic ``goal`` id.
    idea = draft.original_idea.lower()
    if any(token in idea for token in ("目标", "目的", "获胜", "胜利", "坚持", "生存", "逃脱", "完成")):
        categories.add("goal")
    return categories


def select_blocking_gap(draft: CreatorGameDesignDraft) -> str | None:
    """Return the next finite blocking category, or ``None`` at the stop rule."""

    if draft.clarification.question_index >= TURN_BUDGET:
        return None
    confirmed = _confirmed_categories(draft)
    return next((gap for gap in FIRST_PLAYABLE_GAPS if gap not in confirmed), None)


def evaluate_first_playable_readiness(draft: CreatorGameDesignDraft) -> DesignReadiness:
    confirmed = _confirmed_categories(draft)
    unresolved = [gap for gap in FIRST_PLAYABLE_GAPS if gap not in confirmed]
    full_gdd_missing = [gap for gap in GAP_ORDER if gap not in confirmed]
    if not unresolved:
        status = "ready"
        blockers: list[str] = []
    elif draft.clarification.question_index >= TURN_BUDGET:
        status = "blocked"
        blockers = ["question_budget_exhausted"]
    else:
        status = "not_ready"
        blockers = []
    return DesignReadiness(
        status=status,
        blockers=blockers,
        unresolved_decisions=unresolved,
        first_playable_ready=not unresolved,
        full_gdd_ready=not full_gdd_missing,
    )


def apply_brainstorm_input(
    draft: CreatorGameDesignDraft,
    user_input: BrainstormInput,
    *,
    turn: int | None = None,
) -> CreatorGameDesignDraft:
    """Apply one user-confirmed answer without letting provider text become truth."""

    if user_input.action not in {"answer", "free_text"}:
        return draft
    question_id = user_input.question_id or ""
    question = draft.clarification.current_question
    question_text = question.prompt if question and question.id == question_id else question_id
    answer = user_input.answer.strip()
    answer_id = user_input.answer_id or "free-text"
    decision = DesignDecision(
        decision_id=str(uuid4()),
        question_id=question_id,
        question=question_text,
        response="",
        answer_id=answer_id,
        answer=answer,
        provenance="user_confirmed",
    )
    decisions = [item for item in draft.decisions if item.question_id != question_id]
    decisions.append(decision)
    clarification = draft.clarification.model_copy(
        update={
            "question_index": turn if turn is not None else draft.clarification.question_index + 1,
            "status": "clarifying",
            "custom_input": answer if user_input.action == "free_text" else draft.clarification.custom_input,
            "current_question": None,
        }
    )
    return draft.model_copy(update={"decisions": decisions, "clarification": clarification})
