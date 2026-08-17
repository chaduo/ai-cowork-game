"""OpenAI-compatible Game Design Brainstorm provider.

The provider returns strict JSON only. It cannot mutate lifecycle state; the API
re-applies user input and the deterministic readiness gate before persistence.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agents.game_design_planner import GameDesignProviderError, GameDesignProviderNotConfigured
from app.contracts.design import BrainstormQuestion, CreatorGameDesignDraft, DesignSummary
from app.contracts.design_brainstorm import BrainstormInput, BrainstormTurn


def _content_text(content: Any) -> str:
    """Read the text variants used by OpenAI-compatible chat responses."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "".join(parts)
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    raise ValueError("provider content is not text")


def _decode_json(content: str) -> dict[str, Any]:
    """Extract the first JSON object even when the model adds short prose."""

    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1).strip() if fenced else cleaned
    try:
        decoded = json.loads(candidate)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        decoded = None
        for match in re.finditer(r"\{", candidate):
            try:
                decoded, _ = decoder.raw_decode(candidate[match.start() :])
                break
            except json.JSONDecodeError:
                continue
        if decoded is None:
            raise
    if not isinstance(decoded, dict):
        raise ValueError("provider JSON root is not an object")
    return decoded


def _question(value: Any, *, question_index: int) -> BrainstormQuestion | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = {"prompt": value}
    if not isinstance(value, dict):
        raise ValueError("provider question is not an object")
    normalized = dict(value)
    prompt = normalized.get("prompt") or normalized.get("question") or normalized.get("title")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("provider question has no prompt")
    question_id = normalized.get("id")
    if not isinstance(question_id, str) or not question_id.strip():
        question_id = f"provider-question-{question_index}"
    choices = normalized.get("choices", normalized.get("options", []))
    if choices is None:
        choices = []
    normalized_choices: list[dict[str, Any]] = []
    if not isinstance(choices, list):
        raise ValueError("provider question choices are not a list")
    for index, choice in enumerate(choices):
        if isinstance(choice, str):
            choice = {"title": choice}
        if not isinstance(choice, dict):
            raise ValueError("provider question choice is not an object")
        normalized_choice = dict(choice)
        title = normalized_choice.get("title") or normalized_choice.get("label") or normalized_choice.get("text")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("provider question choice has no title")
        choice_id = normalized_choice.get("id")
        if not isinstance(choice_id, str) or not choice_id.strip():
            choice_id = f"choice-{index + 1}"
        normalized_choices.append(
            {
                "id": choice_id,
                "title": title.strip(),
                "description": normalized_choice.get("description") if isinstance(normalized_choice.get("description"), str) else "",
                "recommended": _as_bool(normalized_choice.get("recommended", False)),
            }
        )
    question_payload = {
        "id": question_id,
        "prompt": prompt.strip(),
        "choices": normalized_choices[:4],
    }
    if isinstance(normalized.get("input_hint"), str):
        question_payload["input_hint"] = normalized["input_hint"]
    return BrainstormQuestion.model_validate(question_payload)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "是", "推荐"}
    return bool(value)


def _turn(decoded: dict[str, Any], base: CreatorGameDesignDraft) -> BrainstormTurn:
    """Normalize a provider proposal against the durable reducer-owned draft."""

    raw_draft = decoded.get("draft", {})
    if raw_draft is None:
        raw_draft = {}
    if not isinstance(raw_draft, dict):
        raise ValueError("provider draft is not an object")

    # The provider may propose language, but user decisions and readiness are
    # reducer-owned. Start from the current draft and merge only descriptive
    # fields so a partial model response remains safe and valid.
    updates: dict[str, Any] = {}
    for key in ("project_title", "scenario_id"):
        value = raw_draft.get(key)
        if isinstance(value, str) and value.strip():
            updates[key] = value.strip()
    raw_summary = raw_draft.get("summary")
    if isinstance(raw_summary, dict):
        summary = base.summary.model_dump(mode="json")
        for key, value in raw_summary.items():
            if key in {"title", "summary"} and isinstance(value, str) and value.strip():
                summary[key] = value.strip()
            elif key in {"highlights", "core_loop", "progression"} and isinstance(value, list):
                summary[key] = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        updates["summary"] = DesignSummary.model_validate(summary)

    next_question = decoded.get("next_question", decoded.get("nextQuestion"))
    if next_question is None and ("question" in decoded or "prompt" in decoded):
        next_question = {
            "id": decoded.get("question_id"),
            "prompt": decoded.get("prompt", decoded.get("question")),
            "choices": decoded.get("choices", decoded.get("options", [])),
            "input_hint": decoded.get("input_hint"),
        }
    if next_question is None and isinstance(raw_draft.get("clarification"), dict):
        next_question = raw_draft["clarification"].get("current_question")
    parsed_question = _question(next_question, question_index=base.clarification.question_index)
    if parsed_question is None and base.readiness.status != "ready" and base.clarification.status != "confirmed":
        raise ValueError("provider response has no next question")
    clarification = base.clarification.model_copy(update={"current_question": parsed_question})
    normalized_draft = base.model_copy(update={**updates, "clarification": clarification})
    return BrainstormTurn(draft=normalized_draft, next_question=parsed_question)


