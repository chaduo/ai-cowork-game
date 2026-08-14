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
    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    response: str = ""
    answer_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class ClarificationState(ContractModel):
    question_index: int = Field(default=0, ge=0)
    status: Literal["clarifying", "ready", "iterating", "confirmed"] = "clarifying"
    custom_input: str = ""


class CreatorGameDesignDraft(ContractModel):
    schema_version: Literal[1] = 1
    original_idea: str = Field(min_length=1)
    project_title: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    summary: DesignSummary
    decisions: list[DesignDecision] = Field(default_factory=list)
    clarification: ClarificationState = Field(default_factory=ClarificationState)
