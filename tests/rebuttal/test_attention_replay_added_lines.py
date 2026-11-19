"""Labelling the added lines of a deduction (Horn) prompt as class 1, offline.

The padded arms (``pad``, ``tjunk``, ``both``, ...) show the ``lem`` arm's lemma lines in the
same positions plus one line per derivation-tree slot. With ``label_added_lines`` those
added lines are class 1, so the pad ratio exists for deduction. These tests check the
multi-span ``token_classes``, the line locator on the real rendered rungs in
``rebuttal/rungs`` (deterministic files in the repository), the token classes on those
prompts (stub tokenizers, and the real cached tokenizers where present), the plan, the
manifests, the refusals, the command-line flag and the reader's mass and ratio outputs.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

from smolbench.deduction.horn import render as horn_render
from smolbench.deduction.horn.theory import Theory, generate
from smolbench.evals import attention, attention_analysis
from tests._paths import REPO_ROOT, load_by_path
from tests.evals.test_attention import FakeS3
from tests.evals.test_attention_analysis import capture_npz, synthetic_capture

ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_added_lines_under_test")
horn_tests = load_by_path(
    REPO_ROOT / "tests" / "rebuttal" / "test_attention_replay_horn.py", "attention_replay_horn_tests_for_added_lines"
)

GEMMA, NEMO, DSV31 = "gemma-4-31b", "nemotron-3-super-120b-a12b", "deepseek-v3.1"
RUNGS = REPO_ROOT / "rebuttal" / "rungs"
S3_URI = "s3://bucket/bedrock-trio/attention-v3"
CONFIG = {"num_hidden_layers": 2, "num_attention_heads": 4}
ARMS = ("lem", "pad", "tjunk", "both")
CELLS = [("m64", 100), ("m64", 101), ("m20", 100)]


def template():
    return ar.ChatTemplate(horn_tests.SYS_TEMPLATE, bos_token="<bos>")


class WordTokenizer(horn_tests.CharTokenizer):
    """Specials as one token; a word glued to the newline BEFORE it; every other character alone.

    The ``\\n<word>`` tokens straddle line edges, which exercises the straddle rule.
    """

    def __init__(self):
        super().__init__()
        self._re = re.compile(
            "|".join(re.escape(s) for s in self.specials) + r"|\n?[^\s<]+|.", re.S
        )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _cell_text(rungs: Path, rung: str, seed: int, arm: str):
    d = rungs / rung / f"s{seed:04d}" / arm
    return d / "prompt.md", (d / "prompt.md").read_text(encoding="utf-8"), (d / "system.md").read_text(encoding="utf-8")


def _row(rungs, rung, seed, arm, rep=0, model=GEMMA, content="derive b(x) from a(x)"):
    path = rungs / rung / f"s{seed:04d}" / arm / "prompt.md"
    return {"spec_key": model, "rung": rung, "arm": arm, "seed": seed, "rep": rep,
            "prompt_sha256": _sha(path.read_bytes()), "provider_system_prompt": False,
            "ts": "2026-11-16T07:00:00Z", "verdict": "success", "finish_reason": "stop",
            "content": content, "reasoning": "Chain the lemmas.", "completion_tokens": 9, "prompt_tokens": 50}


def _rows_file(path: Path, rows) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


class _QuarterTokens:
    """The renderer's token counter, without tiktoken: ``len // 4``."""

    def count(self, s: str) -> int:
        return len(s) // 4


def _tiny_rung(root: Path, seeds=(7, 8), arms=ARMS, rung="m3") -> Path:
    """A rendered rung of small theories (chain length 3), laid out like ``rebuttal/rungs``."""
    for seed in seeds:
        theory = generate(seed, m=3, n_extra=1)
        seed_dir = root / rung / f"s{seed:04d}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        (seed_dir / "theory.json").write_text(theory.to_json(), encoding="utf-8")
        for arm in arms:
            rendered = horn_render.render(theory, arm, tok=_QuarterTokens())
            (seed_dir / arm).mkdir(exist_ok=True)
            (seed_dir / arm / "prompt.md").write_text(rendered.prompt, encoding="utf-8")
            (seed_dir / arm / "system.md").write_text(rendered.system, encoding="utf-8")
    return root


def _tiny(tmp_path: Path, seeds=(7, 8), arms=ARMS):
    rungs = _tiny_rung(tmp_path / "rungs", seeds, arms)
    rows = [_row(rungs, "m3", s, a) for s in seeds for a in arms]
    return rungs, _rows_file(tmp_path / "horn" / f"{GEMMA}.jsonl", rows)


