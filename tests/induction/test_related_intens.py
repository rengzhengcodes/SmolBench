"""Test the ``related_intens`` review arm: irrelevant rules of the real rules' form.

The arm is the intensional rules, then a seeded stream of irrelevant rule lines,
then (only if needed) whitespace, token-matched to the question's ``extens`` prompt.
"""

import hashlib
import itertools
import math
import re

import pytest
from conftest import StubTokenizer, import_run_study
from tests.induction._periodic import PERIODIC_TMPL, POSITIVE_ARMS

from smolbench.induction import periodic
from smolbench.induction._common import Prompter
from smolbench.induction.periodic import (
    CONDITIONS,
    REVIEW_CONDITIONS,
    Condition,
    PeriodicConfig,
    get_periodic_prompts,
    numeric_count_query_gen,
    related_rule_lines,
)

RULE = re.compile(r"Every (\d+) positions write ([a-z]+)\.\n")
ALL_ARMS = {**POSITIVE_ARMS, **REVIEW_CONDITIONS}


class WordyTokenizer(StubTokenizer):
    """A second stub with a different per-word cost, so the line counts differ."""

    name = "wordy"

    def count(self, text: str) -> int:
        """Return the stub token count with three characters per word token."""
        total = 0
        for chunk in re.findall(r"\s+|\S+", text):
            if chunk.isspace():
                total += 1 if len(set(chunk)) == 1 and len(chunk) > 8 else math.ceil(len(chunk) / 2)
            else:
                total += math.ceil(len(chunk) / 3)
        return total


class NewlineMergeTokenizer(StubTokenizer):
    """A newline-only run is one token per two newlines; any other run costs one more.

    So the first pad unit inserted between ``.\\n`` and ``\\nQ:`` costs two tokens and a
    remainder of one token is unreachable by whitespace alone, as measured on real
    tokenizers. ``" \\t" * n`` alone costs ``n``, so ``choose_whitespace_unit`` accepts it.
    """

    name = "newline-merge"

    def count(self, text: str) -> int:
        """Return the token count with the newline merge described above."""
        total = 0
        for chunk in re.findall(r"\s+|\S+", text):
            if not chunk.isspace():
                total += math.ceil(len(chunk) / 4)
            elif set(chunk) <= {"\n"}:
                total += math.ceil(len(chunk) / 2)
            else:
                total += math.ceil(len(chunk) / 2) + ("\n" in chunk)
        return total


def _prompter() -> Prompter:
    return Prompter(PERIODIC_TMPL, numeric_count_query_gen)


def _queries(cfg, tokenizer, conditions=ALL_ARMS):
    return list(get_periodic_prompts(cfg, _prompter(), tokenizer=tokenizer, conditions=conditions))


def _split(intens: str, related: str) -> tuple[str, str]:
    """(added rule lines, trailing whitespace) of a related prompt, checking its frame."""
    q = intens.index("\nQ:")
    assert related.startswith(intens[:q]), "related must start with the intens rules"
    tail = related.rindex("\nQ:")
    assert related[tail:] == intens[q:], "the question text must be identical"
    middle = related[q:tail]
    m = re.fullmatch(r"((?:Every \d+ positions write [a-z]+\.\n)*)(\s*)", middle)
    assert m, f"unexpected text between the rules and the question: {middle[:200]!r}"
    return m.group(1), m.group(2)


def _permitted(label: str, real) -> bool:
    return label not in real and not any(r in label or label in r for r in real)


# ------------------------------------------------------------------ the stream


def test_stream_is_deterministic_and_seed_dependent():
    p2l, _ = PeriodicConfig(n=9, labels=9, seed=0).generate_sequence()
    a = list(itertools.islice(related_rule_lines(p2l, 0), 300))
    b = list(itertools.islice(related_rule_lines(p2l, 0), 300))
    c = list(itertools.islice(related_rule_lines(p2l, 1), 300))
    assert a == b and a != c


def test_stream_lines_obey_the_rule_form_periods_and_label_rules_then_fall_back():
    p2l, _ = PeriodicConfig(n=9, labels=9, seed=3).generate_sequence()
    real = tuple(p2l.values())
    assert {len(r) for r in real} == {2}
    pool2 = (26**2 - len(real)) * len(p2l)  # same length: containment is equality
    lines = list(itertools.islice(related_rule_lines(p2l, 3), pool2 + 500))
    pairs = []
    for line in lines:
        m = RULE.fullmatch(line)
        assert m, line
        k, label = int(m.group(1)), m.group(2)
        # The same renderer as the real rules, so the form cannot drift.
        assert line == periodic._render_intensional({k: label})
        assert k in p2l and _permitted(label, real), line
        pairs.append((k, label))
    assert len(set(pairs)) == len(pairs), "a (k, label) pair repeated"
    lengths = [len(label) for _, label in pairs]
    assert lengths[:pool2] == [2] * pool2 and set(lengths[pool2:]) == {3}
    assert all(not any(r in lab for r in real) for _, lab in pairs[pool2:])


