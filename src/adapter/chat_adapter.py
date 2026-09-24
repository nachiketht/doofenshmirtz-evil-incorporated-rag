"""Ollama JSON completion for routing and other small classify calls."""

from __future__ import annotations

import json

import httpx

from ingestion.config import DEFAULT_OLLAMA_BASE_URL


class OllamaChatAdapter:
    def __init__(
        self,
        model_name: str,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        timeout: float = 120.0,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete_json(self, prompt: str, schema: dict | None = None) -> dict:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": schema if schema is not None else "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        payload = response.json()
        raw = payload.get("response")
        if isinstance(raw, dict):
            return raw
        if not isinstance(raw, str) or not raw.strip():
            raise RuntimeError("Ollama returned an empty JSON completion.")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError("Ollama JSON completion was not an object.")
        return parsed
