"""
Context-budget helpers. Each `(model, target)` pair can only run the subset
of conditions whose full prompt fits inside the model's native context window.
Truncating to fit would confound density-dilution with truncation artifacts,
so we drop over-budget conditions instead of clipping them.

A tokenizer is an opaque callable `str -> int` that returns the token count
for a string under the target model's tokenizer. Users supply one either via
`hf_tokenizer(model_name)` (Hugging Face AutoTokenizer) or by writing their
own wrapper around a proprietary API's token counter.
"""

from typing import Callable, Tuple

Tokenizer = Callable[[str], int]


def whitespace_tokenizer(text: str) -> int:
    """Cheap proxy: count whitespace-separated tokens. Only for tests — not
    representative of any real model's tokenizer."""
    return len(text.split())


def hf_tokenizer(model_name_or_path: str) -> Tokenizer:
    """HuggingFace AutoTokenizer wrapped as a `str -> int` token counter."""
    from transformers import AutoTokenizer  # type: ignore
    tok = AutoTokenizer.from_pretrained(model_name_or_path)

    def count(text: str) -> int:
        return len(tok.encode(text, add_special_tokens=False))

    return count


def within_budget(
    prompt: str, budget_tokens: int, tokenizer: Tokenizer
) -> Tuple[bool, int]:
    """Returns (fits, actual_token_count)."""
    n = tokenizer(prompt)
    return n <= budget_tokens, n
