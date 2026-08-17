"""Deterministic planner used only by isolated tests and explicit demo mode."""

from app.contracts.design import BrainstormChoice, BrainstormQuestion, CreatorGameDesignDraft
from app.contracts.design_brainstorm import BrainstormInput, BrainstormTurn
from app.services.game_design_brainstorm import evaluate_first_playable_readiness, select_blocking_gap


class FakeGameDesignPlanner:
    def plan_turn(self, project_id: str, draft: CreatorGameDesignDraft, user_input: BrainstormInput) -> BrainstormTurn:
        gap = select_blocking_gap(draft)
        if gap is None:
            ready = draft.model_copy(
                update={
                    "clarification": draft.clarification.model_copy(update={"status": "ready", "current_question": None}),
                    "readiness": evaluate_first_playable_readiness(draft),
                }
            )
            return BrainstormTurn(draft=ready)

        idea = draft.original_idea
        if any(word in idea for word in ("农场", "种植", "农田")):
            prefix = "farm"
            choices = [
                BrainstormChoice(id="plant", title="种植和收获", description="安排作物、等待成长，再把收获变成新的投入。", recommended=True),
                BrainstormChoice(id="expand", title="扩大土地", description="通过经营成果解锁更大的农场。"),
            ]
        elif any(word in idea for word in ("探索", "灯塔", "线索", "遗迹")):
            prefix = "exploration"
            choices = [
                BrainstormChoice(id="discover", title="探索地点和线索", description="在地图中移动、观察并拼出新的线索。", recommended=True),
                BrainstormChoice(id="collect", title="收集重要物件", description="发现并整理能帮助推进目标的物件。"),
            ]
        elif any(word in idea for word in ("咖啡", "客人", "NPC", "角色")):
            prefix = "relationship"
            choices = [
                BrainstormChoice(id="interact", title="和角色互动", description="通过对话、委托或日常行动推进关系。", recommended=True),
                BrainstormChoice(id="serve", title="完成服务和任务", description="先完成具体工作，再让角色关系发生变化。"),
            ]
        else:
            prefix = "concept"
            choices = [
                BrainstormChoice(id="act", title="反复做一件核心行动", description="玩家通过行动、反馈和成长形成循环。", recommended=True),
                BrainstormChoice(id="discover", title="发现新的目标", description="玩家通过探索和线索让体验逐步展开。"),
            ]

        labels = {
            "core_experience": "玩家最想反复获得什么体验？",
            "player_action": "玩家每一轮最主要做什么？",
            "goal": "玩家为什么愿意继续推进？",
            "feedback": "玩家怎样马上知道自己的行动有效？",
            "progression": "玩家通过什么变化感到自己在成长？",
            "scope": "第一版最小可玩范围应该包含什么？",
            "completion": "玩家完成什么目标时算完成这一局？",
        }
        question = BrainstormQuestion(
            id=f"{prefix}-{gap}",
            prompt=labels[gap],
            choices=choices,
        )
        updated = draft.model_copy(
            update={
                "clarification": draft.clarification.model_copy(update={"status": "clarifying", "current_question": question}),
                "readiness": evaluate_first_playable_readiness(draft),
            }
        )
        return BrainstormTurn(draft=updated, next_question=question)
