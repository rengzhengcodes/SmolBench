"""Provider-agnostic LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    # If True, mark this message as a prompt-cache breakpoint (Anthropic only;
    # OpenAI-compatible providers ignore the hint).
    cache_breakpoint: bool = False


@dataclass(frozen=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    model: str = ""
    finish_reason: str | None = None
    # Reasoning channel: thinking blocks (Anthropic), reasoning_content
    # (DeepSeek-R1 / OpenAI extended-thinking). Empty string when the API/
    # model doesn't surface a separate reasoning channel.
    reasoning: str = ""


class LLMClient(ABC):
    """Minimal completion interface. Implementations must populate token counts.

    `cache_read_tokens` / `cache_creation_tokens` are the dependent variables for
    cost analysis; OpenAI-compatible providers should report 0 for both.
    """

    name: str

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        extra_params: dict | None = None,
    ) -> LLMResponse: ...
