import pytest
from pydantic import ValidationError

from app.contracts.design import ClarificationState, CreatorGameDesignDraft
from app.contracts.design_brainstorm import (
    BrainstormChoice,
    BrainstormInput,
    BrainstormQuestion,
    BrainstormTurn,
)


def _draft(**clarification_overrides):
    clarification = {
        "question_index": 0,
        "status": "clarifying",
        "custom_input": "",
        **clarification_overrides,
    }
    return CreatorGameDesignDraft(
        original_idea="做一个在海边经营修理铺的游戏",
        project_title="海边修理铺",
        scenario_id="planner",
        summary={
            "title": "海边修理铺",
            "summary": "玩家经营一间海边修理铺。",
            "highlights": [],
            "core_loop": [],
            "progression": [],
        },
        clarification=clarification,
    )


def test_brainstorm_question_round_trips_inside_the_draft():
    question = BrainstormQuestion(
        id="player-goal",
        prompt="玩家每天最想完成什么？",
        choices=[
            BrainstormChoice(id="repair", title="修理顾客的物品", description="通过修理获得收入。"),
            BrainstormChoice(id="explore", title="出海寻找材料", description="通过探索发现稀有材料。"),
        ],
    )

    draft = _draft(current_question=question.model_dump(mode="json"))
    restored = CreatorGameDesignDraft.model_validate(draft.model_dump(mode="json"))

    assert restored.clarification.current_question == question


def test_brainstorm_input_requires_answer_for_answer_actions():
    with pytest.raises(ValidationError):
        BrainstormInput(action="answer", question_id="player-goal")


def test_brainstorm_turn_cannot_mark_ready_with_a_follow_up_question():
    question = BrainstormQuestion(id="scope", prompt="第一版做多大？", choices=[])

    with pytest.raises(ValidationError):
        BrainstormTurn(
            draft=_draft(question_index=1, status="ready", current_question=None),
            next_question=question,
        )
