"""OpenAI-compatible Game Design Brainstorm provider.

The provider returns strict JSON only. It cannot mutate lifecycle state; the API
re-applies user input and the deterministic readiness gate before persistence.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agents.game_design_planner import GameDesignProviderError, GameDesignProviderNotConfigured
from app.contracts.design import CreatorGameDesignDraft
from app.contracts.design_brainstorm import BrainstormInput, BrainstormTurn


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

    def plan_turn(self, project_id: str, draft: CreatorGameDesignDraft, user_input: BrainstormInput) -> BrainstormTurn:
        if not self.base_url or not self.api_key:
            raise GameDesignProviderNotConfigured("Game Design provider is not configured")
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是游戏设计 Brainstorm 助手。只返回 JSON，不要 Markdown。"
                        "一次只处理一个最高优先级阻塞问题，给出 2 到 4 个中文选项，允许自由输入。"
                        "只做 First Playable 必需决定，不要替用户确认，不要返回 workflow 状态。"
                        "JSON 必须符合 {draft:{...},next_question:{...}|null}。"
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
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise GameDesignProviderError(f"Game Design provider returned HTTP {error.code}") from error
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise GameDesignProviderError("Game Design provider request failed") from error
        try:
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("provider content is not text")
            fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
            decoded = json.loads(fenced.group(1) if fenced else content)
            return BrainstormTurn.model_validate(decoded)
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise GameDesignProviderError("Game Design provider returned invalid brainstorm JSON") from error
