"""Unit tests for context-budget helpers."""

from deduction.budget import whitespace_tokenizer, within_budget


def test_whitespace_tokenizer() -> None:
    assert whitespace_tokenizer("") == 0
    assert whitespace_tokenizer("one") == 1
    assert whitespace_tokenizer("one two three") == 3
    assert whitespace_tokenizer("  spaced   out  ") == 2


def test_within_budget_pass() -> None:
    ok, n = within_budget("a b c d e", budget_tokens=10, tokenizer=whitespace_tokenizer)
    assert ok is True
    assert n == 5


def test_within_budget_fail() -> None:
    ok, n = within_budget("a b c d e", budget_tokens=3, tokenizer=whitespace_tokenizer)
    assert ok is False
    assert n == 5


def test_within_budget_boundary() -> None:
    ok, n = within_budget("a b c", budget_tokens=3, tokenizer=whitespace_tokenizer)
    assert ok is True
    assert n == 3


def main() -> None:
    test_whitespace_tokenizer()
    test_within_budget_pass()
    test_within_budget_fail()
    test_within_budget_boundary()
    print("All budget tests passed.")


if __name__ == "__main__":
    main()
