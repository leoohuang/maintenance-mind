"""LLM client wrapping an OpenAI-compatible chat completions API."""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()


class LLMClient:
    """Thin wrapper around the OpenAI SDK used by all agent modules."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.environ.get("BERGET_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        self.base_url = base_url or os.environ.get(
            "BERGET_BASE_URL",
            os.environ.get("OPENAI_BASE_URL", "https://api.berget.ai/v1"),
        )
        self.model = model or os.environ.get(
            "BERGET_MODEL",
            os.environ.get("OPENAI_MODEL", "openai/gpt-oss-120b"),
        )
        if not self.api_key:
            raise RuntimeError(
                "No API key found. Set BERGET_API_KEY or OPENAI_API_KEY "
                "in your .env file."
            )
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @retry(
        retry=retry_if_exception_type(
            (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True,
    )
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
        max_tokens: int = 2048,
    ):
        """Send a chat completion request."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = response_format
        return self.client.chat.completions.create(**kwargs)

    def chat_json(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Request and parse a JSON response."""
        response = self.chat(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
            return {}


client = LLMClient()
