from app.contracts.design import CreatorGameDesignDraft, DesignDecision
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


def test_provider_question_ids_use_question_text_for_readiness_categories() -> None:
    draft = _draft().model_copy(
        update={
            "decisions": [
                DesignDecision(
                    question_id="provider-question-1",
                    question="除了移动之外，玩家是否拥有主动操作手段？",
                    answer_id="dash",
                    answer="冲刺",
                    provenance="user_confirmed",
                ),
                DesignDecision(
                    question_id="provider-question-2",
                    question="被敌人抓到会发生什么、胜负如何判定？",
                    answer_id="one-hit",
                    answer="一击即败",
                    provenance="user_confirmed",
                ),
                DesignDecision(
                    question_id="provider-question-3",
                    question="第一版最小配置和场景规模是什么？",
                    answer_id="small",
                    answer="单屏小房间",
                    provenance="user_confirmed",
                ),
            ]
        }
    )

    readiness = evaluate_first_playable_readiness(draft)

    assert "player_action" not in readiness.unresolved_decisions
    assert "completion" not in readiness.unresolved_decisions
    assert "scope" not in readiness.unresolved_decisions


def test_explicit_goal_in_original_idea_counts_as_user_goal() -> None:
    draft = _draft().model_copy(
        update={
            "original_idea": "封闭场景中躲避敌人，坚持到倒计时结束即可获胜。",
            "decisions": [
                DesignDecision(
                    question_id="provider-question-1",
                    question="玩家是否拥有主动操作手段？",
                    answer_id="dash",
                    answer="冲刺",
                    provenance="user_confirmed",
                ),
                DesignDecision(
                    question_id="provider-question-2",
                    question="被敌人抓到会发生什么、胜负如何判定？",
                    answer_id="one-hit",
                    answer="一击即败",
                    provenance="user_confirmed",
                ),
                DesignDecision(
                    question_id="provider-question-3",
                    question="第一版最小配置和场景规模是什么？",
                    answer_id="small",
                    answer="单屏小房间",
                    provenance="user_confirmed",
                ),
            ],
        }
    )

    readiness = evaluate_first_playable_readiness(draft)

    assert "goal" not in readiness.unresolved_decisions
