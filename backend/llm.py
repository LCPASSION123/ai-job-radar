"""Optional provider adapters; no network request occurs unless an application explicitly invokes one."""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class LLMSettings:
    provider: str = os.getenv("LLM_PROVIDER", "local")
    openai_compatible_base_url: str | None = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    def configured(self) -> bool:
        if self.provider == "openai_compatible":
            return bool(self.openai_compatible_base_url and self.openai_api_key)
        if self.provider == "gemini":
            return bool(self.gemini_api_key)
        return self.provider == "local"


def provider_status() -> dict[str, str | bool]:
    settings = LLMSettings()
    return {"provider": settings.provider, "configured": settings.configured(), "note": "MVP uses local deterministic templates; credentials are never returned by the API."}


class OpenAICompatibleAdapter:
    """Opt-in adapter for approved OpenAI-compatible endpoints (including GPT providers)."""
    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "messages": [{"role": "user", "content": prompt}]})
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


class GeminiAdapter:
    """Opt-in adapter for Gemini; callers must keep its API key only in their local environment."""
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key, self.model = api_key, model

    async def generate(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