@pytest.mark.parametrize(
    "rules, match",
    [({}, None), ({2: "ab", 3: "abc"}, "length"), ({2: "aB", 3: "cd"}, None)],
)
def test_stream_rejects_rules_it_cannot_imitate(rules, match):
    with pytest.raises(ValueError, match=match):
        next(related_rule_lines(rules, 0))


def test_a_filler_needs_a_token_target():
    with pytest.raises(ValueError):
        Condition(context=lambda c: c.intensional, filler=related_rule_lines)


def test_review_arm_is_opt_in():
    assert "related_intens" not in CONDITIONS
    assert tuple(CONDITIONS) == ("intens", "extens", "noise_intens", "zero")
    cond = REVIEW_CONDITIONS["related_intens"]
    assert cond.match_tokens_to == "extens" and cond.filler is related_rule_lines
    assert not cond.omit_range


# ------------------------------------------------------------------ rendered prompts


@pytest.mark.parametrize("seed", (0, 5))
def test_rendered_arm_is_token_exact_model_independent_and_keeps_answers(seed):
    cfg = PeriodicConfig(n=7, labels=7, seed=seed)
    p2l, _ = cfg.generate_sequence()
    real = tuple(p2l.values())
    stream = list(itertools.islice(related_rule_lines(p2l, seed), 5000))
    added_by_tok = {}
    for tok in (StubTokenizer(), WordyTokenizer()):
        queries = _queries(cfg, tok)
        expected_answers = [ans for _, ans in numeric_count_query_gen(*cfg.generate_sequence(), seed)]
        assert [q.answer for q in queries] == expected_answers
        added_by_tok[tok.name] = []
        for q in queries:
            related, extens = q.prompts["related_intens"], q.prompts["extens"]
            assert tok.count(related) == tok.count(extens) == q.token_counts["related_intens"]
            assert q.token_counts["related_intens"] == q.token_counts["extens"]
            added, _ws = _split(q.prompts["intens"], related)
            lines = RULE.findall(added)
            assert lines, "the arm must add rule lines"
            assert all(int(k) in p2l and _permitted(lab, real) for k, lab in lines)
            assert len(set(lines)) == len(lines)
            n = len(lines)
            assert added == "".join(stream[:n]), "added lines must be a prefix of the seed's stream"
            added_by_tok[tok.name].append(n)
    # Different tokenizers take different prefixes of one stream.
    assert added_by_tok["stub"] != added_by_tok["wordy"]


def test_longer_label_fallback_in_a_rendered_prompt():
    # One-letter labels: the length-1 pool is (26 - 3) labels x 3 periods = 69 lines, far
    # short of a 1001-line listing, so the stream continues with two-letter labels.
    cfg = PeriodicConfig(n=3, labels=("a", "b", "c"), periods=(7, 11, 13), seed=4)
    tok = StubTokenizer()
    for q in _queries(cfg, tok):
        assert tok.count(q.prompts["related_intens"]) == tok.count(q.prompts["extens"])
        added, _ = _split(q.prompts["intens"], q.prompts["related_intens"])
        labels = [lab for _, lab in RULE.findall(added)]
        assert [len(x) for x in labels[:69]] == [1] * 69
        assert len(labels) > 69 and {len(x) for x in labels[69:]} == {2}
        assert not any(ch in x for x in labels for ch in "abc")


def test_drop_back_reaches_the_exact_count_when_a_one_token_remainder_is_unreachable(monkeypatch):
    calls = {"n": 0, "raised": 0}
    real_pad = periodic.token_matched_noise_prompt

    def counting_pad(*args, **kwargs):
        calls["n"] += 1
        try:
            return real_pad(*args, **kwargs)
        except ValueError:
            calls["raised"] += 1
            raise

    monkeypatch.setattr(periodic, "token_matched_noise_prompt", counting_pad)
    tok = NewlineMergeTokenizer()
    # Under this tokenizer every rule line costs 14 tokens, and for these periods the
    # largest fitting line count leaves exactly one token (found by a scan of configs).
    cfg = PeriodicConfig(n=3, labels=3, seed=0, periods=(4, 5, 7))
    arms = {"intens": CONDITIONS["intens"], "extens": CONDITIONS["extens"], **REVIEW_CONDITIONS}
    for q in _queries(cfg, tok, arms):
        related = q.prompts["related_intens"]
        assert tok.count(related) == tok.count(q.prompts["extens"])
        added, ws = _split(q.prompts["intens"], related)
        assert ws, "after the drop-back the remainder is whitespace"
        # One more stream line would have fitted under the target: the arm dropped back.
        p2l, _ = cfg.generate_sequence()
        n = len(RULE.findall(added))
        nxt = next(itertools.islice(related_rule_lines(p2l, 0), n, None))
        longer = related.replace(added + ws, added + nxt, 1)
        assert tok.count(longer) <= tok.count(q.prompts["extens"])
    assert calls["raised"] > 0, "the case must exercise an unreachable remainder"


