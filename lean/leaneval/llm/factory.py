"""Build an LLMClient from a config dict."""

from __future__ import annotations

from .base import LLMClient


def build_client(cfg: dict) -> LLMClient:
    """`cfg` shape: {"provider": "anthropic" | "openai_compat", ...}."""
    provider = cfg["provider"]
    if provider == "anthropic":
        from .anthropic import AnthropicClient
        return AnthropicClient(api_key=cfg.get("api_key"))
    if provider == "openai_compat":
        from .openai_compat import OpenAICompatClient
        return OpenAICompatClient(
            base_url=cfg.get("base_url", "https://api.pinference.ai/api/v1"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env", "PRIME_INTELLECT_API_KEY"),
            team_id=cfg.get("team_id"),
            team_id_env=cfg.get("team_id_env", "PRIME_INTELLECT_TEAM_ID"),
            timeout=cfg.get("timeout", 600.0),
        )
    raise ValueError(f"unknown provider: {provider!r}")
