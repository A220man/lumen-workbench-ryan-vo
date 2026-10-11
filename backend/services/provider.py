"""LLM provider adapters for advisory explanations.

Supports OpenAI-compatible (OpenAI, LiteLLM, OpenRouter, Ollama), Anthropic,
and Gemini generateContent endpoints. All adapters are async and use httpx.
"""
from __future__ import annotations

import httpx
from typing import Optional

from ..core.config import settings
from ..core.redaction import redact


class LLMError(Exception):
    pass


class LLMProvider:
    def __init__(
        self,
        provider: str,
        model: str,
        base_url: str,
        api_key: str,
        timeout: int = 30,
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    async def complete(self, system: str, prompt: str) -> str:
        """Send a request to the provider and return the raw response."""
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            if self.provider == "openai-compatible":
                return await self._openai(system, prompt, c)
            elif self.provider == "anthropic":
                return await self._anthropic(system, prompt, c)
            elif self.provider == "gemini":
                return await self._gemini(system, prompt, c)
            else:
                raise LLMError(f"Unsupported provider: {self.provider}")

    async def _openai(self, system: str, prompt: str, c: httpx.AsyncClient) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.llm_max_tokens,
            "temperature": 0.7,
        }
        resp = await c.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _anthropic(self, system: str, prompt: str, c: httpx.AsyncClient) -> str:
        url = f"{self.base_url}/v1/messages"
        headers = {"x-ai-key": self.api_key}
        payload = {
            "model": self.model,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = await c.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    async def _gemini(self, system: str, prompt: str, c: httpx.AsyncClient) -> str:
        url = f"{self.base_url}/generateContent"
        headers = {"x-goog-api-key": self.api_key}
        payload = {
            "model": self.model,
            "messages": [{"role": "USER", "parts": [{"text": prompt}]}],
            "generation_config": {"max_output_tokens": settings.llm_max_tokens},
            "stop_sequences": [],
        }
        resp = await c.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]