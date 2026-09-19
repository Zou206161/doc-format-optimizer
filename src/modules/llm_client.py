"""Unified LLM client — wraps OpenAI-compatible chat completions API."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAYS = [2, 5, 10]


class LLMClient:
    def __init__(self) -> None:
        self._api_key = os.getenv("LLM_API_KEY", "")
        self._base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self._model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format_json: bool = False,
    ) -> str:
        """Send a chat completion request and return the assistant's text response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format_json:
            kwargs["response_format"] = {"type": "json_object"}

        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as exc:
                last_err = exc
                logger.warning("LLM call attempt %d failed: %s", attempt + 1, exc)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAYS[attempt])
        raise RuntimeError(f"LLM call failed after {_MAX_RETRIES} retries: {last_err}")

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Like chat() but parses the response as JSON."""
        raw = self.chat(
            system_prompt,
            user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_json=True,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
            raise ValueError(f"Cannot parse LLM response as JSON: {raw[:200]}...")


llm_client = LLMClient()