def _build(rungs, rows_path, tok=None, **kw):
    return ar.build_jobs(GEMMA, Path("unused"), "bedrock-trio/attention-v3", tokenizer=tok or horn_tests.CharTokenizer(),
                         template=template(), study="horn", horn_rows=rows_path, rungs_dir=rungs, **kw)


def _plan(rungs, rows_path, **kw):
    tok = horn_tests.CharTokenizer()
    return ar.plan_replay(models=[GEMMA], study="horn", horn_rows=rows_path, rungs_dir=rungs, s3_uri=S3_URI,
                          tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                          config_for=lambda m: CONFIG, **kw)[GEMMA]


# ------------------------------------------------------------------ token_classes with several spans

def _decode(pieces):
    return lambda ids: [pieces[i] for i in ids]


def test_pad_spans_label_the_union_and_leave_straddlers_out() -> None:
    pieces = ["a\n", "pa", "d\n", "b", "\nq", "q\n", "  ", "c\n"]   # text "a\npad\nb\nqq\n  c\n"
    # Spans: "pad\n" (2, 6), "\nqq\n" in two touching halves (7, 9) and (9, 12), and "  " (12, 14).
    classes = attention.token_classes(range(8), [0, 0], _decode(pieces), pad_spans=[(12, 14), (2, 6), (9, 12), (7, 9)])
    # "pa" and "d\n" lie inside (2, 6); "\nq" crosses the touching edge of two spans, inside the
    # union; "  " is whitespace inside a span (class 1); "b" and "c\n" are outside.
    assert classes == [0, 1, 1, 0, 1, 1, 1, 0, 3, 3]
    # A token that crosses from a span into text outside every span is not class 1.
    assert attention.token_classes(range(3), [], _decode(["ab", "cd", "ef"]), pad_spans=[(0, 3)]) == [1, 0, 0]
    # An empty sequence labels nothing: the same classes as the empty single span.
    plain = attention.token_classes(range(8), [0], _decode(pieces), pad_span=(0, 0))
    assert attention.token_classes(range(8), [0], _decode(pieces), pad_spans=[]) == plain
    assert 1 not in plain


def test_one_span_in_pad_spans_equals_pad_span_and_the_single_span_path_is_unchanged() -> None:
    rng = np.random.default_rng(3)
    alphabet = ["a", "bc", " ", "  \n", "\n", "", "x y", "\t"]
    for _ in range(200):
        pieces = [alphabet[i] for i in rng.integers(0, len(alphabet), rng.integers(1, 12))]
        n = sum(map(len, pieces))
        lo = int(rng.integers(0, n + 1))
        hi = int(rng.integers(lo, n + 1))
        single = attention.token_classes(range(len(pieces)), [0], _decode(pieces), pad_span=(lo, hi))
        assert attention.token_classes(range(len(pieces)), [0], _decode(pieces), pad_spans=[(lo, hi)]) == single
    # The documented single-span and by-rule results stay as they were.
    table = {0: "", 1: "Hi", 2: ".", 3: " " * 40, 9: " ok"}
    assert attention.token_classes([0, 1, 2, 3], [9], lambda ids: [table[i] for i in ids]) == [2, 0, 0, 1, 3]
    pieces = {1: "ab", 2: " ", 3: "cd"}
    assert attention.token_classes([1, 2, 3], [], lambda ids: [pieces[i] for i in ids], pad_span=(2, 3)) == [0, 1, 0]


def test_pad_spans_refuse_bad_spans_and_the_two_keywords_together() -> None:
    with pytest.raises(ValueError, match="not both"):
        attention.token_classes([0], [], _decode(["ab"]), pad_span=(0, 1), pad_spans=[(0, 1)])
    with pytest.raises(ValueError, match="pad_spans element"):
        attention.token_classes([0], [], _decode(["ab"]), pad_spans=[(0, 1), (1, 3)])
    with pytest.raises(ValueError, match="pad_spans element"):
        attention.token_classes([0], [], _decode(["ab"]), pad_spans=[(2, 1)])


