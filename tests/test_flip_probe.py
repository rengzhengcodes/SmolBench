"""Offline tests for scripts/flip_probe.py's PURE helpers and small,
locally-mockable I/O pieces.

Covers logic that does not touch AWS, Lean, or the network: stock
vllm_args reconstruction, cell-key deduplication, the Mathlib-only
measurable-population filter and its exact-count gate (2026-08-18 spec
amendment -- see the module docstring's "Sample-stage population" section),
sample-draw determinism, the Clopper-Pearson interval, the flip/verifier-
drift statistics, the study-originals row-prep helper, the local-file S3
client stand-in used by ``--stage verify``'s leg (b), the ``_spool_flip_run``
upload filter, and ``--stage analyze``'s whitelist-provenance self-check
(driven end-to-end against a `tmp_path` results tree via
``SMOLBENCH_LEAN_RESULTS``, with no AWS client involved since both required
inputs are placed on local disk directly).

``scripts/`` is not an importable package, so `flip_probe` is loaded by path
(mirrors ``tests/test_delivery_probe.py``'s own convention for a sibling
``scripts/*.py`` file).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "flip_probe", Path(__file__).resolve().parents[1] / "scripts" / "flip_probe.py"
)
flip_probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = flip_probe
_SPEC.loader.exec_module(flip_probe)


# ---------------------------------------------------------------------------
# stock_vllm_args
# ---------------------------------------------------------------------------


def test_stock_vllm_args_strips_determinism_suffix_and_adds_caching_flag():
    det = ["--no-enable-prefix-caching", "--max-num-seqs", "1", "--enforce-eager", "--seed", "0"]
    spec_args = ["--revision", "abc123", "--tokenizer-revision", "abc123"] + det
    got = flip_probe.stock_vllm_args(spec_args, det)
    assert got == ["--revision", "abc123", "--tokenizer-revision", "abc123", "--enable-prefix-caching"]
    # No determinism-bundle remnant, no duplicate --enable-prefix-caching.
    for flag in det:
        assert flag not in got
    assert got.count("--enable-prefix-caching") == 1


def test_stock_vllm_args_pre_determinism_shape_strips_bare_caching_flag():
    """A pre-2026-08-18 spec shape (no determinism suffix, but already
    carrying a bare --enable-prefix-caching) must not end up with two."""
    det = ["--no-enable-prefix-caching", "--max-num-seqs", "1", "--enforce-eager", "--seed", "0"]
    spec_args = ["--revision", "abc123", "--enable-prefix-caching"]
    got = flip_probe.stock_vllm_args(spec_args, det)
    assert got == ["--revision", "abc123", "--enable-prefix-caching"]
    assert got.count("--enable-prefix-caching") == 1


def test_stock_vllm_args_never_mutates_its_input():
    det = ["--seed", "0"]
    spec_args = ["--revision", "abc123"] + det
    original = list(spec_args)
    flip_probe.stock_vllm_args(spec_args, det)
    assert spec_args == original


def test_stock_vllm_args_empty_determinism_args_degrades_to_caching_strip():
    got = flip_probe.stock_vllm_args(["--enable-prefix-caching", "--foo"], [])
    assert got == ["--foo", "--enable-prefix-caching"]


# ---------------------------------------------------------------------------
# dedupe_rows_earliest_wins / is_mathlib_cell / measurable_cell_keys /
# assert_population_size -- includes the 2026-08-18 Mathlib-only amendment
# ---------------------------------------------------------------------------


def _row(model, theorem, k, rung, ridx, verdict, file_path="Mathlib/Foo.lean", **extra):
    row = {
        "kind": "cell", "model": model, "theorem_id": theorem, "k": k,
        "rung": rung, "replicate_idx": ridx, "verdict": verdict,
        "file_path": file_path, "candidate_proof": "x", "lean_error": None,
        "prompt_tokens": 10,
    }
    row.update(extra)
    return row


def test_dedupe_rows_earliest_wins_keeps_first_occurrence():
    first = _row("m", "T", 1, "stepk:1", 0, "success")
    dup = _row("m", "T", 1, "stepk:1", 0, "exception")
    by_key = flip_probe.dedupe_rows_earliest_wins([first, dup])
    key = ("m", "T", 1, "stepk:1", 0)
    assert by_key[key] is first
    assert len(by_key) == 1


def test_dedupe_rows_earliest_wins_skips_non_cell_rows():
    sanity = {"kind": "sanity", "theorem_id": "T", "verdict": "success"}
    cell = _row("m", "T", 1, "stepk:1", 0, "success")
    by_key = flip_probe.dedupe_rows_earliest_wins([sanity, cell])
    assert len(by_key) == 1


def test_is_mathlib_cell_excludes_std_package_paths():
    mathlib_row = _row("m", "T", 1, "stepk:1", 0, "success", file_path="Mathlib/Algebra/Foo.lean")
    std_row = _row("m", "S", 1, "stepk:1", 0, "success", file_path=".lake/packages/std/Std/Data/Foo.lean")
    std_row_rooted = _row(
        "m", "S2", 1, "stepk:1", 0, "success",
        file_path="/home/box/.lake/packages/std/Std/Data/Bar.lean",
    )
    missing_path_row = _row("m", "T2", 1, "stepk:1", 0, "success", file_path="")
    assert flip_probe.is_mathlib_cell(mathlib_row) is True
    assert flip_probe.is_mathlib_cell(std_row) is False
    assert flip_probe.is_mathlib_cell(std_row_rooted) is False
    assert flip_probe.is_mathlib_cell(missing_path_row) is True


def _synthetic_study_rows():
    """9 measurable Mathlib cells (4 theorems x 2 rungs + 1 given_up), 2 exception cells,
    1 replay_failed (prefix-class) cell, 1 Std-package cell, and 1 duplicate row (same key as T0/stepk:1, arriving
    SECOND with a verdict that would flip the outcome if it won)."""
    rows = []
    for ti in range(4):
        for ri, rung in enumerate(["stepk:1", "hint:2"]):
            verdict = "success" if (ti + ri) % 2 == 0 else "lean_error"
            rows.append(_row("m", f"T{ti}", 1, rung, 0, verdict))
    rows.append(_row("m", "T4", 1, "stepk:1", 0, "exception"))
    rows.append(_row("m", "T5", 1, "stepk:1", 0, "exception"))
    # Mathlib prefix-failure cell: verifier infrastructure, NOT measurable
    # (settled live 2026-08-18 -- the 792-vs-711 gate firing; see
    # measurable_cell_keys's RESOLVED note).
    rows.append(_row("m", "T6", 1, "stepk:1", 0, "replay_failed"))
    # given_up IS measurable: the candidate drove Lean to a given-up proof
    # state -- a judgment on the candidate, like lean_error (4 such cells
    # measured live in the study lane; 707+4=711).
    rows.append(_row("m", "T7", 1, "stepk:1", 0, "given_up"))
    rows.append(_row("m", "S0", 1, "stepk:1", 0, "success", file_path=".lake/packages/std/Std/Foo.lean"))
    # Duplicate of ("m","T0",1,"stepk:1",0) -- earliest (success) must win,
    # not this later exception row (which would otherwise wrongly EXCLUDE it).
    rows.append(_row("m", "T0", 1, "stepk:1", 0, "exception"))
    return rows


def test_measurable_cell_keys_excludes_exception_std_and_resolves_duplicates():
    measurable = flip_probe.measurable_cell_keys(_synthetic_study_rows())
    assert len(measurable) == 9
    assert ("m", "T7", 1, "stepk:1", 0) in measurable  # given_up IS measurable
    assert ("m", "S0", 1, "stepk:1", 0) not in measurable  # Std-package excluded
    assert ("m", "T4", 1, "stepk:1", 0) not in measurable  # exception excluded
    assert ("m", "T5", 1, "stepk:1", 0) not in measurable  # exception excluded
    assert ("m", "T6", 1, "stepk:1", 0) not in measurable  # replay_failed (prefix class) excluded
    # The duplicated key survives (via its EARLIEST, "success" occurrence).
    assert ("m", "T0", 1, "stepk:1", 0) in measurable
    assert measurable == sorted(measurable)  # ascending-sorted


def test_assert_population_size_passes_on_exact_match():
    flip_probe.assert_population_size(list(range(711)), 711)  # must not raise


def test_assert_population_size_raises_with_observed_count_in_message():
    """A concurrent std-recovery workstream growing the population must be
    caught loudly, with the observed count actionable in the message."""
    with pytest.raises(ValueError, match=r"expected exactly 711.*found 715"):
        flip_probe.assert_population_size(list(range(715)), 711)


def test_measurable_cell_keys_feeds_the_exact_population_gate():
    """End-to-end: the synthetic fixture's Mathlib-only population (8) must
    fail the 711 gate loudly rather than silently sampling a shifted pool."""
    measurable = flip_probe.measurable_cell_keys(_synthetic_study_rows())
    with pytest.raises(ValueError, match=r"expected exactly 711"):
        flip_probe.assert_population_size(measurable, 711)


# ---------------------------------------------------------------------------
# select_sample_keys -- Random(0) determinism, golden values
# ---------------------------------------------------------------------------


def test_select_sample_keys_is_deterministic_and_matches_golden_values():
    """Random(0) over the SORTED population must reproduce an exact, golden
    draw -- pinned so a future refactor of the sampling machinery cannot
    silently change which cells a live run would draw."""
    measurable = flip_probe.measurable_cell_keys(_synthetic_study_rows())
    drawn = flip_probe.select_sample_keys(measurable, 5, 0)
    assert sorted(drawn) == [
        ("m", "T0", 1, "hint:2", 0),
        ("m", "T1", 1, "hint:2", 0),
        ("m", "T2", 1, "hint:2", 0),
        ("m", "T3", 1, "hint:2", 0),
        ("m", "T7", 1, "stepk:1", 0),
    ]  # golden re-pinned 2026-08-18: the fixture population legitimately grew
       # (given_up row T7 is measurable), which reshuffles Random(0)'s draw
    from smolbench.deduction.lean import runner

    assert (
        runner.hash_cell_keys(sorted(drawn))
        == "2a7d2b72c4c196a9d56e81dacf6f0a95c5aaef138ad5227645dc4e43c74fb315"
    )
    # Determinism: calling again with the SAME seed reproduces it exactly.
    assert sorted(flip_probe.select_sample_keys(measurable, 5, 0)) == sorted(drawn)


def test_select_sample_keys_different_seed_differs():
    measurable = flip_probe.measurable_cell_keys(_synthetic_study_rows())
    a = sorted(flip_probe.select_sample_keys(measurable, 5, 0))
    b = sorted(flip_probe.select_sample_keys(measurable, 5, 1))
    assert a != b


# ---------------------------------------------------------------------------
# clopper_pearson_interval -- defining properties, not a remembered table
# ---------------------------------------------------------------------------


def test_clopper_pearson_degenerate_bounds():
    lo0, hi0 = flip_probe.clopper_pearson_interval(0, 50)
    assert lo0 == 0.0
    assert 0.0 < hi0 < 1.0

    lon, hin = flip_probe.clopper_pearson_interval(50, 50)
    assert hin == 1.0
    assert 0.0 < lon < 1.0


@pytest.mark.parametrize("k,n", [(1, 50), (10, 50), (25, 50), (49, 50), (3, 10), (100, 200)])
def test_clopper_pearson_bounds_satisfy_the_defining_equation(k, n):
    """The CP lower bound is the p at which P(X >= k) == alpha/2; the upper
    bound is the p at which P(X <= k) == alpha/2 -- verify both via
    `_binom_cdf` directly, rather than pinning a remembered numeric table."""
    alpha = 0.05
    lower, upper = flip_probe.clopper_pearson_interval(k, n, alpha=alpha)
    # P(X >= k | lower) == 1 - _binom_cdf(k-1, n, lower) == alpha/2
    assert math.isclose(
        1 - flip_probe._binom_cdf(k - 1, n, lower), alpha / 2, abs_tol=1e-6
    )
    # P(X <= k | upper) == _binom_cdf(k, n, upper) == alpha/2
    assert math.isclose(flip_probe._binom_cdf(k, n, upper), alpha / 2, abs_tol=1e-6)
    assert 0.0 <= lower <= k / n <= upper <= 1.0


def test_clopper_pearson_monotone_in_k():
    n = 50
    bounds = [flip_probe.clopper_pearson_interval(k, n) for k in range(n + 1)]
    lowers = [b[0] for b in bounds]
    uppers = [b[1] for b in bounds]
    assert lowers == sorted(lowers)
    assert uppers == sorted(uppers)


def test_clopper_pearson_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        flip_probe.clopper_pearson_interval(-1, 10)
    with pytest.raises(ValueError):
        flip_probe.clopper_pearson_interval(11, 10)
    with pytest.raises(ValueError):
        flip_probe.clopper_pearson_interval(0, 0)


# ---------------------------------------------------------------------------
# flip_stats / verifier_drift_stats -- hand-built pairs, known b/c/rate/CI
# ---------------------------------------------------------------------------


def test_flip_stats_hand_built_pairs_known_b_c_rate_and_ci():
    # 10 cells: 4 both-pass (a), 2 orig-pass/rerun-fail (b), 1 orig-fail/
    # rerun-pass (c), 3 both-fail (d).
    pairs = {}
    for i in range(4):
        pairs[("m", f"A{i}", 1, "stepk:1", 0)] = ("success", "success")
    for i in range(2):
        pairs[("m", f"B{i}", 1, "stepk:1", 0)] = ("success", "lean_error")
    pairs[("m", "C0", 1, "stepk:1", 0)] = ("lean_error", "success")
    for i in range(3):
        pairs[("m", f"D{i}", 1, "stepk:1", 0)] = ("lean_error", "incomplete")

    stats = flip_probe.flip_stats(pairs)
    assert stats["n"] == 10
    assert stats["a_both_pass"] == 4
    assert stats["b_orig_pass_rerun_fail"] == 2
    assert stats["c_orig_fail_rerun_pass"] == 1
    assert stats["d_both_fail"] == 3
    assert stats["discordant"] == 3
    assert stats["flip_rate"] == pytest.approx(0.3)
    assert stats["pass_at_1_se"] == pytest.approx(math.sqrt(0.3 * 0.7 / 10))
    # CI must equal a direct clopper_pearson_interval(discordant, n) call.
    assert stats["flip_rate_ci95"] == list(flip_probe.clopper_pearson_interval(3, 10))
    assert sorted(stats["flipped_keys"]) == sorted(
        [["m", f"B{i}", 1, "stepk:1", 0] for i in range(2)]
        + [["m", "C0", 1, "stepk:1", 0]]
    )


def test_flip_stats_empty_pairs_is_well_defined():
    stats = flip_probe.flip_stats({})
    assert stats["n"] == 0
    assert stats["flip_rate"] == 0.0
    assert stats["flip_rate_ci95"] == [0.0, 0.0]
    assert stats["pass_at_1_se"] == 0.0
    assert stats["flipped_keys"] == []


def test_verifier_drift_stats_hand_built_pairs():
    pairs = {
        ("m", "A", 1, "stepk:1", 0): ("success", "success"),
        ("m", "B", 1, "stepk:1", 0): ("success", "lean_error"),
        ("m", "C", 1, "stepk:1", 0): ("lean_error", "lean_error"),
    }
    drift = flip_probe.verifier_drift_stats(pairs)
    assert drift["n"] == 3
    assert drift["agree"] == 2
    assert drift["agreement_rate"] == pytest.approx(2 / 3)
    assert drift["disagreements"] == [
        {"key": ["m", "B", 1, "stepk:1", 0], "study_verdict": "success", "reverified_verdict": "lean_error"}
    ]


def test_is_pass():
    assert flip_probe.is_pass("success") is True
    assert flip_probe.is_pass("lean_error") is False


def test_is_pass_refuses_the_ungraded_sentinel():
    """``"unverified"`` is not a verdict -- it is the ABSENCE of one.

    Rows are written with this placeholder at generation time and graded
    later. Scoring it as a failure (which `is_pass` used to do) silently
    biases every paired b/c statistic downward, and does so invisibly: the
    report looks complete. Callers that can legitimately hold ungraded rows
    filter them out first (`measurable_cell_keys` does), so reaching here with
    one is a bug, not a case to handle.
    """
    with pytest.raises(ValueError) as excinfo:
        flip_probe.is_pass("unverified")
    message = str(excinfo.value)
    assert "unverified" in message
    assert "ungraded" in message.lower()


# ---------------------------------------------------------------------------
# _prepare_originals_rows
# ---------------------------------------------------------------------------


def test_prepare_originals_rows_resets_verdict_and_stashes_study_verdict():
    study_rows = [
        _row("m", "T0", 1, "stepk:1", 0, "success", candidate_proof="proof0", lean_error=None),
        _row("m", "T1", 1, "hint:2", 0, "lean_error", candidate_proof="proof1", lean_error="boom"),
    ]
    whitelist = [("m", "T1", 1, "hint:2", 0), ("m", "T0", 1, "stepk:1", 0)]  # unsorted on purpose

    out = flip_probe._prepare_originals_rows(study_rows, whitelist)

    assert [r["theorem_id"] for r in out] == ["T0", "T1"]  # SORTED key order
    t0, t1 = out
    assert t0["verdict"] == "unverified"
    assert t0["_study_verdict"] == "success"
    assert t0["_study_lean_error"] is None
    assert t0["lean_error"] is None
    assert t0["final_state_pp"] is None
    assert t0["candidate_proof"] == "proof0"  # preserved

    assert t1["verdict"] == "unverified"
    assert t1["_study_verdict"] == "lean_error"
    assert t1["_study_lean_error"] == "boom"
    assert t1["candidate_proof"] == "proof1"


def test_prepare_originals_rows_raises_on_missing_whitelisted_key():
    study_rows = [_row("m", "T0", 1, "stepk:1", 0, "success")]
    whitelist = [("m", "T0", 1, "stepk:1", 0), ("m", "GHOST", 9, "stepk:1", 0)]
    with pytest.raises(ValueError, match="GHOST"):
        flip_probe._prepare_originals_rows(study_rows, whitelist)


def test_prepare_originals_rows_dedupes_earliest_wins_before_selection():
    """A duplicated study row for a whitelisted key must resolve via the
    SAME earliest-wins rule as everywhere else in this module."""
    first = _row("m", "T0", 1, "stepk:1", 0, "success", candidate_proof="EARLIEST")
    dup = _row("m", "T0", 1, "stepk:1", 0, "lean_error", candidate_proof="LATER")
    out = flip_probe._prepare_originals_rows([first, dup], [("m", "T0", 1, "stepk:1", 0)])
    assert len(out) == 1
    assert out[0]["candidate_proof"] == "EARLIEST"
    assert out[0]["_study_verdict"] == "success"


# ---------------------------------------------------------------------------
# _LocalRunClient -- the fake S3 client behind --stage verify's leg (b)
# ---------------------------------------------------------------------------


def test_local_run_client_serves_rows_and_raises_nosuchkey_before_upload(tmp_path):
    from botocore.exceptions import ClientError

    rows_path = tmp_path / "originals_all_rows.jsonl"
    rows_path.write_text('{"kind": "cell"}\n')
    verified_path = tmp_path / "verified_rows.jsonl"

    client = flip_probe._LocalRunClient(
        rows_path=rows_path, verified_path=verified_path,
        rows_filename="all_rows.jsonl", verified_filename="verified_rows.jsonl",
    )

    got = client.get_object(Bucket="b", Key="whatever/all_rows.jsonl")
    assert got["Body"].read() == rows_path.read_bytes()

    with pytest.raises(ClientError) as exc_info:
        client.get_object(Bucket="b", Key="whatever/verified_rows.jsonl")
    assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

    with pytest.raises(ValueError):
        client.get_object(Bucket="b", Key="whatever/unexpected.jsonl")


def test_local_run_client_upload_file_populates_owned_verified_path(tmp_path):
    rows_path = tmp_path / "originals_all_rows.jsonl"
    rows_path.write_text("{}\n")
    verified_path = tmp_path / "verified_rows.jsonl"
    scratch_dir = tmp_path / "_scratch"
    scratch_dir.mkdir()
    scratch_file = scratch_dir / "verified_rows.jsonl"
    scratch_file.write_text('{"verdict": "success"}\n')

    client = flip_probe._LocalRunClient(
        rows_path=rows_path, verified_path=verified_path,
        rows_filename="all_rows.jsonl", verified_filename="verified_rows.jsonl",
    )
    client.upload_file(str(scratch_file), "b", "whatever/verified_rows.jsonl")

    assert verified_path.read_text() == scratch_file.read_text()

    # And a subsequent get_object now serves it (resume-correct).
    got = client.get_object(Bucket="b", Key="whatever/verified_rows.jsonl")
    assert got["Body"].read() == verified_path.read_bytes()

    with pytest.raises(ValueError):
        client.upload_file(str(scratch_file), "b", "whatever/all_rows.jsonl")


# ---------------------------------------------------------------------------
# _spool_flip_run -- correct destination prefix + originals_rerun/ exclusion
# ---------------------------------------------------------------------------


class _FakeSpoolClient:
    """Records uploads; head_object reports back exactly what was uploaded
    (a passing size-verification path) unless overridden by a subclass."""

    def __init__(self) -> None:
        self.uploaded: dict[str, int] = {}

    def upload_file(self, filename, Bucket, Key):  # boto3's own param casing
        self.uploaded[Key] = Path(filename).stat().st_size

    def head_object(self, Bucket, Key):
        return {"ContentLength": self.uploaded[Key]}


def test_spool_flip_run_excludes_originals_rerun_subtree(tmp_path):
    run_dir = tmp_path / flip_probe.FLIP_RUN_NAME
    (run_dir / "originals_rerun" / "_scratch").mkdir(parents=True)
    (run_dir / "originals_rerun" / "verified_rows.jsonl").write_text("study-derived")
    (run_dir / "originals_rerun" / "_scratch" / "all_rows.jsonl").write_text("study-derived-2")
    (run_dir / "all_rows.jsonl").write_text("flip-own")
    (run_dir / "manifest.json").write_text("flip-own-2")

    client = _FakeSpoolClient()
    n = flip_probe._spool_flip_run(run_dir, client=client)

    assert n == 2
    uploaded_keys = set(client.uploaded)
    assert not any("originals_rerun" in k for k in uploaded_keys)
    assert any(k.endswith("/all_rows.jsonl") for k in uploaded_keys)
    assert any(k.endswith("/manifest.json") for k in uploaded_keys)
    # Correctly-prefixed destination -- the whole point of NOT reusing
    # run_study.spool_to_s3 (see the module docstring's HARD RULE section).
    assert all(k.startswith(f"{flip_probe.SPOOL_PREFIX}/{flip_probe.FLIP_RUN_NAME}/") for k in uploaded_keys)


def test_spool_flip_run_missing_dir_is_a_noop():
    assert flip_probe._spool_flip_run(Path("/nonexistent/definitely/not/a/dir")) == 0


def test_spool_flip_run_raises_on_size_mismatch(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "f.txt").write_text("hello")

    class _BadClient(_FakeSpoolClient):
        def head_object(self, Bucket, Key):
            return {"ContentLength": 999999}

    with pytest.raises(RuntimeError, match="size mismatch"):
        flip_probe._spool_flip_run(run_dir, client=_BadClient())


# ---------------------------------------------------------------------------
# --stage analyze's whitelist-provenance self-check -- end-to-end against a
# tmp_path results tree (SMOLBENCH_LEAN_RESULTS), no AWS client needed since
# both of --stage analyze's required inputs are placed on local disk.
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _stage_analyze_fixture(tmp_path, monkeypatch, *, sample_sha: str,
                           originals_verdict: str = "success",
                           rerun_verdict: str = "success"):
    """A minimal ``--stage analyze`` input tree.

    `originals_verdict` / `rerun_verdict` set the verdict on the one cell row
    of each of the two legs analyze pairs, so a test can plant the ungraded
    sentinel in either leg independently.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_RESULTS", str(tmp_path))
    run_dir = tmp_path / "runs" / flip_probe.FLIP_RUN_NAME
    key = ["m", "T0", 1, "stepk:1", 0]

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "whitelist.json").write_text(json.dumps([key]))
    (run_dir / "sample_manifest.json").write_text(
        json.dumps({"sha256": sample_sha, "n_measurable_mathlib_population": 711})
    )
    _write_jsonl(run_dir / "originals_rerun" / "verified_rows.jsonl", [{
        "kind": "cell", "model": "m", "theorem_id": "T0", "k": 1, "rung": "stepk:1",
        "replicate_idx": 0, "verdict": originals_verdict, "_study_verdict": "success",
        "candidate_proof": "p",
    }])
    _write_jsonl(run_dir / "verified_rows.jsonl", [{
        "kind": "cell", "model": "m", "theorem_id": "T0", "k": 1, "rung": "stepk:1",
        "replicate_idx": 0, "verdict": rerun_verdict, "candidate_proof": "p2",
        "prompt_tokens": 5,
    }])
    return run_dir, key


