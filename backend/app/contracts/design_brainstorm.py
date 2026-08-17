from typing import Literal

from pydantic import Field, model_validator

from app.contracts.design import BrainstormChoice, BrainstormQuestion, CreatorGameDesignDraft
from app.contracts.gamespec import ContractModel


class BrainstormInput(ContractModel):
    action: Literal["start", "answer", "free_text", "continue"] = "start"
    question_id: str | None = Field(default=None, max_length=120)
    answer_id: str | None = Field(default=None, max_length=120)
    answer: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_action_payload(self) -> "BrainstormInput":
        if self.action == "answer" and not self.answer.strip():
            raise ValueError("answer action requires answer")
        if self.action == "free_text" and not self.answer.strip():
            raise ValueError("free_text action requires answer")
        if self.action in {"answer", "free_text"} and not self.question_id:
            raise ValueError(f"{self.action} action requires question_id")
        return self


class BrainstormTurn(ContractModel):
    draft: CreatorGameDesignDraft
    next_question: BrainstormQuestion | None = None

    @model_validator(mode="after")
    def validate_ready_question(self) -> "BrainstormTurn":
        if self.draft.clarification.status in {"ready", "confirmed"} and self.next_question is not None:
            raise ValueError("ready brainstorm turn cannot contain a follow-up question")
        return self


__all__ = ["BrainstormChoice", "BrainstormInput", "BrainstormQuestion", "BrainstormTurn"]
