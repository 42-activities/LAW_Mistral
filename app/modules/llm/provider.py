"""Model-agnostic LLM interface (spec §5). Engines never import this; only the LLM service does."""

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings


@dataclass(frozen=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LlmError(RuntimeError):
    pass


class LlmProvider(Protocol):
    model: str

    def complete(self, messages: list[Message], *, json_mode: bool = False) -> Completion: ...


class MistralProvider:
    """Mistral chat completions over plain HTTPS."""

    def __init__(self, api_key: str, model: str, base_url: str, timeout_s: float) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def complete(self, messages: list[Message], *, json_mode: bool = False) -> Completion:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0,  # narration, not creativity
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LlmError(f"Mistral request failed: {exc}") from exc
        latency = int((time.monotonic() - started) * 1000)
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("Mistral returned an unexpected payload") from exc
        usage = body.get("usage") or {}
        return Completion(
            text=text,
            model=body.get("model", self.model),
            latency_ms=latency,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )


def default_provider() -> LlmProvider | None:
    s = get_settings()
    if not s.mistral_api_key:
        return None
    return MistralProvider(s.mistral_api_key, s.mistral_model, s.mistral_base_url, s.llm_timeout_s)
