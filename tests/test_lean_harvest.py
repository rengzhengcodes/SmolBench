"""Offline tests for scripts/harvest_expert_iter.py and the lean_ec2_sweep.py
changes it depends on (COT_SMOKE_ARMS / the "cot-gate" and "expert-iter"
PHASES entries / --n-rollouts / _resolve_config).

Everything here runs on the main venv with NO network, NO AWS credentials,
and NO real LeanDojo Benchmark 4 download: `corpus.load_split` is
monkeypatched to an in-memory dict (see `lean_corpus_patch`) rather than
pointed at the committed `tests/fixtures/lean_mini` fixture, because the
harvester's "novel_premises/train" lookup has no counterpart in that
fixture (it only ships `random/val.json` -- see test_lean_corpus.py) and
extending the fixture is out of this file's scope. `decontam.HoldoutIndex`
is exercised for real (it is pure, in-memory, deterministic logic), just
built from hand-built `BenchmarkTheorem`s instead of a real split file.

Imports `lean_ec2_sweep`/`harvest_expert_iter` as TOP-LEVEL modules (scripts/
added to sys.path), matching tests/test_lean_capacity_blocks.py's existing
convention for scripts/ modules that are not `pip install`ed.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import harvest_expert_iter as harvest  # noqa: E402  (needs the sys.path insert above)
import lean_ec2_sweep as sweep  # noqa: E402

import smolbench.deduction.lean.corpus as corpus  # noqa: E402
from smolbench.deduction.lean import context, decontam, prompt  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures / builders
# ---------------------------------------------------------------------------


def _theorem(full_name: str, tactics: list[tuple[str, str]]) -> corpus.BenchmarkTheorem:
    """Build a minimal BenchmarkTheorem: `tactics` is [(tactic, state_before), ...]."""
    return corpus.BenchmarkTheorem(
        url="https://github.com/leanprover-community/mathlib4",
        commit="fe4454af900584467d21f4fd4fe951d29d9332a7",
        file_path="Mini/Harvest.lean",
        full_name=full_name,
        start=(1, 1),
        end=(1, 1),
        traced_tactics=[
            corpus.TracedTactic(tactic=tac, state_before=state, state_after="no goals", premises=[])
            for tac, state in tactics
        ],
    )


#: One 2-tactic theorem, k=1 (the last step) is the cell every test below
#: harvests from -- state_before at k=1 mirrors test_lean_decontam.py's
#: THEOREM_A_STEP2_STATE shape (hyps + turnstile goal) so context.render's
#: "Current goal"/"Full tactic state" blocks have realistic content.
THEOREM_A = _theorem(
    "Mini.harvestA",
    [
        ("intro h", "n : ℕ\n⊢ P n → Q n"),
        ("exact fooA h", "n : ℕ\nh : P n\n⊢ Q n"),
    ],
)
THEOREM_A_K = 1  # last traced-tactic index


def _row(
    theorem_id: str,
    k: int,
    rollout_idx: int,
    verdict: str,
    candidate_proof: str = "ring",
    raw_response: str = "",
    reasoning_content=None,
) -> dict:
    """A minimal all_rows.jsonl `kind == "cell"` row -- only the fields
    harvest_expert_iter.py reads (see smolbench.deduction.lean.runner's
    row schema for the full set a real sweep writes)."""
    row = {
        "kind": "cell",
        "theorem_id": theorem_id,
        "k": k,
        "rollout_idx": rollout_idx,
        "verdict": verdict,
        "candidate_proof": candidate_proof,
        "raw_response": raw_response,
    }
    if reasoning_content is not None:
        row["reasoning_content"] = reasoning_content
    return row


@pytest.fixture
def lean_corpus_patch(monkeypatch):
    """Monkeypatch `corpus.load_split` to an in-memory `(kind, split) ->
    [BenchmarkTheorem]` dict, so the harvester's theorem lookup -- and
    everything downstream that also calls `corpus.load_split` through the
    SAME module object (`sft.eval_holdout_names`, `decontam.HoldoutIndex.
    build`) -- reads from it instead of needing the real (not committed)
    LeanDojo Benchmark 4 dataset. Tests populate the returned dict's
    ``("novel_premises", "train"/"val"/"test")`` entries before calling
    anything that triggers a lookup.
    """
    splits: dict[tuple[str, str], list[corpus.BenchmarkTheorem]] = {
        ("novel_premises", "train"): [],
        ("novel_premises", "val"): [],
        ("novel_premises", "test"): [],
    }

    def fake_load_split(kind="random", split="val"):
        return list(splits.get((kind, split), []))

    monkeypatch.setattr(corpus, "load_split", fake_load_split)
    return splits


@pytest.fixture
def isolated_ec2_deploy_specs(monkeypatch):
    """`lean_ec2_sweep._resolve_config` mutates `ec2.EC2_DEPLOY_SPECS` in
    place (registers new LoRA variant entries, flips the Qwen base to its
    BF16 override) -- a real side effect the live driver relies on, but one
    that must NOT leak across tests (or test FILES) sharing this pytest
    process. Swap in a deep copy for the test's duration; `monkeypatch`
    restores the original dict object afterward regardless of pass/fail.
    """
    from smolbench.evals import ec2

    monkeypatch.setattr(ec2, "EC2_DEPLOY_SPECS", copy.deepcopy(ec2.EC2_DEPLOY_SPECS))
    return ec2


# ---------------------------------------------------------------------------
# normalize_proof
# ---------------------------------------------------------------------------


def test_normalize_proof_strips_each_line_but_keeps_blank_lines():
    assert harvest.normalize_proof("  ring  \n\tomega\t") == "ring\nomega"
    # A literal blank line between tactics is preserved (per-line strip
    # only, no collapsing) -- see normalize_proof's docstring.
    assert harvest.normalize_proof("a\n\nb") == "a\n\nb"


# ---------------------------------------------------------------------------
# derive_rationale
# ---------------------------------------------------------------------------


def test_derive_rationale_prefers_reasoning_content_when_truthy():
    row = _row("T", 0, 0, "success", reasoning_content="  because X  ",
                raw_response="<think>other</think>\nring")
    assert harvest.derive_rationale(row) == "because X"


def test_derive_rationale_falls_back_to_raw_response_before_think_close():
    row = _row("T", 0, 0, "success", raw_response="<think>because Y</think>\nring")
    assert harvest.derive_rationale(row) == "because Y"


def test_derive_rationale_missing_reasoning_content_key_falls_back():
    # A non-reasoning-capable provider's row may not even carry the key.
    row = {"raw_response": "<think>because Z</think>ring"}
    assert harvest.derive_rationale(row) == "because Z"


def test_derive_rationale_unclosed_think_is_empty():
    row = _row("T", 0, 0, "success", raw_response="<think>never closes... ring")
    assert harvest.derive_rationale(row) == ""


def test_derive_rationale_no_think_tag_at_all_is_empty():
    row = _row("T", 0, 0, "success", raw_response="just ring, no reasoning shown")
    assert harvest.derive_rationale(row) == ""


def test_derive_rationale_falsy_reasoning_content_falls_back():
    # An empty-string reasoning_content is falsy -- must fall back to
    # raw_response, not be treated as "the rationale is the empty string".
    row = _row("T", 0, 0, "success", reasoning_content="",
                raw_response="<think>because W</think>ring")
    assert harvest.derive_rationale(row) == "because W"


# ---------------------------------------------------------------------------
# wrap_assistant -- style-wrapping exactness (coordination constants)
# ---------------------------------------------------------------------------


def test_wrap_assistant_think_style_exact():
    assistant, used_bare = harvest.wrap_assistant("think", "because X", "ring")
    assert assistant == "<think>\nbecause X\n</think>\n\nring"
    assert used_bare is False


def test_wrap_assistant_fenced_style_exact():
    assistant, used_bare = harvest.wrap_assistant("fenced", "because X", "ring")
    assert assistant == "because X\n\n```lean\nring\n```"
    assert used_bare is False


@pytest.mark.parametrize("style", ["think", "fenced"])
def test_wrap_assistant_empty_rationale_is_bare_for_every_style(style):
    assistant, used_bare = harvest.wrap_assistant(style, "", "ring")
    assert assistant == "ring"
    assert used_bare is True


# ---------------------------------------------------------------------------
# _rationale_has_forbidden_markup (Fix 5: rationale sanitization)
# ---------------------------------------------------------------------------


def test_rationale_markup_gate_passes_clean_prose():
    assert harvest._rationale_has_forbidden_markup("because fooA applies to the local hypothesis") is False
    assert harvest._rationale_has_forbidden_markup("") is False


@pytest.mark.parametrize(
    "bad",
    [
        "contains a ``` fence right here",
        "opens a <think> tag mid-sentence",
        "closes a </think> tag mid-sentence",
    ],
)
def test_rationale_markup_gate_flags_forbidden_tokens(bad):
    assert harvest._rationale_has_forbidden_markup(bad) is True


def test_build_rows_rationale_with_forbidden_markup_degrades_to_bare_and_is_counted():
    """Fix 5: a recovered rationale containing a literal `</think>` (e.g. a
    reasoning-parser artifact, or the model quoting Lean in a code fence)
    must be treated as EMPTY -- not wrapped verbatim, which would close the
    <think> block early and strand the verified tail outside it -- and
    counted under the dedicated `rationale_markup_dropped` counter (which is
    a SUBSET of `empty_rationale_count`, since the row still ends up bare)."""
    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(
                THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h",
                reasoning_content="because fooA applies</think>\nhere it is",
            ),
        ],
    }
    index = decontam.HoldoutIndex.build(eval_specs=[])
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names=set(), index=index,
    )
    assert stats["rationale_markup_dropped"] == 1
    assert stats["empty_rationale_count"] == 1
    (row,) = rows
    assert row["assistant"] == "exact fooA h"  # bare -- no <think> block emitted at all


def test_build_rows_rationale_without_markup_is_wrapped_normally():
    """Non-regression: a clean rationale (no forbidden tokens) is wrapped as
    usual and does NOT increment `rationale_markup_dropped`."""
    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(
                THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h",
                reasoning_content="because fooA applies here directly",
            ),
        ],
    }
    index = decontam.HoldoutIndex.build(eval_specs=[])
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names=set(), index=index,
    )
    assert stats["rationale_markup_dropped"] == 0
    assert stats["empty_rationale_count"] == 0
    (row,) = rows
    assert row["assistant"] == "<think>\nbecause fooA applies here directly\n</think>\n\nexact fooA h"


# ---------------------------------------------------------------------------
# select_candidates -- success filter, easy-at boundary, dedup, max-per-theorem
# ---------------------------------------------------------------------------


def test_select_candidates_success_filter_excludes_non_success_rows():
    groups = {
        ("T", 0): [
            _row("T", 0, 0, "success", "ring"),
            _row("T", 0, 1, "lean_error", "bogus"),
            _row("T", 0, 2, "exception", "bogus2"),
        ],
    }
    kept, stats = harvest.select_candidates(
        groups, easy_at=0.99, min_successes=1, max_per_theorem=5, seed=1
    )
    assert [r["candidate_proof"] for r in kept[("T", 0)]] == ["ring"]
    assert stats["candidates_considered"] == 1


def test_select_candidates_easy_at_boundary_is_inclusive():
    # 3/4 == 0.75 -> dropped (>=).
    at_threshold = {
        ("T", 0): (
            [_row("T", 0, i, "success", f"p{i}") for i in range(3)]
            + [_row("T", 0, 3, "lean_error")]
        ),
    }
    kept, stats = harvest.select_candidates(
        at_threshold, easy_at=0.75, min_successes=1, max_per_theorem=5, seed=1
    )
    assert kept == {}
    assert stats["groups_easy_filtered"] == 1
    assert stats["groups_kept"] == 0

    # 3/6 == 0.5 < 0.75 -> kept.
    under_threshold = {
        ("T", 0): (
            [_row("T", 0, i, "success", f"p{i}") for i in range(3)]
            + [_row("T", 0, j, "lean_error") for j in range(3, 6)]
        ),
    }
    kept2, stats2 = harvest.select_candidates(
        under_threshold, easy_at=0.75, min_successes=1, max_per_theorem=5, seed=1
    )
    assert list(kept2) == [("T", 0)]
    assert stats2["groups_easy_filtered"] == 0
    assert stats2["groups_kept"] == 1


def test_select_candidates_min_successes_drops_thin_evidence():
    groups = {("T", 0): [_row("T", 0, 0, "success", "ring")]}
    kept, stats = harvest.select_candidates(
        groups, easy_at=0.99, min_successes=2, max_per_theorem=5, seed=1
    )
    assert kept == {}
    assert stats["groups_insufficient_successes"] == 1


def test_select_candidates_dedup_normalizes_whitespace_keeps_first_by_rollout():
    groups = {
        ("T", 0): [
            _row("T", 0, 0, "success", "  ring  "),
            _row("T", 0, 1, "success", "ring"),  # same normalized text
            _row("T", 0, 2, "success", "omega"),  # distinct
        ],
    }
    # easy_at=2.0: a ratio no real success rate (max 1.0) can reach, so the
    # difficulty gate never fires -- this test isolates dedup, not the gate
    # (an all-success group would otherwise be its own "too easy" fixture).
    kept, stats = harvest.select_candidates(
        groups, easy_at=2.0, min_successes=1, max_per_theorem=5, seed=1
    )
    proofs = sorted(r["candidate_proof"] for r in kept[("T", 0)])
    # The canonical row for the "ring" dup keeps its ORIGINAL (unnormalized)
    # text -- normalize_proof is a dedup key only, not a rewrite.
    assert proofs == ["  ring  ", "omega"]
    assert stats["candidates_deduped"] == 2
    assert stats["candidates_considered"] == 3


def test_select_candidates_max_per_theorem_caps_and_is_seed_deterministic():
    groups = {("T", 0): [_row("T", 0, i, "success", f"proof{i}") for i in range(5)]}
    # easy_at=2.0: see the dedup test above -- isolates the cap/sample logic
    # from the (all-success) fixture's own difficulty rate.
    kept1, stats1 = harvest.select_candidates(
        groups, easy_at=2.0, min_successes=1, max_per_theorem=2, seed=42
    )
    kept2, stats2 = harvest.select_candidates(
        groups, easy_at=2.0, min_successes=1, max_per_theorem=2, seed=42
    )
    assert stats1["candidates_deduped"] == 5
    assert stats1["candidates_sampled"] == 2
    assert len(kept1[("T", 0)]) == 2
    # Same seed over the same input -> the exact same sample, every time.
    assert [r["rollout_idx"] for r in kept1[("T", 0)]] == [r["rollout_idx"] for r in kept2[("T", 0)]]


# ---------------------------------------------------------------------------
# build_rows -- rendering, meta shape, theorem-not-found, holdout-name drop,
# content-level decontam drop
# ---------------------------------------------------------------------------


def test_build_rows_emits_expected_shape_and_wraps_with_rationale():
    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h",
                 reasoning_content="because fooA applies here"),
        ],
    }
    index = decontam.HoldoutIndex.build(eval_specs=[])  # trivially empty holdout
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="lean_expert_iter",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names=set(), index=index,
    )
    assert stats == {
        "theorem_not_found": 0, "eval_holdout_name_hits": 0,
        "empty_rationale_count": 0, "rationale_markup_dropped": 0,
        "dropped": {}, "emitted": 1,
    }
    (row,) = rows
    assert set(row) == {"system", "user", "assistant", "meta"}
    assert row["system"] == prompt.SYSTEM
    assert row["user"] == prompt.build_user_prompt(
        context.render(THEOREM_A, THEOREM_A_K, "stepk", 1)
    )
    assert row["assistant"] == "<think>\nbecause fooA applies here\n</think>\n\nexact fooA h"
    assert row["meta"] == {
        "full_name": THEOREM_A.full_name, "k": THEOREM_A_K, "n_tail": 1,
        "source_run": "lean_expert_iter", "rollout_idx": 0,
    }


def test_build_rows_empty_rationale_counted_and_bare():
    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h"),
        ],
    }
    index = decontam.HoldoutIndex.build(eval_specs=[])
    rows, stats = harvest.build_rows(
        kept, style="fenced", run_name="r",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names=set(), index=index,
    )
    assert stats["empty_rationale_count"] == 1
    assert rows[0]["assistant"] == "exact fooA h"  # bare -- no fence, no rationale


def test_build_rows_holdout_name_drop():
    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h"),
        ],
    }
    index = decontam.HoldoutIndex.build(eval_specs=[])
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names={THEOREM_A.full_name},  # name-based holdout hit
        index=index,
    )
    assert rows == []
    assert stats["eval_holdout_name_hits"] == 1
    assert stats["emitted"] == 0


def test_build_rows_theorem_not_found_is_skipped_not_raised():
    kept = {("Mini.missing", 0): [_row("Mini.missing", 0, 0, "success", "ring")]}
    index = decontam.HoldoutIndex.build(eval_specs=[])
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r", theorem_by_name={},
        holdout_names=set(), index=index,
    )
    assert rows == []
    assert stats["theorem_not_found"] == 1


def test_build_rows_content_level_decontam_drops_state_match():
    # A differently-NAMED eval theorem whose own step state is byte-identical
    # to THEOREM_A's k=1 state -- a content-level restatement the K1 name
    # check alone would miss.
    eval_leak = _theorem("Mini.evalLeak", [("some_eval_tactic", "n : ℕ\nh : P n\n⊢ Q n")])
    index = decontam.HoldoutIndex()
    index._add_theorem(eval_leak)

    kept = {
        (THEOREM_A.full_name, THEOREM_A_K): [
            _row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h"),
        ],
    }
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r",
        theorem_by_name={THEOREM_A.full_name: THEOREM_A},
        holdout_names=set(), index=index,
    )
    assert rows == []
    # Fix 3: build_rows now also passes statement=states[0] to index.check.
    # eval_leak has exactly ONE tactic, so its state_before double-indexes
    # as BOTH the K2 statement (traced_tactics[0]) AND a K3 state (the same
    # tactic, iterated again by the all-steps loop) -- and HoldoutIndex.check
    # evaluates the `statement=` branch (which finds the K2 exact hit)
    # BEFORE the separate `states=` sweep, so hits[0] is now "statement",
    # not "state". Either way the row is still dropped -- confirmed
    # empirically against the real HoldoutIndex.check ordering, not just by
    # inspection.
    assert stats["dropped"] == {"statement": 1}
    assert stats["emitted"] == 0


def test_build_rows_content_level_decontam_near_dup_statement_hit():
    """Fix 3: passing `statement=states[0]` (not just `states=`) reaches the
    K2 NEAR-DUPLICATE (MinHash/LSH) family, which a plain `states=` exact
    sweep never reaches at all. Plant an eval theorem whose STEP-0 state is
    an alpha-rename (one hypothesis renamed) of the harvested row's own k=1
    state -- long enough for shingle overlap to survive the rename, per
    tests/test_lean_decontam.py's `test_k2_near_duplicate_alpha_rename_hit`
    (the identical recipe, proven there to clear the 0.85 Jaccard
    threshold). An EXACT `states=` sweep alone would find nothing here (the
    text differs) -- only the near-dup family catches it.
    """
    long_stmt = (
        "F : Type u_1\ninst : Field F\ns t : Set F\nm : F ≃+* F\n"
        "hs : s ⊆ Set.range ↑m\nht : t ⊆ Set.range ↑m\n⊢ s / t ⊆ Set.range ↑m"
    )
    renamed = long_stmt.replace("hs :", "h1 :")

    theorem_long = _theorem(
        "Mini.harvestLong",
        [
            ("intro h1 ht", "F : Type u_1\ninst : Field F\n⊢ True"),  # k=0, unused filler
            ("simp", renamed),  # k=1 -- what build_rows will re-render and derive states[0] from
        ],
    )
    theorem_long_k = 1

    eval_near_dup = _theorem("Mini.evalNearDupSource", [("some_eval_tactic", long_stmt)])
    index = decontam.HoldoutIndex()
    index._add_theorem(eval_near_dup)

    kept = {
        (theorem_long.full_name, theorem_long_k): [
            _row(theorem_long.full_name, theorem_long_k, 0, "success", "field_simp"),
        ],
    }
    rows, stats = harvest.build_rows(
        kept, style="think", run_name="r",
        theorem_by_name={theorem_long.full_name: theorem_long},
        holdout_names=set(), index=index,
    )
    assert rows == []
    assert stats["dropped"] == {"statement_near": 1}
    assert stats["emitted"] == 0


# ---------------------------------------------------------------------------
# End-to-end: build(args) -> output JSONL + manifest
# ---------------------------------------------------------------------------


def _write_all_rows(run_dir: Path, rows: list[dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "all_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_load_cell_rows_missing_file_raises_actionable_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="expert-iter"):
        harvest.load_cell_rows(tmp_path / "nope")


def test_load_cell_rows_skips_non_cell_and_malformed_lines(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "all_rows.jsonl").write_text(
        json.dumps({"kind": "sanity", "theorem_id": "T", "verdict": "success"}) + "\n"
        + "{not json\n"
        + json.dumps(_row("T", 0, 0, "success", "ring")) + "\n"
    )
    rows = harvest.load_cell_rows(run_dir)
    assert len(rows) == 1 and rows[0]["theorem_id"] == "T"


def test_build_end_to_end_manifest_counts_and_output_file(tmp_path, lean_corpus_patch):
    lean_corpus_patch[("novel_premises", "train")] = [THEOREM_A]
    # val/test stay empty -> a trivially empty eval holdout; nothing should
    # be decontam-dropped in this run (that path is covered directly by
    # test_build_rows_content_level_decontam_drops_state_match above).

    run_dir = tmp_path / "runs" / "lean_expert_iter"
    rows = (
        # 3 successes: two dedup to one distinct proof, one distinct + bare
        # (no think tag -> empty rationale).
        [_row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h",
              raw_response="<think>because fooA</think>\nexact fooA h")]
        + [_row(THEOREM_A.full_name, THEOREM_A_K, 1, "success", "  exact fooA h  ",
                raw_response="<think>because fooA again</think>\nexact fooA h")]
        + [_row(THEOREM_A.full_name, THEOREM_A_K, 2, "success", "simp")]  # bare
        # 5 failures -> total 8 rollouts, success rate 3/8 = 0.375 < 0.75.
        + [_row(THEOREM_A.full_name, THEOREM_A_K, i, "lean_error", "bogus") for i in range(3, 8)]
    )
    _write_all_rows(run_dir, rows)

    args = harvest.build_parser().parse_args(
        ["--run-dir", str(run_dir), "--out", str(tmp_path / "out" / "harvest.jsonl"), "--style", "think"]
    )
    manifest_path, manifest = harvest.build(args)

    s = manifest["stats"]
    assert s["total_cell_rows"] == 8
    assert s["groups_total"] == 1
    assert s["groups_insufficient_successes"] == 0
    assert s["groups_easy_filtered"] == 0
    assert s["groups_kept"] == 1
    assert s["candidates_considered"] == 3
    assert s["candidates_deduped"] == 2  # "exact fooA h" (deduped) + "simp"
    assert s["candidates_sampled"] == 2  # under the default --max-per-theorem 2
    assert s["theorem_not_found"] == 0
    assert s["eval_holdout_name_hits"] == 0
    assert s["dropped"] == {}
    assert s["dropped_total"] == 0
    assert s["empty_rationale_count"] == 1  # the "simp" rollout
    assert s["rationale_markup_dropped"] == 0  # neither rationale here has forbidden markup
    assert s["emitted"] == 2

    assert manifest["config"]["run_dir"] == str(run_dir)
    assert manifest["config"]["style"] == "think"
    assert manifest_path == args.out.with_name(args.out.stem + ".manifest.json")
    assert manifest_path.exists()

    out_rows = [json.loads(line) for line in args.out.read_text().splitlines()]
    assert len(out_rows) == 2
    assert {r["meta"]["source_run"] for r in out_rows} == {"lean_expert_iter"}
    assistants = {r["assistant"] for r in out_rows}
    assert "<think>\nbecause fooA\n</think>\n\nexact fooA h" in assistants
    assert "simp" in assistants  # bare -- no rationale was recoverable


def test_build_asserts_on_eval_holdout_contamination(tmp_path, lean_corpus_patch):
    # The theorem is (incorrectly) present in BOTH the train pool AND the
    # eval holdout -- simulates an upstream bug (a sweep run against
    # val/test theorems). build() must hard-fail rather than silently drop.
    lean_corpus_patch[("novel_premises", "train")] = [THEOREM_A]
    lean_corpus_patch[("novel_premises", "val")] = [THEOREM_A]

    run_dir = tmp_path / "runs" / "lean_expert_iter"
    # A failure row keeps the success rate (1/2 = 0.5) under the default
    # --easy-at 0.75 gate, so the cell survives select_candidates and the
    # contamination check in build_rows is what's actually exercised here
    # -- an all-success single row would be dropped as "too easy" first.
    _write_all_rows(run_dir, [
        _row(THEOREM_A.full_name, THEOREM_A_K, 0, "success", "exact fooA h"),
        _row(THEOREM_A.full_name, THEOREM_A_K, 1, "lean_error", "bogus"),
    ])

    args = harvest.build_parser().parse_args(
        ["--run-dir", str(run_dir), "--out", str(tmp_path / "out.jsonl")]
    )
    with pytest.raises(AssertionError, match="contamination"):
        harvest.build(args)


# ---------------------------------------------------------------------------
# lean_ec2_sweep.py: PHASES shape, --n-rollouts, --cot-smoke, _resolve_config
# ---------------------------------------------------------------------------


def test_expert_iter_phase_sources_with_proof_not_replay_passing():
    # The replay_passing sidecar is never generated for train -- see the
    # PHASES["expert-iter"] comment; with_proof needs no sidecar.
    phase = sweep.PHASES["expert-iter"]
    assert phase["theorems"]["source"] == "with_proof"
    assert phase["theorems"]["kind"] == "novel_premises"
    assert phase["theorems"]["split"] == "train"
    assert phase["rungs"] == ["stepk:1"]
    assert phase["n_rollouts"] == 8


def test_cot_gate_phase_shape():
    phase = sweep.PHASES["cot-gate"]
    assert phase["theorems"]["source"] == "replay_passing"
    assert phase["theorems"]["split"] == "val"
    assert phase["n_rollouts"] == 8
    assert phase["rungs"] == ["stepk:1", "hint:2", "noise:3", "hint:3"]


def test_n_rollouts_override_plumbs_into_resolved_config(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(
        ["--phase", "expert-iter", "--n-rollouts", "3", "--only", "qwen3-235b-a22b"]
    )
    config, variants, run_dir = sweep._resolve_config(args)
    assert config["n_rollouts"] == 3
    assert run_dir.name == "lean_expert_iter"
    assert [v["key"] for v in variants] == ["qwen3-235b-a22b"]


def test_n_rollouts_not_set_leaves_phase_default(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "expert-iter", "--only", "qwen3-235b-a22b"])
    config, _variants, _run_dir = sweep._resolve_config(args)
    assert config["n_rollouts"] == 8  # PHASES["expert-iter"]'s own default, untouched


def test_lora_rank_defaults_to_16_without_cot_smoke(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "pilot"])
    sweep._resolve_config(args)
    assert args.lora_rank == 16


def test_lora_rank_defaults_to_128_with_cot_smoke(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "cot-gate", "--cot-smoke"])
    sweep._resolve_config(args)
    assert args.lora_rank == 128


def test_lora_rank_explicit_value_is_not_overridden(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "cot-gate", "--cot-smoke", "--lora-rank", "64"])
    sweep._resolve_config(args)
    assert args.lora_rank == 64


def test_cot_smoke_variants_and_deploy_spec_s3_subprefixes(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "cot-gate", "--cot-smoke"])
    config, variants, _run_dir = sweep._resolve_config(args)

    assert [v["key"] for v in variants] == [
        "qwen3-235b-a22b", "qwen3-lean-real", "qwen3-lean-bare-r128", "qwen3-lean-cot-r128",
    ]
    assert variants[0]["display"] == "qwen3-235b-a22b-base"

    specs = isolated_ec2_deploy_specs.EC2_DEPLOY_SPECS
    assert specs["qwen3-lean-bare-r128"]["adapters"][0]["s3"].endswith(
        "qwen3-235b-a22b/bare8k-r128"
    )
    assert specs["qwen3-lean-cot-r128"]["adapters"][0]["s3"].endswith(
        "qwen3-235b-a22b/cot8k-r128"
    )
    assert specs["qwen3-lean-real"]["adapters"][0]["s3"].endswith("qwen3-235b-a22b/real-only")
    # --cot-smoke's resolved rank (128) reaches the served --max-lora-rank.
    assert "128" in specs["qwen3-lean-cot-r128"]["vllm_args"]
    # BF16 override applies here too (same constraint as the trio's Qwen arm).
    assert specs["qwen3-235b-a22b"]["hf_model_id"] == "Qwen/Qwen3-235B-A22B"
    assert specs["qwen3-235b-a22b"]["max_model_len"] == 40960


def test_qwen_4way_and_cot_smoke_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        sweep.build_parser().parse_args(["--qwen-4way", "--cot-smoke"])


def test_limit_override_still_overrides_theorem_count(isolated_ec2_deploy_specs):
    # Non-regression: --limit predates this change and must keep working
    # once config-resolution moved into _resolve_config.
    args = sweep.build_parser().parse_args(
        ["--phase", "pilot", "--limit", "1", "--only", "qwen3-235b-a22b"]
    )
    config, variants, _run_dir = sweep._resolve_config(args)
    assert config["theorems"]["limit"] == 1
    assert [v["key"] for v in variants] == ["qwen3-235b-a22b"]


def test_only_filter_raises_when_nothing_matches(isolated_ec2_deploy_specs):
    args = sweep.build_parser().parse_args(["--phase", "pilot", "--only", "not-a-real-key"])
    with pytest.raises(SystemExit):
        sweep._resolve_config(args)


def test_only_filter_error_lists_resolved_variant_keys_not_bare_trio(isolated_ec2_deploy_specs):
    """Fix 6: the --only mismatch error must interpolate the ACTUAL resolved
    variant keys, not the raw `TRIO` constant -- `_variants` (the default,
    non-qwen-4way/non-cot-smoke arm list) also emits each base's
    `<key>-lean-lora` variant, which bare `TRIO` doesn't name at all."""
    args = sweep.build_parser().parse_args(["--phase", "pilot", "--only", "not-a-real-key"])
    with pytest.raises(SystemExit, match=r"llama-31-405b-lean-lora"):
        sweep._resolve_config(args)


def test_only_filter_error_under_cot_smoke_lists_cot_smoke_keys_not_trio(isolated_ec2_deploy_specs):
    """Under --cot-smoke, the resolved variant list is COT_SMOKE_ARMS's
    qwen3-lean-* keys -- TRIO's dense-model keys (llama-31-405b,
    nemotron-ultra-253b) are not even candidates and must not appear in the
    error message."""
    args = sweep.build_parser().parse_args(
        ["--phase", "cot-gate", "--cot-smoke", "--only", "not-a-real-key"]
    )
    with pytest.raises(SystemExit) as exc_info:
        sweep._resolve_config(args)
    msg = str(exc_info.value)
    assert "qwen3-lean-cot-r128" in msg
    assert "llama-31-405b" not in msg
    assert "nemotron-ultra-253b" not in msg
