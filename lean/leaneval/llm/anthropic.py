"""Anthropic SDK client with prompt-cache support."""

from __future__ import annotations

import os

import anthropic

from .base import LLMClient, LLMResponse, Message


class AnthropicClient(LLMClient):
    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self._client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        extra_params: dict | None = None,  # ignored by Anthropic SDK path
    ) -> LLMResponse:
        _ = extra_params
        system_blocks: list[dict] = []
        chat: list[dict] = []
        for m in messages:
            block: dict = {"type": "text", "text": m.content}
            if m.cache_breakpoint:
                block["cache_control"] = {"type": "ephemeral"}
            if m.role == "system":
                system_blocks.append(block)
            else:
                chat.append({"role": m.role, "content": [block]})

        rsp = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_blocks if system_blocks else anthropic.NOT_GIVEN,
            messages=chat,
        )

        text_parts: list[str] = []
        thinking_parts: list[str] = []
        for b in rsp.content:
            if b.type == "text":
                text_parts.append(b.text)
            elif b.type == "thinking":
                # Surfaced when extended thinking is enabled. `b.thinking`
                # holds the model's reasoning trace.
                thinking_parts.append(getattr(b, "thinking", "") or "")
        text = "".join(text_parts)
        reasoning = "\n\n".join(p for p in thinking_parts if p)

        usage = rsp.usage
        return LLMResponse(
            text=text,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            model=rsp.model,
            finish_reason=rsp.stop_reason,
            reasoning=reasoning,
        )