class SplitConjunctionTokenizer(horn_tests.CharTokenizer):
    """One token per character, except that `` ∧`` becomes two tokens with OVERLAPPING offsets.

    As a byte-level tokenizer splits U+2227: ``(i, i + 2)`` then ``(i + 1, i + 2)``.
    """

    def encode_offsets(self, text):
        out = []
        for start, end in super().encode_offsets(text):
            if text[start:end] == "∧" and out and out[-1] == (start - 1, start) and text[start - 1] == " ":
                out[-1] = (start - 1, end)
                out.append((start, end))
            else:
                out.append((start, end))
        return out

    def encode_ids(self, text):
        return [self.vocab.setdefault(text[s:e], len(self.vocab)) for s, e in self.encode_offsets(text)]


def test_overlapping_offsets_inside_the_pad_ranges_are_labelled() -> None:
    query = "Facts\nlem(x) ∧ a(x)\nadd(x) ∧ b(x)\nlem2(x)\nadd2 ∧ c\nGoal\n"
    lines = query.split("\n")
    starts = [sum(len(x) + 1 for x in lines[:i]) for i in range(len(lines))]
    spans = [(starts[i], starts[i] + len(lines[i]) + 1) for i in (2, 4)]
    tok = SplitConjunctionTokenizer()
    # The single-span mapping needs the query's tokens to tile it, which these do not.
    with pytest.raises(ValueError, match="not adjacent"):
        ar.rebuild_sequence(query, "r", "x", tokenizer=tok, template=template(), fmt=ar.REASONING_FORMATS[GEMMA],
                            system="S", pad_query_span=spans[0])
    r = ar.rebuild_sequence(query, "r", "x", tokenizer=tok, template=template(), fmt=ar.REASONING_FORMATS[GEMMA],
                            system="S", pad_query_spans=spans)
    _assert_classes_follow_the_lines(r, tok, query, spans)
    # Still one token per added character (" \u2227" and "\u2227" replace " " and "\u2227"), and
    # both overlapping tokens of each added line's conjunction are class 1.
    assert r.classes[: len(r.prompt_ids)].count(1) == sum(hi - lo for lo, hi in spans)
    split = [i for i, (a, b) in enumerate(zip(tok.encode_offsets(r.prompt_text), tok.encode_offsets(r.prompt_text)[1:]))
             if a[1] > b[0]]
    assert len(split) == 3 and [r.classes[i] for i in split] == [0, 1, 1]   # the lemma line's is not


# ------------------------------------------------------------------ the line locator on the real rungs

@pytest.mark.parametrize("rung,seed", CELLS)
def test_the_added_lines_are_the_tree_slots_and_the_same_in_every_padded_arm(rung, seed) -> None:
    cache: dict = {}
    found = {}
    for arm in ARMS + ("rep", "marked-lemma"):
        _path, query, _system = _cell_text(RUNGS, rung, seed, arm)
        spans = ar._horn_added_line_spans(RUNGS, rung, seed, arm, query, cache)
        lines = query.split("\n")
        head = lines.index("## Library")
        starts = [sum(len(x) + 1 for x in lines[:i]) for i in range(len(lines))]
        positions = []                     # 1-based position of each added line in the library
        for lo, hi in spans:
            i = starts.index(lo)
            # One whole line plus its own newline.
            assert hi == lo + len(lines[i]) + 1 and query[hi - 1] == "\n"
            positions.append(i - head)
        n_library = lines.index("", head) - head - 1
        found[arm] = (positions, lines[head + 1: head + 1 + n_library])
    lem_positions, lem_library = found["lem"]
    assert lem_positions == []                                                 # lem has no added line
    for arm in ("pad", "tjunk", "both", "rep", "marked-lemma"):
        positions, library = found[arm]
        assert positions == found["pad"][0]                                    # one set for every padded arm
        assert len(library) == len(lem_library) + len(positions)              # the extra lines, nothing else
        tag = horn_render.LEMMA_TAG if arm == "marked-lemma" else ""
        kept = [line for pos, line in enumerate(library, 1) if pos not in set(positions)]
        assert [line[len(tag):] for line in kept] == lem_library               # lemma lines are never added
    if (rung, seed) == ("m64", 100):
        assert len(found["pad"][0]) == 1614 - 462 == 1152
    # The pad arm's added lines are exactly its lorem-ipsum lines; both's are the real tree rules.
    lorem = set(horn_render._LOREM)
    positions, library = found["pad"]
    for pos, line in enumerate(library, 1):
        assert (pos in set(positions)) == all(w in lorem for w in line.split()), line
    theory = Theory.from_json((RUNGS / rung / f"s{seed:04d}" / "theory.json").read_text(encoding="utf-8"))
    tree_texts = {theory.rules[k].text() for k in theory.tree_keys()}
    _positions, library = found["both"]
    assert {library[pos - 1] for pos in positions} <= tree_texts


