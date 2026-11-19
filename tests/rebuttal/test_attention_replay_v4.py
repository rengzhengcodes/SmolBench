"""Capture version 4 in the rebuttal replay, and the induction labels it was built for.

Version 4 summary captures add the prompt entropy split by prompt key class
(``sum_prompt_entropy_by_class``) and the sums over the answer rows (class-4 tokens). Covered
here: the audit (version 3 still valid, version 4 checked further), the reader (version 3,
version 4 and mixed arms; answer rows from summary and mass jobs), the loader, the ``extens``
listing as class 1 under ``label_added_lines`` (stored marks when present, synthetic cases),
and the answer tokens as class 4 under ``label_answer_tokens``. Offline throughout.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pytest

from smolbench.evals import attention, attention_analysis
from smolbench.evals.quiz import COMPLIANT, Mark, Marks
from tests._paths import REPO_ROOT, load_by_path
from tests.evals.test_attention import FakeS3
from tests.evals.test_attention_analysis import TinyStore, capture_npz, synthetic_capture
from tests.rebuttal import test_attention_replay as base
from tests.rebuttal import test_attention_replay_summary as summ

ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_v4_under_test")

GEMMA, DSV31 = "gemma-4-31b", "deepseek-v3.1"
LAYERS = ((0, False), (5, False), (0, True), (9, True))
CONFIG = {"num_hidden_layers": 4, "num_attention_heads": 4}
BY_CLASS = "sum_prompt_entropy_by_class"


def _answer_classes(n_prompt: int = 14, n_completion: int = 11, n_answer: int = 4, pad=(4, 10)) -> np.ndarray:
    classes = np.zeros(n_prompt + n_completion, np.uint8)
    if pad is not None:
        classes[pad[0]:pad[1]] = 1
    classes[n_prompt - 1] = 2
    classes[n_prompt:] = 3
    if n_answer:
        classes[-n_answer:] = 4
    return classes


def _cap(seed: int, n_answer: int = 4, **kw) -> dict:
    return synthetic_capture(seed, layers=LAYERS, classes=_answer_classes(n_answer=n_answer), **kw)


def _store(s3: FakeS3, job: attention.Job, cap: dict, *, version: int = 4, corrupt=None) -> None:
    summ._store(s3, job, cap, version=version, corrupt=corrupt)


def _job(cap: dict, job_id: str = "q0") -> attention.Job:
    return summ._job_for(cap, job_id)


# ------------------------------------------------------------------ the audit

@pytest.mark.parametrize("version, n_answer", [(3, 0), (3, 4), (4, 0), (4, 4), (4, 11)])
def test_the_audit_passes_consistent_version_3_and_version_4_summaries(version, n_answer) -> None:
    cap = _cap(40 + n_answer, n_answer=n_answer, boost=1.0)
    job = _job(cap)
    s3 = FakeS3()
    _store(s3, job, cap, version=version)
    assert summ._audit(s3, [job]) == {"q0": None}
    assert summ._audit(s3, [job], mode="summary", capture_version=version) == {"q0": None}


def test_a_summary_run_requires_version_4_but_audit_existing_takes_the_stored_version() -> None:
    cap = _cap(50)
    job = _job(cap)
    s3 = FakeS3()
    _store(s3, job, cap, version=3)
    reason = summ._audit(s3, [job], mode="summary", capture_version=ar.SUMMARY_CAPTURE_VERSION)["q0"]
    assert reason is not None and "capture_version" in reason


def _shift_class_0_to_1(a):
    a[..., 1] += a[..., 0] + 0.25
    a[..., 0] = -0.25
    return a


#: name -> (npz edit of rank 0, word the failure must contain)
_V4_CORRUPTIONS = {
    "missing-by-class": (dict(sum_prompt_entropy_by_class=None), "sum_prompt_entropy_by_class"),
    "missing-answer": (dict(sum_entropy_answer=None), "sum_entropy_answer"),
    "missing-rows-answer": (dict(rows_answer=None), "rows_answer"),
    "by-class-shape": (dict(sum_prompt_entropy_by_class=lambda a: a[..., :2]), "sum_prompt_entropy_by_class"),
    "by-class-nan": (dict(sum_prompt_entropy_by_class=lambda a: a * np.nan), "finite"),
    "identity": (dict(sum_prompt_entropy_by_class=lambda a: a * 1.01), "sums to"),
    "identity-one-class": (dict(sum_prompt_entropy_by_class=lambda a: a + np.eye(3)[0] * 0.05), "sums to"),
    "negative": (dict(sum_prompt_entropy_by_class=_shift_class_0_to_1), "negative"),
    "rows-answer": (dict(rows_answer=lambda a: a + 1), "rows_answer"),
    "n-answer": (dict(n_prompt_entropy_answer=lambda a: a - 1), "n_prompt_entropy_answer"),
    "answer-exceeds": (dict(sum_entropy_answer=lambda a: a + 1000.0), "exceeds"),
    "answer-mass-exceeds": (dict(sum_mass_answer=lambda a: a + 100.0), "exceeds"),
    "answer-identity": (dict(sum_prompt_entropy_by_class_answer=lambda a: a * 0.9), "sum_prompt_entropy_by_class_answer"),
}


@pytest.mark.parametrize("name", sorted(_V4_CORRUPTIONS))
def test_the_audit_refuses_a_version_4_capture_that_breaks_a_rule(name) -> None:
    edit, word = _V4_CORRUPTIONS[name]
    cap = _cap(60, boost=1.0)
    job = _job(cap)
    s3 = FakeS3()
    _store(s3, job, cap, corrupt=lambda rank, blob: summ._edit(blob, **edit) if rank == 0 else blob)
    reason = summ._audit(s3, [job])["q0"]
    assert reason is not None and reason.startswith("rank 0: ") and word in reason, reason


def test_the_identity_tolerance_admits_float32_order_and_tf32_rounding() -> None:
    """A relative 5e-4 deviation (TF32's 2**-11) passes; 2e-3 fails."""
    cap = _cap(61)
    job = _job(cap)
    for factor, ok in ((1 + 4.9e-4, True), (1 + 2e-3, False)):
        s3 = FakeS3()
        _store(s3, job, cap, corrupt=lambda rank, blob, f=factor: summ._edit(
            blob, sum_prompt_entropy_by_class=lambda a: a * f))
        assert (summ._audit(s3, [job])["q0"] is None) is ok, factor


def test_a_version_3_capture_is_audited_without_the_new_rules() -> None:
    """A version-3 meta skips every version-4 rule, even when the npz happens to hold a bad split."""
    cap = _cap(62)
    job = _job(cap)
    s3 = FakeS3()
    summ._store(s3, job, cap, version=3,
                corrupt=lambda rank, blob: summ._edit(blob, sum_prompt_entropy_by_class=np.ones((4, 2, 3))))
    assert summ._audit(s3, [job]) == {"q0": None}


# ------------------------------------------------------------------ the loader

def test_load_capture_carries_the_version_4_arrays_and_refuses_ranks_that_disagree() -> None:
    cap = _cap(70)
    store = TinyStore()
    for rank in range(2):
        store.objects[f"p/q0.r{rank}.npz"] = capture_npz(cap, rank, 2, "summary")
    out = attention_analysis.load_capture(store, "p/", "q0", 2)
    assert out["rows_answer"] == 4 and out[BY_CLASS].shape == (4, 4, 3)
    np.testing.assert_array_equal(out[BY_CLASS], cap["summary"][BY_CLASS])
    by_layer = attention_analysis.entropy_by_layer(out)
    np.testing.assert_allclose(by_layer["prompt_entropy_by_class"].sum(-1), by_layer["prompt_entropy"], rtol=1e-12)
    np.testing.assert_allclose(by_layer["prompt_entropy_by_class_answer"].sum(-1), by_layer["prompt_entropy_answer"],
                               rtol=1e-12)
    # A version-3 rank beside a version-4 rank is another capture.
    store.objects["p/q0.r1.npz"] = capture_npz(cap, 1, 2, "summary", version=3)
    with pytest.raises(ValueError, match="rank 1"):
        attention_analysis.load_capture(store, "p/", "q0", 2)
    single = TinyStore()
    single.objects["p/q0.r0.npz"] = capture_npz(cap, 0, 1, "summary", version=3)
    v3 = attention_analysis.load_capture(single, "p/", "q0", 1)
    assert BY_CLASS not in v3 and "rows_answer" not in v3
    assert "prompt_entropy_by_class" not in attention_analysis.entropy_by_layer(v3)


# ------------------------------------------------------------------ the reader

def _mirror(root: Path, jobs: dict, *, arm: str = "intens", source: str = "summary_f16") -> None:
    """``{idx: (capture, kind, version)}`` as one verified run directory.

    ``source`` "summary_f16" (default) sums the float16 rows, so summary and mass jobs hold the
    same numbers; "summary" sums the unrounded rows, where the class split adds up exactly.
    """
    run_dir = root / "induction" / GEMMA / "seed=0" / f"{arm}--{summ.STAMP}"
    run_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for idx, (cap, kind, version) in jobs.items():
        for rank in range(2):
            (run_dir / f"q{idx}.r{rank}.npz").write_bytes(
                capture_npz(cap, rank, 2, kind, summary=source, version=version))
        entries.append({"job_id": f"j{idx}", "mark_index": idx, "status": "verified"})
    (run_dir / "manifest--20261116T000000.000000Z.json").write_text(json.dumps({"jobs": entries}))


def _read(root: Path) -> dict:
    return ar.read_captures(GEMMA, root, arms=("intens",), config=CONFIG)["intens"]


def test_a_version_3_arm_has_none_of_the_new_keys_and_the_same_values(tmp_path: Path) -> None:
    caps = [_cap(80, n_answer=0), _cap(81, n_answer=0, boost=1.0)]
    _mirror(tmp_path / "v3", {i: (c, "summary", 3) for i, c in enumerate(caps)})
    _mirror(tmp_path / "v4", {i: (c, "summary", 4) for i, c in enumerate(caps)})
    v3, v4 = _read(tmp_path / "v3"), _read(tmp_path / "v4")
    assert not any("by_class" in k or "answer" in k for k in v3)
    assert set(v4) - set(v3) == {
        "prompt_entropy_by_class_jobs", "prompt_entropy_by_class_per_job", "prompt_entropy_by_class_mean",
        "prompt_entropy_by_class_global_per_job", "prompt_entropy_by_class_global_mean"}
    for key, value in v3.items():
        if key == "job_labels":   # the folders differ by name only
            assert [x.replace("/v3/", "/") for x in value] == [x.replace("/v4/", "/") for x in v4[key]]
        elif isinstance(value, np.ndarray):
            np.testing.assert_array_equal(value, v4[key], err_msg=key)
        else:
            assert value == v4[key] or (value != value and v4[key] != v4[key]), key


def test_the_class_split_per_job_adds_up_to_the_jobs_prompt_entropy(tmp_path: Path) -> None:
    caps = [_cap(90), _cap(91, boost=1.0), _cap(92, boost=-1.0)]
    _mirror(tmp_path, {i: (c, "summary", 4) for i, c in enumerate(caps)}, source="summary")
    out = _read(tmp_path)
    assert out["prompt_entropy_by_class_jobs"] == 3
    for split_key, whole_key in (("prompt_entropy_by_class_per_job", "prompt_entropy_per_job"),
                                 ("prompt_entropy_by_class_global_per_job", "prompt_entropy_global_per_job")):
        split = np.asarray(out[split_key])
        assert split.shape == (3, 3)
        np.testing.assert_allclose(split.sum(-1), out[whole_key], rtol=1e-12)
    np.testing.assert_allclose(out["prompt_entropy_by_class_mean"],
                               np.mean(out["prompt_entropy_by_class_per_job"], axis=0), rtol=1e-12)
    np.testing.assert_allclose(out["prompt_entropy_by_class_mean"].sum(), out["prompt_entropy_mean"], rtol=1e-12)
    # The direct definition for job 0: class sums over every layer and head / defined rows.
    s = caps[0]["summary"]
    np.testing.assert_allclose(out["prompt_entropy_by_class_per_job"][0],
                               s[BY_CLASS].sum(axis=(0, 1)) / s["n_prompt_entropy"].sum(), rtol=1e-12)
    # Global layers are 0 and 2 (window 0).
    np.testing.assert_allclose(out["prompt_entropy_by_class_global_per_job"][0],
                               s[BY_CLASS][[0, 2]].sum(axis=(0, 1)) / s["n_prompt_entropy"][[0, 2]].sum(),
                               rtol=1e-12)
    # Class 1 (the pad) and class 2 take a share; nothing is negative.
    assert (np.asarray(out["prompt_entropy_by_class_per_job"]) > 0).all()


def test_a_mixed_arm_reads_the_split_from_its_version_4_jobs_only(tmp_path: Path) -> None:
    caps = [_cap(100), _cap(101, boost=1.0), _cap(102)]
    _mirror(tmp_path, {0: (caps[0], "summary", 3), 1: (caps[1], "summary", 4), 2: (caps[2], "mass", 4)})
    out = _read(tmp_path)
    assert out["jobs"] == 3 and out["prompt_entropy_by_class_jobs"] == 1
    per_job = np.asarray(out["prompt_entropy_by_class_per_job"])
    assert np.isnan(per_job[[0, 2]]).all() and not np.isnan(per_job[1]).any()
    np.testing.assert_array_equal(out["prompt_entropy_by_class_mean"], per_job[1])
    assert out["prompt_entropy_jobs"] == 3   # the existing statistic still reads all three


def test_answer_rows_read_the_same_from_summary_and_mass_jobs(tmp_path: Path) -> None:
    caps = [_cap(110, n_answer=4), _cap(111, n_answer=7, boost=1.0)]
    _mirror(tmp_path / "s", {i: (c, "summary", 4) for i, c in enumerate(caps)})
    _mirror(tmp_path / "m", {i: (c, "mass", 4) for i, c in enumerate(caps)})
    _mirror(tmp_path / "x", {0: (caps[0], "mass", 4), 1: (caps[1], "summary", 4)})
    s, m, x = _read(tmp_path / "s"), _read(tmp_path / "m"), _read(tmp_path / "x")
    for out in (s, m, x):
        assert out["prompt_entropy_answer_jobs"] == 2
        np.testing.assert_allclose(out["prompt_entropy_answer_per_job"], s["prompt_entropy_answer_per_job"],
                                   rtol=1e-9)
        np.testing.assert_allclose(out["prompt_entropy_answer_global_per_job"],
                                   s["prompt_entropy_answer_global_per_job"], rtol=1e-9)
    # Direct definition for job 0: the answer rows only (the last 4 response rows).
    rows = caps[0]["prompt_entropy"].astype(np.float64)[:, -4:, :]
    assert s["prompt_entropy_answer_per_job"][0] == pytest.approx(np.nanmean(rows), rel=1e-9)
    assert s["prompt_entropy_answer_per_job"][0] != pytest.approx(s["prompt_entropy_per_job"][0], rel=1e-3)
    # The class split over the answer rows: summary only, NaN for mass jobs; it adds up (exactly
    # on the unrounded sums; the float16-row sums round the split and the total separately).
    _mirror(tmp_path / "u", {i: (c, "summary", 4) for i, c in enumerate(caps)}, source="summary")
    u = _read(tmp_path / "u")
    np.testing.assert_allclose(np.asarray(u["prompt_entropy_by_class_answer_per_job"]).sum(-1),
                               u["prompt_entropy_answer_per_job"], rtol=1e-12)
    np.testing.assert_allclose(np.asarray(s["prompt_entropy_by_class_answer_per_job"]).sum(-1),
                               s["prompt_entropy_answer_per_job"], rtol=1e-3)
    assert np.isnan(m["prompt_entropy_by_class_answer_per_job"]).all()
    assert np.isnan(x["prompt_entropy_by_class_answer_per_job"][0]).all()
    np.testing.assert_array_equal(x["prompt_entropy_by_class_answer_mean"], s["prompt_entropy_by_class_answer_per_job"][1])
    assert s["prompt_entropy_answer_mean"] == pytest.approx(np.mean(s["prompt_entropy_answer_per_job"]), rel=1e-12)


def test_an_arm_without_answer_labels_has_no_answer_keys(tmp_path: Path) -> None:
    _mirror(tmp_path, {0: (_cap(120, n_answer=0), "summary", 4), 1: (_cap(121, n_answer=0), "mass", 4)})
    assert not any("answer" in k for k in _read(tmp_path))


# ------------------------------------------------------------------ extens listing as class 1

_RULES = "Context:\nrules:\nEvery 1 positions write ab.\nEvery 2 positions write cd.\n"
_LISTING = "Position 1: ab.\nPosition 2: ab|cd.\n"
_QUESTION = "\nQuestion:\nHow many of the positions 1 through 2 include 'ab'?"


def test_the_listing_span_is_what_extens_adds_after_the_rules() -> None:
    intens, extens = _RULES + _QUESTION, _RULES + _LISTING + _QUESTION
    start, end = ar._extens_listing_span(intens, extens)
    assert extens[start:end] == _LISTING
    for bad, needle in ((extens.replace("Every 2", "Every 3"), "does not start"),
                        (_RULES + _LISTING + _QUESTION.replace("'ab'", "'cd'"), "question differs"),
                        (_RULES + _QUESTION, "empty"), (_RULES + _LISTING, "no ")):
        with pytest.raises(ValueError, match=needle):
            ar._extens_listing_span(intens, bad)
    # The related_intens messages are unchanged.
    with pytest.raises(ValueError, match="the related_intens query does not start"):
        ar._related_pad_span(intens, "x" + extens)


def _write_runs(root: Path, model: str, arms: dict, seed: int = 0) -> None:
    seed_dir = root / "induction" / model / f"seed={seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    for arm, (queries, reasoning) in arms.items():
        marks = Marks(model=model, marks=tuple(
            Mark(query=q, answer=1, response="2", score=1, compliance=COMPLIANT, reasoning=reasoning)
            for q in queries))
        (seed_dir / f"{arm}--{summ.STAMP}.yaml").write_text(marks.dumps())


def _build(root: Path, tok=None, **kw):
    tok = tok or base.CharTokenizer(base.DS_SPECIALS)
    return ar.build_jobs(DSV31, root, "p", tokenizer=tok, template=base.ds_template(), **kw)


def test_synthetic_extens_listing_is_class_1_only_with_the_flag(tmp_path: Path) -> None:
    intens = [_RULES + _QUESTION, _RULES + _QUESTION.replace("'ab'", "'cd'")]
    extens = [_RULES + _LISTING + q[len(_RULES):] for q in intens]
    _write_runs(tmp_path, DSV31, {"intens": (intens, "think"), "extens": (extens, "think"),
                                  "noise_intens": ([_RULES + base.PAD + _QUESTION], "think")})
    off, off_err = _build(tmp_path)
    on, on_err = _build(tmp_path, label_added_lines=True)
    assert off_err == on_err == []
    assert [p.job.job_id for p in off] == [p.job.job_id for p in on]
    tok = base.CharTokenizer(base.DS_SPECIALS)
    for a, b in zip(off, on):
        if b.run.arm != "extens":
            assert a.job == b.job, b.run.arm
            continue
        assert 1 not in a.job.classes          # no whitespace run of 32 characters: none by rule
        prompt = b.job.prompt_token_ids
        tok.encode_ids("".join(base.DS_SPECIALS))  # register the specials in the stub's vocabulary
        labelled = [i for i, c in zip(prompt, b.job.classes) if c == 1]
        assert len(labelled) == len(_LISTING)  # one character per stub token, none straddles
        assert a.job.classes[len(prompt):] == b.job.classes[len(prompt):]
        assert any("pad span by construction" in n for n in b.notes)


def test_an_extens_mark_whose_listing_cannot_be_located_is_a_plan_error(tmp_path: Path) -> None:
    _write_runs(tmp_path, DSV31, {"intens": ([_RULES + _QUESTION], "t"),
                                  "extens": ([_RULES + _LISTING + _QUESTION, "other" + _LISTING + _QUESTION],
                                             "t")})
    jobs, errors = _build(tmp_path, label_added_lines=True)
    assert [p.mark_index for p in jobs if p.run.arm == "extens"] == [0]
    assert len(errors) == 1 and "#q1" in errors[0] and "intens" in errors[0]
    # Without an intens run for the seed: every extens mark is an error, the flag off plans them.
    other = tmp_path / "other"
    _write_runs(other, DSV31, {"extens": ([_RULES + _LISTING + _QUESTION], "t")})
    jobs, errors = _build(other, label_added_lines=True)
    assert jobs == [] and "no intens run for seed 0" in errors[0]
    assert len(_build(other)[0]) == 1


def test_an_extens_rebuild_without_a_class_1_token_is_a_plan_error(tmp_path: Path) -> None:
    query = _RULES + _LISTING + _QUESTION
    _write_runs(tmp_path, DSV31, {"intens": ([_RULES + _QUESTION], "t"), "extens": ([query], "t")})
    # A tokenizer that keeps the whole query as one token: it straddles the listing's edges.
    tok = base.CharTokenizer(base.DS_SPECIALS + (query,))
    jobs, errors = _build(tmp_path, tok=tok, label_added_lines=True)
    assert [p.run.arm for p in jobs] == ["intens"]
    assert len(errors) == 1 and "no token is class 1" in errors[0]


def test_extens_labels_on_the_stored_marks(tmp_path: Path) -> None:
    """The stored rebuttal marks (skipped when absent): every extens mark is labelled, its class-1
    text is its listing exactly, and the other arms are unchanged by the flag."""
    root = ar.DEFAULT_RESULTS_ROOT
    if not (root / "induction" / DSV31).is_dir():
        pytest.skip("no stored induction marks under rebuttal/results/induction")
    tok = base.CharTokenizer(base.DS_SPECIALS)
    off, off_err = _build(root, tok=tok, seeds=[0, 1])
    on, on_err = _build(root, tok=tok, seeds=[0, 1], label_added_lines=True)
    assert on_err == off_err == [] and len(on) == len(off) == 72
    marks = {}
    for item in on:
        marks.setdefault((item.run.seed, item.run.arm), Marks.loads(item.run.path.read_text()).marks)
    for a, b in zip(off, on):
        assert a.job.job_id == b.job.job_id
        if b.run.arm != "extens":
            assert a.job == b.job, b.job.job_id
            continue
        query = marks[(b.run.seed, "extens")][b.mark_index].query
        intens = marks[(b.run.seed, "intens")][b.mark_index].query
        start, end = ar._extens_listing_span(intens, query)
        text = "".join(tok.decode_tokens([i for i, c in zip(b.job.prompt_token_ids, b.job.classes) if c == 1]))
        assert text == query[start:end] and text.startswith("Position 1: ") and text.endswith(".\n")
        assert 1 not in a.job.classes
    assert all(1 not in p.job.classes for p in on if p.run.arm == "intens")


# ------------------------------------------------------------------ answer tokens as class 4

def test_rebuild_labels_the_response_and_end_of_turn_class_4() -> None:
    tok = base.CharTokenizer(base.DS_SPECIALS)
    fmt = ar.REASONING_FORMATS[DSV31]
    kw = dict(tokenizer=tok, template=base.ds_template(), fmt=fmt)
    plain = ar.rebuild_sequence("Q?", "think", "42", **kw)
    r = ar.rebuild_sequence("Q?", "think", "42", label_answer=True, **kw)
    assert r.prompt_ids == plain.prompt_ids and r.completion_ids == plain.completion_ids
    q = len(r.prompt_ids)
    assert r.classes[:q] == plain.classes[:q] and set(plain.classes[q:]) == {3}
    # "think" (5) and </think> stay 3; "4", "2" and the end-of-turn token are 4.
    assert list(r.classes[q:]) == [3] * 6 + [4] * 3
    assert any("3 class 4, 0 straddle" in n for n in r.notes)
    # No stored reasoning: the whole completion is the answer (delimiters included).
    bare = ar.rebuild_sequence("Q?", None, "42", label_answer=True, **kw)
    assert set(bare.classes[len(bare.prompt_ids):]) == {4}
    # A token that straddles the boundary stays 3.
    merged = base.CharTokenizer(base.DS_SPECIALS + ("</think>4",))
    s = ar.rebuild_sequence("Q?", "think", "42", label_answer=True, tokenizer=merged,
                            template=base.ds_template(), fmt=fmt)
    assert list(s.classes[len(s.prompt_ids):]) == [3] * 6 + [4] * 2
    assert any("1 straddle" in n for n in s.notes)


def test_label_answer_tokens_counts_class_4_in_the_plan_and_refuses_an_unlabelled_job(tmp_path: Path) -> None:
    _write_runs(tmp_path, DSV31, {"intens": (["ab", "abcd"], "r")})
    tok = base.CharTokenizer(base.DS_SPECIALS)
    kwargs = base._plan_kwargs(tok)
    plain = ar.plan_replay(tmp_path, [DSV31], s3_uri="s3://b/p", **kwargs)[DSV31]
    plan = ar.plan_replay(tmp_path, [DSV31], s3_uri="s3://b/p", label_answer_tokens=True, **kwargs)[DSV31]
    assert "class4_tokens" not in plain.per_arm["intens"] and "label_answer_tokens" not in plain.summary()
    # "1" plus the end-of-turn token per mark.
    assert plan.per_arm["intens"]["class4_tokens"] == 4 and plan.per_arm["intens"]["class4_tokens_mean"] == 2.0
    assert "class-4 tokens 4 total, 2.0 per job" in plan.summary() and plan.label_answer_tokens
    jobs, _ = _build(tmp_path, label_answer_tokens=True)
    assert all(p.job.classes[p.job.query_start:][-2:] == (4, 4) for p in jobs)
    rebuilt = ar.rebuild_sequence("Q?", "t", "1", tokenizer=tok, template=base.ds_template(),
                                  fmt=ar.REASONING_FORMATS[DSV31])
    with pytest.raises(ValueError, match="class 4"):
        ar._check_answer_labelled(rebuilt, True)
    ar._check_answer_labelled(rebuilt, False)


def test_a_labelled_run_records_both_flags_in_every_manifest_and_verifies(tmp_path: Path) -> None:
    summ._write_results(tmp_path)
    s3 = FakeS3()
    report = summ._replay(tmp_path, summ.SummaryBox(s3), s3, mode="summary",
                          label_added_lines=True, label_answer_tokens=True)
    assert len(report.verified) == 2 and report.audit_failures == {}
    assert report.plan.label_answer_tokens and report.plan.label_added_lines
    for key in report.manifests:
        manifest = json.loads(s3.objects[key])
        assert manifest["label_answer_tokens"] is True and manifest["label_added_lines"] is True
    for key, blob in s3.objects.items():
        if key.endswith(".npz"):
            npz = np.load(io.BytesIO(blob))
            assert int(npz["capture_version"]) == 4 and int(npz["rows_answer"]) == 2   # "1" + end of turn
    plain_s3 = FakeS3()
    plain = summ._replay(tmp_path, summ.SummaryBox(plain_s3), plain_s3, mode="summary")
    assert all("label_answer_tokens" not in json.loads(plain_s3.objects[k]) for k in plain.manifests)
