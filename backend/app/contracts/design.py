from datetime import datetime
from typing import Literal

from pydantic import Field

from app.contracts.gamespec import ContractModel


class DesignSummary(ContractModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    highlights: list[str] = Field(default_factory=list)
    core_loop: list[str] = Field(default_factory=list)
    progression: list[str] = Field(default_factory=list)


class DesignDecision(ContractModel):
    decision_id: str | None = Field(default=None, min_length=1, max_length=120)
    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    response: str = ""
    answer_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    provenance: Literal["user_confirmed", "ai_inferred"] | None = None
    supersedes_decision_id: str | None = Field(default=None, min_length=1, max_length=120)


class BrainstormChoice(ContractModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=1000)
    recommended: bool = False


class BrainstormQuestion(ContractModel):
    id: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=2000)
    choices: list[BrainstormChoice] = Field(default_factory=list, max_length=4)
    input_hint: str = Field(default="也可以直接描述你的想法。", max_length=500)


class ClarificationState(ContractModel):
    question_index: int = Field(default=0, ge=0)
    status: Literal["clarifying", "ready", "iterating", "confirmed"] = "clarifying"
    custom_input: str = ""
    current_question: BrainstormQuestion | None = Field(default=None, exclude_if=lambda value: value is None)


class DesignReadiness(ContractModel):
    status: Literal["not_ready", "ready", "blocked"] = "not_ready"
    blockers: list[str] = Field(default_factory=list)
    unresolved_decisions: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None


class CreatorGameDesignDraft(ContractModel):
    schema_version: Literal[1] = 1
    original_idea: str = Field(min_length=1)
    project_title: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    summary: DesignSummary
    decisions: list[DesignDecision] = Field(default_factory=list)
    clarification: ClarificationState = Field(default_factory=ClarificationState)
    readiness: DesignReadiness = Field(default_factory=DesignReadiness)