def test_cells_whose_added_lines_cannot_be_located_are_refused(tmp_path: Path) -> None:
    rungs = _tiny_rung(tmp_path / "rungs", seeds=(7,))
    cache: dict = {}
    query = (rungs / "m3" / "s0007" / "pad" / "prompt.md").read_text(encoding="utf-8")
    assert len(ar._horn_added_line_spans(rungs, "m3", 7, "pad", query, cache)) > 0
    # A prompt with one line more or less than the theory shows.
    with pytest.raises(ar._HornRowError, match="disagree"):
        ar._horn_added_line_spans(rungs, "m3", 7, "pad", query.replace("## Library\n", "## Library\nextra\n"), {})
    # A lemma line that differs from the lem arm's line in the same position.
    added = {lo for lo, _hi in ar._horn_added_line_spans(rungs, "m3", 7, "pad", query, {})}
    lines = query.split("\n")
    head = lines.index("## Library")
    starts = [sum(len(x) + 1 for x in lines[:i]) for i in range(len(lines))]
    first_lemma = next(i for i in range(head + 1, len(lines)) if starts[i] not in added)
    lines[first_lemma] = "zzz(x) \u2192 yyy(x)"
    with pytest.raises(ar._HornRowError, match="lemma lines"):
        ar._horn_added_line_spans(rungs, "m3", 7, "pad", "\n".join(lines), {})
    # Missing theory.json or lem prompt.
    (rungs / "m3" / "s0007" / "theory.json").unlink()
    with pytest.raises(ar._HornRowError, match="theory.json not found"):
        ar._horn_added_line_spans(rungs, "m3", 7, "pad", query, {})
    with pytest.raises(ar._HornRowError, match="arm 'nope'"):
        ar._horn_added_line_spans(RUNGS, "m20", 100, "nope", query, {})


# ------------------------------------------------------------------ token classes on the real prompts

def _assert_classes_follow_the_lines(rebuilt, tok, query, spans, default=None):
    """Check the class-1 rule against the prompt text, independently of the mapping code."""
    text = rebuilt.prompt_text
    # A template may strip the query (the stub and the real templates trim it); the ranges then
    # shift by the stripped leading characters and are clipped to the text that remains.
    located = query if query in text else query.strip()
    assert text.count(located) == 1
    lead = 0 if located == query else len(query) - len(query.lstrip())
    q0 = text.index(located)
    clip = lambda x: q0 + min(max(x - lead, 0), len(located))  # noqa: E731
    union = sorted((clip(lo), clip(hi)) for lo, hi in spans)
    offsets = tok.encode_offsets(text)
    n_prompt = len(rebuilt.prompt_ids)
    assert len(offsets) == n_prompt
    # A character mask of the added text: a token lies inside the added lines when every one of
    # its characters is added (straightforward, and independent of the code under test).
    added = np.zeros(len(text) + 1, dtype=bool)
    for lo, hi in union:
        added[lo:hi] = True
    inside_line = [e > s and bool(added[s:e].all()) for s, e in offsets]
    classes = rebuilt.classes
    for i, (s, e) in enumerate(offsets):
        member = inside_line[i] and s >= q0 and e <= q0 + len(located)
        assert (classes[i] == 1) == member, (i, text[s:e], classes[i])
        if classes[i] == 1:
            # Never a character of a lemma line, a heading or any other non-added text.
            assert added[s:e].all()
    assert set(classes[n_prompt:]) <= {3}
    if default is not None:
        assert default.prompt_ids == rebuilt.prompt_ids and default.completion_ids == rebuilt.completion_ids
        assert 1 not in default.classes
        # Every token that is not class 1 keeps the class it has without the labels.
        assert all(d == c for d, c in zip(default.classes, classes) if c != 1)
    return sum(1 for c in classes[:n_prompt] if c == 1)