def _parse_failure_kind(error: Exception) -> str:
    if isinstance(error, json.JSONDecodeError):
        return "malformed_json"
    if isinstance(error, KeyError):
        return "missing_response_field"
    if error.__class__.__name__ == "ValidationError":
        return "schema_mismatch"
    return "invalid_response_shape"


class OpenAICompatibleGameDesignPlanner:
    def __init__(
        self,
        *,
        base_url: str | None,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 45.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = ""
            try:
                raw = error.read().decode("utf-8", errors="replace")
                parsed = json.loads(raw)
                detail = str(parsed.get("error", {}).get("message", ""))
            except (AttributeError, OSError, TypeError, ValueError):
                detail = ""
            detail = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", detail)[:400]
            suffix = f": {detail}" if detail else ""
            raise GameDesignProviderError(f"Game Design provider returned HTTP {error.code}{suffix}") from error
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise GameDesignProviderError("Game Design provider request failed") from error

    @staticmethod
    def _repair_payload(payload: dict[str, Any]) -> dict[str, Any]:
        repair = json.loads(json.dumps(payload))
        repair["max_tokens"] = min(int(repair.get("max_tokens", 1800)), 1800)
        repair["messages"] = [
            {
                "role": "system",
                "content": (
                    "上一次输出无法解析。现在只输出一个合法 JSON 对象，不能有 Markdown、解释文字或思考过程。"
                    "必须包含 next_question 对象；除非输入中的 readiness.first_playable_ready=true，否则 next_question 不得为 null。"
                    "draft 可省略。"
                ),
            },
            repair["messages"][1],
        ]
        return repair

    @staticmethod
    def _parse_turn(body: dict[str, Any], draft: CreatorGameDesignDraft) -> BrainstormTurn:
        choice = body["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content") or message.get("reasoning_content") or choice.get("text")
        decoded = _decode_json(_content_text(content))
        return _turn(decoded, draft)

    def plan_turn(self, project_id: str, draft: CreatorGameDesignDraft, user_input: BrainstormInput) -> BrainstormTurn:
        if not self.base_url or not self.api_key:
            raise GameDesignProviderNotConfigured("Game Design provider is not configured")
        payload = {
            "model": self.model,
            # Kimi K3's compatible endpoint currently accepts only temperature=1.
            # Other providers keep the lower-variance setting for structured turns.
            "temperature": 1 if self.model.lower().startswith("kimi") else 0.2,
            "max_tokens": 6000,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是游戏设计 Brainstorm 助手。只返回 JSON，不要 Markdown。"
                        "一次只处理一个最高优先级阻塞问题，给出 2 到 4 个中文选项，允许自由输入。"
                        "只做 First Playable 必需决定，不要替用户确认，不要返回 workflow 状态。"
                        "请返回增量结果：draft 可省略或只包含 summary、project_title、scenario_id；"
                        "不要输出 decisions/readiness/original_idea。必须包含 next_question（完成 First Playable 时可为 null）。"
                        'JSON 形如 {"next_question":{"id":"...","prompt":"...","choices":[]},"draft":{}}。'
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"project_id": project_id, "draft": draft.model_dump(mode="json"), "input": user_input.model_dump(mode="json")},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        try:
            return self._parse_turn(self._request_json(payload), draft)
        except (AttributeError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            try:
                return self._parse_turn(self._request_json(self._repair_payload(payload)), draft)
            except (AttributeError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as second_error:
                kind = _parse_failure_kind(second_error)
                raise GameDesignProviderError(f"Game Design provider returned invalid brainstorm JSON ({kind})") from second_error
