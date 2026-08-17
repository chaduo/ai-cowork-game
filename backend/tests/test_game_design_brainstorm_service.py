from app.contracts.design import CreatorGameDesignDraft
from app.contracts.design_brainstorm import BrainstormInput, BrainstormQuestion
from app.services.game_design_brainstorm import (
    apply_brainstorm_input,
    evaluate_first_playable_readiness,
    select_blocking_gap,
)


def _draft() -> CreatorGameDesignDraft:
    return CreatorGameDesignDraft(
        original_idea="一个让玩家经营海边咖啡店并认识常客的游戏",
        project_title="海边咖啡店",
        scenario_id="generic",
        summary={
            "title": "海边咖啡店",
            "summary": "咖啡店经营和常客关系",
            "highlights": [],
            "core_loop": [],
            "progression": [],
        },
        clarification={
            "current_question": {
                "id": "core-experience",
                "prompt": "玩家每天最主要做什么？",
                "choices": [
                    {"id": "serve", "title": "接待顾客", "description": "", "recommended": True},
                ],
            }
        },
    )


def test_user_answer_is_recorded_as_confirmed_and_advances_question() -> None:
    draft = _draft()

    updated = apply_brainstorm_input(
        draft,
        BrainstormInput(action="answer", question_id="core-experience", answer_id="serve", answer="接待顾客"),
        turn=1,
    )

    assert updated.decisions[0].answer == "接待顾客"
    assert updated.decisions[0].answer_id == "serve"
    assert select_blocking_gap(updated) == "player_action"
    assert updated.clarification.question_index == 1


def test_inferred_summary_does_not_make_first_playable_ready() -> None:
    draft = _draft()
    draft.summary.summary = "AI 推断玩家会探索并收集线索"

    readiness = evaluate_first_playable_readiness(draft)

    assert readiness.status == "not_ready"
    assert "core_experience" in readiness.unresolved_decisions


def test_six_turn_budget_stops_new_questions() -> None:
    draft = _draft()
    draft.clarification.question_index = 6
    draft.clarification.status = "ready"

    assert select_blocking_gap(draft) is None
    assert evaluate_first_playable_readiness(draft).status in {"ready", "blocked", "not_ready"}