@pytest.mark.parametrize("rung,seed,tok_class", [
    *((rung, seed, horn_tests.CharTokenizer) for rung, seed in CELLS),
    ("m64", 100, WordTokenizer),                      # the straddling tokenizer, on one cell
])
def test_the_real_prompts_label_exactly_the_added_lines(rung, seed, tok_class) -> None:
    fmt = ar.REASONING_FORMATS[GEMMA]
    counts = {}
    for arm in ARMS:
        tok = tok_class()
        _path, query, system = _cell_text(RUNGS, rung, seed, arm)
        spans = ar._horn_added_line_spans(RUNGS, rung, seed, arm, query, {})
        default = ar.rebuild_sequence(query, "r", "derive x", tokenizer=tok, template=template(), fmt=fmt,
                                      system=system, pad_query_span=(0, 0))
        labelled = ar.rebuild_sequence(query, "r", "derive x", tokenizer=tok, template=template(), fmt=fmt,
                                       system=system, pad_query_spans=spans)
        counts[arm] = _assert_classes_follow_the_lines(labelled, tok, query, spans, default)
        straddling = int(re.search(r"(\d+) straddle", labelled.notes[-1]).group(1))
        if tok_class is WordTokenizer and arm != "lem":
            # "\n<word>" tokens cross from a lemma line into an added one and back: not class 1.
            assert straddling > 0
        if tok_class is horn_tests.CharTokenizer:
            assert straddling == 0
            # One token per character: every added character (newline included) is class 1,
            # the spaces inside an added line too.
            assert counts[arm] == sum(hi - lo for lo, hi in spans)
            space = tok.vocab.get(" ")
            assert arm == "lem" or any(c == 1 and t == space for c, t in zip(labelled.classes, labelled.prompt_ids))
    assert counts["lem"] == 0 and all(counts[a] > 0 for a in ("pad", "tjunk", "both"))


def _cached_tokenizer(model):
    return horn_tests._cached_tokenizer(model)


