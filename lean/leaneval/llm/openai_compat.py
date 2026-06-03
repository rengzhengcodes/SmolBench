"""OpenAI-compatible HTTP client (Prime Intellect / vLLM)."""

from __future__ import annotations

import os
import time

import httpx

from .base import LLMClient, LLMResponse, Message

DEFAULT_PRIME_BASE_URL = "https://api.pinference.ai/api/v1"

# Retry on transient 429 / 5xx — upstream providers (e.g. Qwen via PI) have
# tight rate quotas that bursty concurrent traffic can trip even when global
# concurrency looks fine. Honor Retry-After when present, else exp-backoff.
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_RETRY_ATTEMPTS = 4
_RETRY_BACKOFF_S = (5.0, 15.0, 45.0, 120.0)


class OpenAICompatClient(LLMClient):
    name = "openai_compat"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_PRIME_BASE_URL,
        api_key: str | None = None,
        api_key_env: str = "PRIME_INTELLECT_API_KEY",
        team_id: str | None = None,
        team_id_env: str = "PRIME_INTELLECT_TEAM_ID",
        timeout: float = 1800.0,
    ) -> None:
        key = api_key or os.environ.get(api_key_env)
        if not key:
            raise RuntimeError(
                f"missing API key: pass api_key= or set {api_key_env}"
            )
        team = team_id if team_id is not None else os.environ.get(team_id_env)
        self._base_url = base_url.rstrip("/")
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if team:
            headers["X-Prime-Team-ID"] = team
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers=headers,
        )

    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        extra_params: dict | None = None,
    ) -> LLMResponse:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if extra_params:
            payload.update(extra_params)
        rsp = None
        for attempt in range(_RETRY_ATTEMPTS):
            rsp = self._client.post("/chat/completions", json=payload)
            if rsp.status_code not in _RETRY_STATUSES:
                break
            if attempt + 1 == _RETRY_ATTEMPTS:
                break
            # Honor server-suggested Retry-After if present and reasonable.
            retry_after = rsp.headers.get("retry-after")
            wait_s: float
            if retry_after:
                try:
                    wait_s = min(float(retry_after), 300.0)
                except ValueError:
                    wait_s = _RETRY_BACKOFF_S[attempt]
            else:
                wait_s = _RETRY_BACKOFF_S[attempt]
            time.sleep(wait_s)
        assert rsp is not None
        if rsp.status_code >= 400:
            # Surface the API's error body, not just the status line — most
            # provider 4xx errors carry useful detail (context-too-long,
            # invalid model, billing, etc.) in the JSON body.
            body = rsp.text[:1000]
            raise httpx.HTTPStatusError(
                f"{rsp.status_code} from {rsp.request.url}: {body}",
                request=rsp.request, response=rsp,
            )
        data = rsp.json()

        choice = data["choices"][0]
        msg = choice["message"]
        text = msg.get("content") or ""
        # Capture the model's reasoning channel if present. DeepSeek-R1, GPT-5
        # reasoning, and other CoT-emitting models put it in `reasoning_content`
        # (a non-OpenAI extension; some providers use `reasoning`).
        reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            cache_read_tokens=0,
            cache_creation_tokens=0,
            model=data.get("model", model),
            finish_reason=choice.get("finish_reason"),
            reasoning=reasoning,
        )

    def list_models(self) -> list[str]:
        rsp = self._client.get("/models")
        rsp.raise_for_status()
        return [m["id"] for m in rsp.json().get("data", [])]