def test_stage_analyze_provenance_check_passes_on_matching_sha256(tmp_path, monkeypatch):
    from smolbench.deduction.lean import runner

    matching_sha = runner.hash_cell_keys([("m", "T0", 1, "stepk:1", 0)])
    run_dir, _ = _stage_analyze_fixture(tmp_path, monkeypatch, sample_sha=matching_sha)

    flip_probe._stage_analyze(argparse.Namespace())

    report = json.loads((run_dir / "flip_report.json").read_text())
    assert report["n_paired"] == 1
    assert report["sample_whitelist_sha256"] == matching_sha
    assert report["sample_n_measurable_mathlib_population"] == 711


def test_stage_analyze_provenance_check_raises_on_mismatched_sha256(tmp_path, monkeypatch):
    run_dir, _ = _stage_analyze_fixture(tmp_path, monkeypatch, sample_sha="0" * 64)

    with pytest.raises(SystemExit, match="does not match"):
        flip_probe._stage_analyze(argparse.Namespace())

    assert not (run_dir / "flip_report.json").exists()


@pytest.mark.parametrize(
    "leg, filename",
    [("originals", "originals_rerun/verified_rows.jsonl"),
     ("rerun", "verified_rows.jsonl")],
)
def test_stage_analyze_refuses_ungraded_rows_in_either_leg(tmp_path, monkeypatch, leg, filename):
    """An ungraded row must stop the pairing, not be scored as a failure.

    Both legs are re-verified files and neither should ever contain the
    generation-time sentinel; one that does means verification silently
    no-oped for those rows. Pairing them anyway produces a complete flip table
    whose b/c counts are biased by however many rows were never graded -- the
    exact failure mode `flip_free_bound.py`'s own assert exists to prevent.
    """
    from smolbench.deduction.lean import runner

    sha = runner.hash_cell_keys([("m", "T0", 1, "stepk:1", 0)])
    verdicts = {"originals_verdict": "success", "rerun_verdict": "success"}
    verdicts[f"{'originals' if leg == 'originals' else 'rerun'}_verdict"] = "unverified"
    run_dir, _ = _stage_analyze_fixture(tmp_path, monkeypatch, sample_sha=sha, **verdicts)

    with pytest.raises(SystemExit) as excinfo:
        flip_probe._stage_analyze(argparse.Namespace())

    message = str(excinfo.value)
    assert "unverified" in message
    assert "1" in message, "the message must carry the offending row COUNT"
    assert Path(filename).name in message and str(run_dir) in message, (
        "the message must name the offending FILE"
    )
    assert not (run_dir / "flip_report.json").exists()
