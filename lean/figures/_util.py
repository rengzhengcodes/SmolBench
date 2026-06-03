"""Shared helpers for figure scripts."""

from __future__ import annotations


def pretty_model(name: str) -> str:
    """Display name for a model row's `model` field.

    The DeepSeek V3.2 entries are configured with `display_name` like `v3.2-high`
    (the `deepseek-` prefix dropped at config time); restore it for plotting so
    every model in the legend is unambiguously labeled by lab.
    """
    if name.startswith("v3.2-"):
        return f"deepseek {name}"
    return name


def model_sort_key(name: str, low_n: set[str]) -> tuple:
    """Order models alphabetically within (full-n, low-n) groups so low-n
    models (Sonnet 4.6, GPT-5.5 — only present in the smaller main_v3_2
    sweep) appear last in legends and bar groupings."""
    return (1 if name in low_n else 0, name)