@pytest.mark.parametrize("model", [NEMO, DSV31, GEMMA])
def test_the_real_tokenizers_label_exactly_the_added_lines(model, monkeypatch) -> None:
    """The real byte-level tokenizers split U+2227 with overlapping offsets; the labels must hold."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    tok = _cached_tokenizer(model)
    try:
        real = ar.load_chat_template(model, local_files_only=True)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"{model} chat template not cached: {type(exc).__name__}")
    fmt = ar.REASONING_FORMATS[model]
    counts = {}
    for arm in ARMS:
        _path, query, system = _cell_text(RUNGS, "m64", 100, arm)
        spans = ar._horn_added_line_spans(RUNGS, "m64", 100, arm, query, {})
        default = ar.rebuild_sequence(query, "r", "derive x", tokenizer=tok, template=real, fmt=fmt,
                                      system=system, pad_query_span=(0, 0))
        labelled = ar.rebuild_sequence(query, "r", "derive x", tokenizer=tok, template=real, fmt=fmt,
                                       system=system, pad_query_spans=spans)
        counts[arm] = _assert_classes_follow_the_lines(labelled, tok, query, spans, default)
    assert counts["lem"] == 0 and min(counts["pad"], counts["tjunk"], counts["both"]) > 0
    # The renamed tree rules are token-matched to the real ones, so the two counts are close.
    assert abs(counts["tjunk"] - counts["both"]) <= 0.02 * counts["both"]


# ------------------------------------------------------------------ build and plan

def _real_rows(tmp_path: Path, cells=CELLS[:2], arms=ARMS) -> Path:
    rows = [_row(RUNGS, rung, seed, arm) for rung, seed in cells for arm in arms]
    return _rows_file(tmp_path / "horn" / f"{GEMMA}.jsonl", rows)


def test_the_default_keeps_the_horn_classes_and_the_labels_change_only_the_added_lines(tmp_path: Path) -> None:
    rows = _real_rows(tmp_path)
    default, errors = _build(RUNGS, rows)
    assert errors == []
    labelled, errors = _build(RUNGS, rows, label_added_lines=True)
    assert errors == [] and [p.job.job_id for p in default] == [p.job.job_id for p in labelled]
    tok = horn_tests.CharTokenizer()
    for d, item in zip(default, labelled):
        # The default is the rebuild with the empty pad span, as before the option existed.
        _path, query, system = _cell_text(RUNGS, item.run.rung, item.seed, item.run.arm)
        before = ar.rebuild_sequence(query, "Chain the lemmas.", "derive b(x) from a(x)", tokenizer=tok,
                                     template=template(), fmt=ar.REASONING_FORMATS[GEMMA], system=system,
                                     pad_query_span=(0, 0))
        assert d.job.classes == before.classes and 1 not in d.job.classes
        assert d.job.key == item.job.key and d.job.prompt_token_ids == item.job.prompt_token_ids
        changed = [i for i, (a, b) in enumerate(zip(d.job.classes, item.job.classes)) if a != b]
        assert all(item.job.classes[i] == 1 for i in changed)
        n1 = item.job.classes.count(1)
        assert (n1 == 0) == (item.run.arm == "lem")
        assert any("pad ranges by construction" in note for note in item.notes)


def test_the_plan_reports_the_labels_and_the_class1_tokens_per_arm(tmp_path: Path) -> None:
    rows = _real_rows(tmp_path)
    plain = _plan(RUNGS, rows)
    assert plain.label_added_lines is False and "label_added_lines" not in plain.summary()
    assert not any("class1_tokens" in stats for stats in plain.per_arm.values())
    plan = _plan(RUNGS, rows, label_added_lines=True)
    assert plan.label_added_lines is True and plan.errors == [] and plan.jobs == 8
    stats = plan.per_arm
    assert stats["lem"]["class1_tokens"] == 0
    assert all(stats[a]["class1_tokens"] > 0 for a in ("pad", "tjunk", "both"))
    assert stats["pad"]["class1_tokens_mean"] == stats["pad"]["class1_tokens"] / 2
    text = plan.summary()
    assert "label_added_lines: the added lines of every padded arm are class 1" in text
    assert f"class-1 tokens {stats['tjunk']['class1_tokens']} total" in text
    # Everything but the labels is the same plan.
    assert plan.total_tokens == plain.total_tokens and plan.est_capture_bytes == plain.est_capture_bytes


def test_cells_without_locatable_lines_or_without_class1_tokens_are_plan_errors(tmp_path: Path, monkeypatch) -> None:
    rungs, rows = _tiny(tmp_path)
    plan = _plan(rungs, rows, label_added_lines=True)
    assert plan.errors == [] and plan.jobs == 8
    (rungs / "m3" / "s0008" / "theory.json").unlink()
    plan = _plan(rungs, rows, label_added_lines=True)
    assert plan.jobs == 4 and len(plan.errors) == 4
    assert all("s0008" in e or "seed 8" in e for e in plan.errors) and all("theory.json" in e for e in plan.errors)
    assert plan.per_arm["pad"]["errors"] == 1
    # The default plan does not read theory.json at all.
    assert _plan(rungs, rows).errors == []
    # A padded arm whose added lines label no token is refused, never planned unlabelled.
    real = ar._horn_added_line_spans
    monkeypatch.setattr(ar, "_horn_added_line_spans",
                        lambda rungs_dir, rung, seed, arm, query, cache:
                        [] if arm == "pad" else real(rungs_dir, rung, seed, arm, query, cache))
    plan = _plan(rungs, rows, label_added_lines=True, seeds=[7])
    assert plan.jobs == 3 and len(plan.errors) == 1 and "no class-1 token" in plan.errors[0]


def test_the_labels_are_accepted_for_the_induction_study_and_must_be_bools(tmp_path: Path) -> None:
    """The flag labels the extens listing for induction (``test_attention_replay_extens_labels``)."""
    plan = ar.plan_replay(tmp_path, [GEMMA], s3_uri=S3_URI, label_added_lines=True)[GEMMA]
    assert plan.label_added_lines is True and plan.jobs == 0 and plan.errors == []
    assert ar.build_jobs(GEMMA, tmp_path, "p", label_added_lines=True) == ([], [])
    for name in ("label_added_lines", "label_answer_tokens"):
        with pytest.raises(ValueError, match="must be a bool"):
            ar.plan_replay(tmp_path, [GEMMA], s3_uri=S3_URI, study="horn", horn_rows=tmp_path / "x.jsonl",
                           **{name: "yes"})
        with pytest.raises(ValueError, match="must be a bool"):
            ar.plan_replay(tmp_path, [GEMMA], s3_uri=S3_URI, **{name: 1})


# ------------------------------------------------------------------ replay, audit and manifests

def _replay(tmp_path, rungs, rows_path, box, s3, monkeypatch, **kw):
    from smolbench.evals.providers import ec2 as real_ec2

    monkeypatch.setattr(ar, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(real_ec2, "derive_tp", lambda *a, **k: box.tp)
    tok = horn_tests.CharTokenizer()
    return ar.replay_model(
        GEMMA, Path("unused"), S3_URI, approved=True, study="horn", horn_rows=rows_path, rungs_dir=rungs,
        tokenizer_for=lambda m: tok, template_for=lambda m: template(), config_for=lambda m: CONFIG,
        ec2=box, s3_client_factory=lambda: s3, poll_s=0, batch_timeout_s=10, url_ttl_s=99, **kw)


def test_every_manifest_of_a_labelled_run_records_the_flag(tmp_path: Path, monkeypatch) -> None:
    rungs, rows = _tiny(tmp_path, seeds=(7,), arms=("lem", "pad"))
    s3 = FakeS3()
    box = horn_tests.HornBox(s3)
    report = _replay(tmp_path, rungs, rows, box, s3, monkeypatch, label_added_lines=True)
    assert len(report.verified) == 2 and len(report.manifests) == 2 and report.plan.label_added_lines
    sent = {line["job_id"]: line["classes"] for b in box.batches for line in b["jobs"]}
    assert 1 not in sent["horn.m3.lem.s7.rep0"] and 1 in sent["horn.m3.pad.s7.rep0"]
    for key in report.manifests:
        assert json.loads(s3.objects[key])["label_added_lines"] is True
    # The default run under another prefix writes no such key.
    s3b = FakeS3()
    plain = _replay(tmp_path, rungs, rows, horn_tests.HornBox(s3b), s3b, monkeypatch)
    assert plain.manifests and all("label_added_lines" not in json.loads(s3b.objects[k]) for k in plain.manifests)
    # The post-hoc audit of the labelled captures: the stored classes match the labelled plan,
    # and its manifests carry the flag too.
    for key in [k for k in s3.objects if "manifest--" in k]:
        del s3.objects[key]
    tok = horn_tests.CharTokenizer()
    audit = ar.audit_existing(GEMMA, Path("unused"), S3_URI, study="horn", horn_rows=rows, rungs_dir=rungs,
                              tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                              config_for=lambda m: CONFIG, s3_client_factory=lambda: s3, label_added_lines=True)
    assert len(audit.verified) == 2 and not audit.audit_failures
    assert all(json.loads(s3.objects[k])["label_added_lines"] is True for k in audit.manifests)
    # Audited against the default classes, the labelled pad capture does not match.
    for key in [k for k in s3.objects if "manifest--" in k]:
        del s3.objects[key]
    mismatch = ar.audit_existing(GEMMA, Path("unused"), S3_URI, study="horn", horn_rows=rows, rungs_dir=rungs,
                                 tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                                 config_for=lambda m: CONFIG, s3_client_factory=lambda: s3)
    assert list(mismatch.audit_failures) == ["horn.m3.pad.s7.rep0"]


# ------------------------------------------------------------------ command line

@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setitem(sys.modules, "attention_replay", ar)
    return load_by_path(REPO_ROOT / "rebuttal" / "run_attention.py", "run_attention_added_lines", snapshot_env=True)


def test_the_cli_flag_reaches_the_plan_for_both_studies(cli, tmp_path, monkeypatch, capsys) -> None:
    rows = _real_rows(tmp_path, cells=CELLS[:1])
    seen: dict = {}
    real_plan = ar.plan_replay
    tok = horn_tests.CharTokenizer()

    def plan(results_root, models, **kw):
        seen.update(kw)
        return real_plan(results_root, models, tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                         config_for=lambda m: CONFIG, **kw)

    monkeypatch.setattr(cli.ar, "plan_replay", plan)
    monkeypatch.setattr(cli.ar, "replay_model", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    base = ["--model", GEMMA, "--study", "horn", "--results-root", str(tmp_path / "results" / "induction"),
            "--rows", str(rows), "--rungs-dir", str(RUNGS), "--s3-uri", S3_URI]
    assert cli.main(base + ["--label-added-lines"]) == 0
    out = capsys.readouterr().out
    assert seen["label_added_lines"] is True
    assert "label_added_lines: the added lines" in out and "class-1 tokens 0 total" in out
    assert "arm pad: 1 jobs" in out and "plan only" in out
    seen.clear()
    assert cli.main(base) == 0
    assert "label_added_lines" not in seen and "class-1 tokens" not in capsys.readouterr().out
    # Induction: the flag is valid and reaches the plan (the extens listing becomes class 1).
    seen.clear()
    assert cli.main(["--model", GEMMA, "--results-root", str(tmp_path / "results" / "induction"),
                     "--s3-uri", S3_URI, "--label-added-lines", "--label-answer-tokens"]) == 0
    assert seen["label_added_lines"] is True and seen["label_answer_tokens"] is True
    assert "study" not in seen


# ------------------------------------------------------------------ reader

def _write_horn_capture(mirror: Path, arm: str, seed: int, cap: dict, kind: str, *, drop=()) -> None:
    arm_dir = mirror / "deduction" / "horn" / GEMMA / "m20" / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    for rank in range(2):
        (arm_dir / f"s{seed}.rep0.r{rank}.npz").write_bytes(capture_npz(cap, rank, 2, kind, drop=drop))
    manifest = arm_dir / "manifest--x.json"
    jobs = json.loads(manifest.read_text())["jobs"] if manifest.exists() else []
    jobs.append({"job_id": ar._horn_job_id("m20", arm, seed, 0), "status": "verified"})
    manifest.write_text(json.dumps({"jobs": jobs}))


def _expected_job(cap: dict, kind: str):
    """Mass by class over all and global layers, and the pooled pad ratios, from the capture's own arrays."""
    window = cap["sliding_window"]
    if kind == "mass":
        per_layer = cap["mass"].astype(np.float64).mean(axis=(1, 2))                 # [L, 4]
        ratio = attention_analysis.whitespace_ratio(cap["mass"].astype(np.float32), cap["classes"], cap["query_start"])
        sums = np.where(np.isnan(ratio), 0.0, ratio).sum(axis=1, dtype=np.float64)
        counts = (~np.isnan(ratio)).sum(axis=1)
    else:
        s = cap["summary"]
        per_layer = (np.asarray(s["sum_mass"], np.float64) / s["rows"]).mean(axis=1)
        sums, counts = np.asarray(s["sum_pad_ratio"], np.float64), np.asarray(s["n_pad_ratio"])
    glob = window == 0
    return (per_layer.mean(0), per_layer[glob].mean(0),
            sums.sum() / counts.sum(), sums[glob].sum() / counts[glob].sum())