# ------------------------------------------------------------------ existing arms unchanged

#: sha256 over (prompt, NUL, repr(answer), NUL) of each arm's 9 questions, computed by
#: running HEAD c2ce6a6c (before the review arm existed) from a ``git archive`` copy with
#: ``run_study.make_quizzes(seed, "deepseek-v3.1")`` and the offline ``StubTokenizer``.
HEAD_PINS = {
    (0, "intens"): "cd2e591868fd53b3007d38b18d602d154df854f267e484f66e1d354322b8146a",
    (0, "extens"): "022295b01cfad23488c4f5994f43e0f47045a182286c7a14c8984e73b69f6421",
    (0, "noise_intens"): "293a5b55f037d20abcc5804f1e853c8a9ff926e9a00ae9172b4946a4f7a2dbf5",
    (0, "zero"): "cfce4214e9e2c06a158d955955e0a8f76a20e44ec0f08f0e040edc4b8088f38b",
    (1, "intens"): "01560a61d6e4664c0ac015860130851e994fbe107ed6a9a06d4d03c3e3f33a53",
    (1, "extens"): "7f39a2e12fce5a889c64c0c4aaf0e2edea1ce23541aa0ae3683ff0ec03f50941",
    (1, "noise_intens"): "391085cdbdd7cc0161243ba0a0e6086566bd3e896a433076f27340d80fae6c18",
    (1, "zero"): "b83ef5415ce792f95b84d4f66b52c2ae7de7abfbd9e144589f3282ec5e1fe1de",
    (2, "intens"): "4f25c78963a04b62f5aa14c11c07d1a16538bb738a72471bc708572c41387417",
    (2, "extens"): "398ddcc5e9eef495c8314a6b9bb8cb581176819822f50ff9c601f4f05b26712d",
    (2, "noise_intens"): "5d79b44b8bbc8beef2610db02d52626574d291cb45116b77fc0f1bac8e8b5be9",
    (2, "zero"): "91803a1fc505d28abe24f888157b07c1366b5d91417c0a289f6df0c9dd58a14d",
    (29, "intens"): "57cfc336762461b85adca0b07b3d5c15e20dbec5397242253a56664e9157238f",
    (29, "extens"): "4fd438c33dc1b23ebee40f4ba7e8f1def5071fc53f1760b0a8622b508721c064",
    (29, "noise_intens"): "a370f726fe69e6245b10eea4778e3170548b071455d937b67aa80cb02a12ebfe",
    (29, "zero"): "7fd3e14b21a40af1f63530927250083c1c38b79f3300a4f6e81ba167fe6ee4cf",
}
#: ``run_study.completion_budget(model, range(0, 30))`` at HEAD under ``StubTokenizer``.
HEAD_BUDGET = 99741


def _arm_hash(quiz) -> str:
    h = hashlib.sha256()
    for q in quiz:
        h.update(q.prompt.encode() + b"\0" + repr(q.answer).encode() + b"\0")
    return h.hexdigest()


@pytest.fixture(scope="module")
def run_study():
    module, exc, _env = import_run_study("run_study_for_related_intens")
    assert exc is None, exc
    module.for_model = lambda _model: StubTokenizer()
    return module


@pytest.mark.parametrize("seed", (0, 1, 2, 29))
def test_existing_arms_are_byte_identical_to_head(run_study, seed):
    default = run_study.make_quizzes(seed, "deepseek-v3.1")
    assert tuple(default) == ("intens", "extens", "noise_intens", "zero")
    merged = run_study.make_quizzes(
        seed, "deepseek-v3.1", conditions={**run_study.CONDITIONS, **REVIEW_CONDITIONS}
    )
    assert tuple(merged) == ("intens", "extens", "noise_intens", "zero", "related_intens")
    for arm in ("intens", "extens", "noise_intens", "zero"):
        assert _arm_hash(default[arm]) == HEAD_PINS[(seed, arm)], arm
        # Opting into the review arm leaves the other arms untouched.
        assert _arm_hash(merged[arm]) == HEAD_PINS[(seed, arm)], arm
    assert [q.answer for q in merged["related_intens"]] == [q.answer for q in merged["intens"]]


def test_driver_defaults_and_budget_are_unchanged(run_study):
    assert run_study.INFO_TYPES == ("intens", "extens", "noise_intens", "zero")
    assert tuple(run_study.EXPERIMENT.info_types) == run_study.INFO_TYPES
    assert run_study.completion_budget("deepseek-v3.1", range(0, 30)) == HEAD_BUDGET