def test_the_reader_reports_mass_by_class_and_per_job_ratios_for_horn_arms(tmp_path: Path) -> None:
    mirror = tmp_path / "mirror"
    # Two pad jobs with class-1 tokens (one mass, one summary capture) and one lem job without.
    caps = {("pad", 100, "mass"): synthetic_capture(11), ("pad", 101, "summary"): synthetic_capture(12),
            ("lem", 100, "summary"): synthetic_capture(13, pad=None)}
    for (arm, seed, kind), cap in caps.items():
        _write_horn_capture(mirror, arm, seed, cap, kind)
    out = ar.read_captures(GEMMA, mirror, study="horn", config=CONFIG)
    pad, lem = out["pad"], out["lem"]
    assert pad["job_labels"][0].endswith("/pad/s100.rep0") and pad["job_labels"][1].endswith("/pad/s101.rep0")
    expected = [_expected_job(caps[("pad", 100, "mass")], "mass"), _expected_job(caps[("pad", 101, "summary")], "summary")]
    np.testing.assert_allclose(pad["mass_mean"], np.mean([e[0] for e in expected], axis=0), rtol=1e-12)
    np.testing.assert_allclose(pad["mass_global_mean"], np.mean([e[1] for e in expected], axis=0), rtol=1e-12)
    np.testing.assert_allclose(pad["ratio_per_job"], [e[2] for e in expected], rtol=1e-6)
    np.testing.assert_allclose(pad["ratio_global_per_job"], [e[3] for e in expected], rtol=1e-6)
    assert pad["mass_mean"].shape == (4,) and pad["mass_mean"].sum() <= 1 + 1e-6     # the sink takes the rest
    # The pad statistics the reader already had come out for a horn arm with class-1 tokens.
    assert np.isfinite(pad["ratio_mean"]) and pad["pad_tokens_mean"] == 6
    # An arm without class-1 tokens: zero pad mass, undefined ratios.
    assert lem["mass_mean"][1] == 0 and np.isnan(lem["ratio_mean"]) and np.isnan(lem["ratio_per_job"][0])
    assert lem["pad_tokens_mean"] == 0


def test_without_a_sliding_window_array_the_global_mass_is_the_mass(tmp_path: Path) -> None:
    mirror = tmp_path / "mirror"
    for seed, kind in ((100, "mass"), (101, "summary")):
        _write_horn_capture(mirror, "pad", seed, synthetic_capture(20 + seed), kind, drop=("sliding_window",))
    pad = ar.read_captures(GEMMA, mirror, study="horn", config=CONFIG)["pad"]
    np.testing.assert_array_equal(pad["mass_global_mean"], pad["mass_mean"])
    np.testing.assert_array_equal(pad["ratio_global_per_job"], pad["ratio_per_job"])
    assert np.isnan(pad["entropy_global_mean"])                                  # unchanged convention
