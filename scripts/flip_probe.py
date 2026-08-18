"""Score-level flip experiment: how much does a serving PROCESS change change
a lane's headline?

WHY THIS EXISTS
---------------
``notebooks/DETERMINISM_PLAN_2026-08-16.md`` section 6.2 specifies this
measurement; read it first. In brief: the family-ladder deduction study's
only "noise floor" so far is a BYTE-agreement number (0/8 or 8/8 on 8
prompts, bimodal, see the plan's section 0) -- not a score-level term. The
paper needs the latter: *given the same cells, how much does the headline
pass@1 metric move when the serving process changes?*

Design (plan §6.2): take ``nemotron-3-nano-4b`` -- "the only lane in the
study whose deduction cells all come from a single serving process" -- draw
a random n=200-cell sample from its measurable population, regenerate
EXACTLY those cells on one fresh box, grade both the rerun and a fresh
re-verification of the ORIGINAL candidates through the SAME (today's)
verifier, and report the paired discordance rate (McNemar b+c over n) with
an exact binomial (Clopper-Pearson) 95% CI, plus a verifier-drift sanity
check (re-verified originals vs. the study's own stored verdicts).

THIS SCRIPT builds the driver + filter + analysis. It never provisions EC2,
never calls a model, and never writes to S3 itself when this module is
merely IMPORTED -- ``--stage generate``/``--stage verify`` are LIVE and are
meant to be invoked by an operator (or an orchestrating agent) on real
infrastructure, not run as a side effect of importing or testing this file.

STAGES (``--stage {sample,generate,verify,analyze}``)
-------------------------------------------------------
``sample``   Offline except for one READ-ONLY S3 GET. Downloads the study
             lane's ``verified_rows.jsonl``, restricts to the MATHLIB-ONLY
             measurable population (see "Sample-stage population" below),
             draws n=200 via ``random.Random(0)`` over the SORTED population,
             and writes ``whitelist.json`` + ``sample_manifest.json``.

``generate`` LIVE EC2 spend. Sets this experiment's own env (tag, state
             file, run name, ``LEAN_CELL_WHITELIST``), reconstructs the
             STUDY-ERA ("stock") ``vllm_args`` for this model (undoing the
             2026-08-18 determinism-bundle default -- see "Stock
             reconstruction" below), and runs the SAME
             ``notebooks/deduction/run_study.py`` machinery the study itself
             uses for exactly this one model, restricted to the whitelisted
             200 cells. Tears its box down in a ``finally``, then spools the
             run to S3 under this experiment's OWN prefix.

``verify``   LIVE Lean/Dojo work; needs ``.venv-lean``. Two legs, both via
             ``scripts/lean_verify_rows.py``'s ``verify_run`` (imported, not
             subprocessed -- see "Why import, not subprocess" below):
             (a) verifies the flip run's own freshly generated rows (normal
             S3 round-trip, permitted under its own prefix); (b) fetches the
             study's ORIGINAL candidate rows for exactly the 200 whitelisted
             cells READ-ONLY, and re-verifies them in a LOCAL-ONLY
             ``originals_rerun/`` directory -- see the HARD RULE below for
             why this leg never touches S3 at all.

``analyze``  Offline. Pairs each of the 200 cells' re-verified-original
             verdict against its rerun verdict (the primary, cross-PROCESS
             comparison -- both sides graded by today's verifier, so
             verifier-version drift cannot leak into it), computes McNemar
             b/c/discordance/Clopper-Pearson-CI/implied-SE, and separately
             checks the re-verified originals against the study's OWN stored
             verdicts (a verifier-drift sanity check, not the headline).
             Writes ``flip_report.json``.  MUST run on the same machine (or
             filesystem) that ``--stage verify`` ran on, for leg (b)'s data
             -- see the HARD RULE below.

HARD RULE -- no write of any kind under the study's ``scaling_*`` S3
prefixes, ever
-------------------------------------------------------------------------
The study's own results (``s3://<SPOOL_BUCKET>/<SPOOL_PREFIX>/scaling_*/``)
are read-only from this script's point of view. This experiment's OWN data
lives under a SEPARATE ``flip_*`` prefix, which spooling to S3 IS permitted
for (that is "what run_study does anyway", per this task's brief). Two
consequences that shaped this file's design:

1. ``notebooks/deduction/run_study.py``'s own ``spool_to_s3`` is
   DELIBERATELY NOT reused for the ``generate`` stage's upload: that
   function hardcodes its destination as ``f"{SPOOL_PREFIX}/scaling_{key}/"``
   -- literally the study's own prefix, regardless of what run directory it
   is pointed at. Calling it with ``key="nemotron-3-nano-4b"`` would spool
   this experiment's freshly generated rows ON TOP OF the live study data.
   ``_spool_flip_run`` below is a small, independent, correctly-prefixed
   replacement (upload + ``head_object`` size verification, no pruning --
   see that function's docstring for why not pruning is the right call
   here).
2. ``--stage verify``'s leg (b) (re-verifying the study's ORIGINAL
   candidates) downloads from the study's S3 prefix via a plain, read-only
   ``get_object`` and then drives ``lean_verify_rows.verify_run`` through
   ``_LocalRunClient`` -- a fake S3 client backed by two local files, so it
   is STRUCTURALLY IMPOSSIBLE for that leg to write anything to real S3 at
   all (see ``_LocalRunClient``'s own docstring).

Sample-stage population: Mathlib-only, exactly 711 cells (2026-08-18
spec amendment)
-------------------------------------------------------------------------
The original brief said "identify measurable cells... expect ~711". A
concurrent workstream is recovering Std-theorem (not Mathlib) cell verdicts
into this SAME lane's ``verified_rows.jsonl``, which would silently GROW the
measurable population -- and change its membership -- depending on exactly
when ``--stage sample`` runs relative to that recovery landing. The §6.2
estimand is the STUDY-ERA MATHLIB-measurable population specifically, so
``measurable_cell_keys`` excludes any cell whose theorem ``file_path`` is
under ``.lake/packages/std/`` (see ``is_mathlib_cell``), and
``assert_population_size`` is a HARD gate: the sample stage raises loudly
(never silently samples a shifted population) if the count is not exactly
711.

Stock reconstruction
---------------------
Every ``EC2_DEPLOY_SPECS`` entry now ends with ``ec2.DETERMINISM_ARGS`` (the
2026-08-18 hinge-certified determinism bundle -- see
``notebooks/DETERMINISM_PLAN_2026-08-16.md`` §3-4 and
``smolbench/evals/ec2.py``'s own module-level assembly loop). The study
lane this experiment reruns predates that default and was generated under
the STOCK configuration (``--enable-prefix-caching``, no determinism
bundle). ``stock_vllm_args`` reconstructs that stock argv, byte-identical to
``scripts/hinge_probe.py``'s own inline reconstruction (~lines 201-215 as of
the determinism-default commit) -- copied here as a standalone, unit-tested
pure function rather than re-derived. Getting this wrong would confound the
measurement: cross-CONFIG agreement (stock vs. determinism-bundle) is
independently ALREADY measured at 0/8 (plan §3, "Cross-config is 0/8 on BOTH
models") -- generating the rerun under the wrong config would measure that
known effect instead of cross-process variation.

Why import, not subprocess, for ``--stage verify``
-----------------------------------------------------
``lean_verify_rows._dojo_cache_lock`` is an EXCLUSIVE, non-blocking
``flock`` that raises ``SystemExit`` on contention (concurrent passes race
on the shared traced-repo build cache). Spawning
``scripts/lean_verify_rows.py`` as a subprocess while this process ALSO
needs to drive Dojo (for leg (b)) would contend for that same lock across
two processes. Importing ``lean_verify_rows`` and calling ``verify_run``
directly for BOTH legs, inside ONE shared ``_dojo_cache_lock()`` context,
removes the hazard entirely and makes "both sides graded by the SAME
verifier" literally true (the same module object, in the same process).

Duplicate cell keys: EARLIEST-wins
------------------------------------
``scaling_nemotron-3-nano-4b`` is known to carry more than one surviving row
for some cell keys (a resampling-bug artifact -- see
``smolbench/deduction/lean/runner.py``'s ``_existing_keys`` docstring, and
independently, ``scripts/lean_verify_rows.py``'s own ``--no-resume`` comment
noting this exact lane "had had all 944 of its cells regenerated").
``dedupe_rows_earliest_wins`` resolves any duplicate by keeping the FIRST
occurrence in file order -- the study's own live ruling for this class of
duplicate ("EARLIEST-wins both legs"), applied here for consistency with
how the rest of this study's data was resolved.

Streaming transport: left OFF, a flagged (not resolved) decision
---------------------------------------------------------------------
``scripts/hinge_probe.py`` enables ``EC2_STREAM_COMPLETIONS=1`` because a
capped-length response can otherwise vanish on the wire (plan §1.3's
delivery fault). This experiment's cells run at ``max_tokens=32768`` --
squarely in that fault's regime -- but the STUDY's own original generation
did NOT use streaming, and this task's brief is explicit: "Generation params
are whatever run_study already does -- change nothing." So streaming is left
UNSET here too, and ``--stage analyze`` instead REPORTS the count of rerun
cells with an empty ``candidate_proof`` (split by whether ``prompt_tokens``
was nonzero, the fault's own signature) so a contaminated flip rate is
VISIBLE in the report rather than silently baked into the headline. This is
a decision worth an operator's attention, not a silent one.

USAGE
-----
::

    set -a && source notebooks/deduction/keys.env && source notebooks/ec2-operator.env && set +a

    .venv/bin/python scripts/flip_probe.py --stage sample
    .venv/bin/python scripts/flip_probe.py --stage generate
    .venv-lean/bin/python scripts/flip_probe.py --stage verify
    .venv/bin/python scripts/flip_probe.py --stage analyze

Writes under
``notebooks/deduction/results/runs/flip_nemotron-3-nano-4b/``:
``whitelist.json``, ``sample_manifest.json``, ``originals_rerun/`` (local
only -- see the HARD RULE), ``flip_report.json``, plus everything
``runner.sweep``/``lean_verify_rows.verify_run`` themselves write there
(``all_rows.jsonl``, ``verified_rows.jsonl``, ``manifest.json``,
``server_config.yaml``, ``theorems/``).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import math
import os
import random
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from smolbench.deduction.lean import runner

# ---------------------------------------------------------------------------
# Constants (fixed decisions -- see the module docstring's STAGES section)
# ---------------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[1]

#: The one lane this whole script is hardcoded to -- see the module
#: docstring's "WHY THIS EXISTS" section for why this model specifically.
MODEL: str = "nemotron-3-nano-4b"
STUDY_RUN_NAME: str = f"scaling_{MODEL}"
FLIP_RUN_NAME: str = f"flip_{MODEL}"

EC2_TAG: str = f"flip-{MODEL}"
EC2_STATE_FILE_NAME: str = f".ec2_state_flip_{MODEL}.json"
EC2_REQUIRE_GPU: str = "L40S:1"
EC2_INSTANCE_TYPE: str = "g6e.4xlarge"

#: Same bucket/region/prefix as `notebooks/deduction/run_study.py`'s own
#: SPOOL_BUCKET/SPOOL_REGION/SPOOL_PREFIX -- this study's whole S3 footprint
#: lives in one bucket. Kept as plain literals (not imported), mirroring
#: that file's own precedent for SPOOL_PREFIX (see its docstring): this
#: script owns its own spool contract end to end rather than depending on
#: another module's "off-limits" internals for a value this stable.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
SPOOL_REGION: str = "us-west-2"
SPOOL_PREFIX: str = "deduction/runs"

#: Matches `scripts/lean_verify_rows.py`'s own `VERIFIED_FILENAME` constant
#: value. Duplicated here (rather than importing that module at this file's
#: TOP level) so `sample`/`analyze` -- which need only this one literal, not
#: any of that module's Lean/Dojo-adjacent machinery -- stay light to import
#: (see the module docstring's design note on `--stage verify`).
VERIFIED_FILENAME: str = "verified_rows.jsonl"

#: Sample design (locked; see notebooks/DETERMINISM_PLAN_2026-08-16.md §6.2
#: "Sample size" and the 2026-08-18 spec amendment in this file's docstring).
N_SAMPLE: int = 200
SAMPLE_SEED: int = 0
#: Exact Mathlib-only measurable population size this experiment's estimand
#: is fixed to -- see the module docstring's "Sample-stage population"
#: section. A HARD gate, not an expectation: `assert_population_size` raises
#: on any other count.
EXPECTED_MATHLIB_POPULATION: int = 711

#: Theorem `file_path` marker for a Std (not Mathlib) theorem -- see
#: `is_mathlib_cell`.
_STD_PACKAGE_MARKER: str = ".lake/packages/std/"


def _flip_run_dir() -> Path:
    """This experiment's local run directory, resolved at CALL time.

    Built from `runner.results_root()` (which itself honors
    `SMOLBENCH_LEAN_RESULTS` at call time, never import time) rather than a
    frozen module-level constant, so a caller (or a test) that overrides
    that environment variable before calling any stage function gets a
    consistent answer everywhere in this file.
    """
    return runner.results_root() / "runs" / FLIP_RUN_NAME


def _whitelist_path() -> Path:
    return _flip_run_dir() / "whitelist.json"


def _sample_manifest_path() -> Path:
    return _flip_run_dir() / "sample_manifest.json"


def _originals_dir() -> Path:
    return _flip_run_dir() / "originals_rerun"


def _flip_report_path() -> Path:
    return _flip_run_dir() / "flip_report.json"


# ---------------------------------------------------------------------------
# Pure helpers -- unit-testable with no AWS, no Lean, no network.
# ---------------------------------------------------------------------------


def stock_vllm_args(spec_args: Sequence[str], determinism_args: Sequence[str]) -> list[str]:
    """Reconstructs a spec's pre-determinism-bundle ("stock") ``vllm_args``.

    See the module docstring's "Stock reconstruction" section for WHY this
    experiment needs the study-era config rather than today's default.
    Byte-identical to ``scripts/hinge_probe.py``'s own inline reconstruction
    (as of the 2026-08-18 determinism-default commit), factored into a
    standalone pure function here so it is unit-testable with plain lists --
    calling it must not require importing ``smolbench.evals.ec2`` (which
    freezes its ``EC2_*`` module constants from the process environment the
    moment it is FIRST imported; a test that triggers that import merely to
    check a list-slicing operation would risk polluting later tests in this
    same interpreter with whatever ``EC2_*`` values happened to be set at
    that moment).

    Parameters
    ----------
    spec_args : Sequence[str]
        A spec's current ``vllm_args``, e.g.
        ``ec2.EC2_DEPLOY_SPECS[model]["vllm_args"]``.
    determinism_args : Sequence[str]
        The determinism-bundle suffix to detect and strip, e.g.
        ``ec2.DETERMINISM_ARGS``.

    Returns
    -------
    list[str]
        A NEW list (never `spec_args` itself, never a view into it):
        `spec_args` with the trailing `determinism_args` suffix removed (if
        present) -- or, for a pre-determinism-bundle spec shape, with any
        bare ``--enable-prefix-caching`` flag removed instead -- followed by
        exactly one ``--enable-prefix-caching`` flag.

    Notes
    -----
    Detects the suffix by direct list comparison (``spec_args[-n:] ==
    list(determinism_args)``), not by scanning for individual flags: the
    determinism bundle's flags could, in principle, appear elsewhere in a
    spec for an unrelated reason, and a suffix match is the same test
    ``smolbench/evals/ec2.py``'s own module-level assembly loop uses to
    prove every spec carries the bundle at all. Guards ``n == 0`` explicitly
    (unlike a literal negative-slice reading, ``spec_args[-0:]`` is the
    WHOLE list, which would otherwise compare it against an empty
    `determinism_args` and almost always fail to match) -- purely a
    defensive edge case for testability; `determinism_args` is always the
    fixed 6-element ``ec2.DETERMINISM_ARGS`` bundle in production use.
    """
    spec_args = list(spec_args)
    determinism_args = list(determinism_args)
    n = len(determinism_args)
    if n and spec_args[-n:] == determinism_args:
        base_args = spec_args[:-n]
    else:  # pre-determinism-bundle spec shape: strip the study-era flag directly
        base_args = [a for a in spec_args if a != "--enable-prefix-caching"]
    return base_args + ["--enable-prefix-caching"]


def dedupe_rows_earliest_wins(rows: Iterable[dict]) -> dict[tuple, dict]:
    """Collapses `rows` to one row per cell key, keeping the FIRST occurrence.

    See the module docstring's "Duplicate cell keys" section for why this is
    load-bearing, not a theoretical edge case, for the exact lane this
    script reruns.

    Parameters
    ----------
    rows : Iterable[dict]
        Rows to deduplicate. Only ``kind == "cell"`` rows are considered;
        every other ``kind`` (e.g. ``"sanity"``) is silently skipped.

    Returns
    -------
    dict[tuple, dict]
        Maps a `runner._row_key`-shaped tuple to the FIRST matching row
        object (the same `dict`, not a copy), in first-seen order.
    """
    by_key: dict[tuple, dict] = {}
    for row in rows:
        if row.get("kind") != "cell":
            continue
        key = runner._row_key(
            row.get("model", ""), row.get("theorem_id", ""),
            int(row.get("k", -1)), row.get("rung", ""),
            int(row.get("replicate_idx", -1)),
        )
        if key not in by_key:
            by_key[key] = row
    return by_key


def is_mathlib_cell(row: dict) -> bool:
    """True iff a cell row's theorem is vendored from Mathlib, not Std.

    See the module docstring's "Sample-stage population" section (2026-08-18
    spec amendment) for why this exclusion exists and why it is a hard
    requirement, not a refinement.

    Parameters
    ----------
    row : dict
        A cell row carrying a ``file_path`` field (every cell row does --
        see ``smolbench/deduction/lean/runner.py``'s ``_execute_one_cell``).

    Returns
    -------
    bool
        `False` iff ``file_path`` contains ``.lake/packages/std/`` anywhere
        (covers both a bare ``".lake/packages/std/Foo.lean"`` path and one
        rooted under some other prefix); `True` otherwise, INCLUDING when
        ``file_path`` is missing or empty (a row this permissive about is
        not what this check is for -- a missing path is not evidence of
        being a Std theorem).
    """
    file_path = str(row.get("file_path") or "")
    return _STD_PACKAGE_MARKER not in file_path


def measurable_cell_keys(rows: Iterable[dict]) -> list[tuple]:
    """Sorted Mathlib-only cell keys with a surviving, non-exception verdict.

    "Measurable" mirrors ``smolbench/deduction/lean/runner.py``'s own resume
    logic (``_existing_keys``): a verdict of ``"exception"`` means the
    VERIFIER failed, not the candidate proof, so there is nothing to compare
    against a rerun; ``"unverified"`` means phase-2 verification never
    actually ran for that row (should not occur in a fully-verified lane's
    ``verified_rows.jsonl``, excluded defensively rather than asserted
    against). Restricted to Mathlib cells only -- see `is_mathlib_cell` and
    the module docstring's "Sample-stage population" section.

    Duplicate cell keys are resolved via `dedupe_rows_earliest_wins` BEFORE
    the verdict/Mathlib filters are applied, so a cell with several
    surviving rows contributes at most once.

    RESOLVED 2026-08-18, by the exact-711 gate doing its job on the first
    live run: the original "surviving non-exception" phrasing (excluding
    only ``"exception"``/``"unverified"``) found 792 cells -- 793 Mathlib
    cells minus the lane's single DojoTacticTimeout exception -- and the
    +81 over the expected 711 is exactly the Mathlib prefix-failure class
    (``"replay_failed"``: the ground-truth prefix fails to replay, a
    verifier-INFRASTRUCTURE outcome, not a judgment on the candidate
    proof). Measurable is therefore a POSITIVE verdict whitelist: a cell
    counts only when its surviving verdict is one of ``success`` /
    ``lean_error`` / ``incomplete`` / ``given_up`` (the last measured live:
    4 cells in this lane where the candidate tactic drove Lean to a
    given-up proof state -- a judgment on the CANDIDATE, like
    ``lean_error``) -- the same denominator the coverage diagnosis derives
    (712 measurable minus this lane's one timeout cell = 711; verified
    live: 707 + 4 given_up = 711 exactly).

    Parameters
    ----------
    rows : Iterable[dict]
        Rows exactly as parsed from a ``verified_rows.jsonl`` download.

    Returns
    -------
    list[tuple]
        `runner._row_key`-shaped tuples, ascending-sorted -- sorting is what
        makes `select_sample_keys`'s draw reproducible independent of
        `rows`' on-disk order.
    """
    by_key = dedupe_rows_earliest_wins(rows)
    return sorted(
        key for key, row in by_key.items()
        if row.get("verdict") in ("success", "lean_error", "incomplete", "given_up")
        and is_mathlib_cell(row)
    )


def assert_population_size(measurable: Sequence[tuple], expected: int) -> None:
    """Raises loudly if the measurable population is not EXACTLY `expected`.

    A hard gate, not a warning -- see the module docstring's "Sample-stage
    population" section (2026-08-18 spec amendment) for why silently
    sampling a shifted population would be a real, not theoretical, mistake
    for this specific lane right now.

    Parameters
    ----------
    measurable : Sequence[tuple]
        The population `select_sample_keys` is about to draw from.
    expected : int
        The exact required population size.

    Raises
    ------
    ValueError
        ``len(measurable) != expected``. The message names both the
        expected and observed count.
    """
    n = len(measurable)
    if n != expected:
        raise ValueError(
            f"flip_probe sample: expected exactly {expected} Mathlib-only "
            f"measurable cells in the study lane's verified_rows.jsonl, "
            f"found {n}. This gate exists because a concurrent workstream "
            "is recovering std-theorem cells into this same lane's "
            "verified_rows.jsonl -- an unexpected count likely means either "
            "that recovery has landed (which would silently change the "
            "sampled population depending on run order) or that something "
            "else about the lane's data changed. Investigate before "
            "drawing a sample."
        )


def select_sample_keys(measurable: Sequence[tuple], n: int, seed: int) -> list[tuple]:
    """Draws a reproducible n-cell sample from an already-SORTED population.

    Parameters
    ----------
    measurable : Sequence[tuple]
        Population to draw from -- MUST already be sorted (see
        `measurable_cell_keys`); this function does not re-sort, since a
        caller sorting a DIFFERENT way (e.g. by first-seen file order)
        would silently change the draw for a fixed seed.
    n : int
        Sample size.
    seed : int
        `random.Random` seed.

    Returns
    -------
    list[tuple]
        `n` distinct keys drawn from `measurable`, in `random.Random(seed)
        .sample`'s own output order (NOT re-sorted here -- a caller that
        needs a canonical order, e.g. before writing ``whitelist.json`` or
        calling `runner.hash_cell_keys`, sorts the result itself).

    Raises
    ------
    ValueError
        `n` exceeds `len(measurable)` (propagated unwrapped from
        `random.Random.sample`; its message is already actionable).
    """
    rng = random.Random(seed)
    return rng.sample(list(measurable), n)


def _binom_cdf(k: int, n: int, p: float) -> float:
    """``P(X <= k)`` for ``X ~ Binomial(n, p)``.

    Pure stdlib (``math.comb`` + floats) -- see `clopper_pearson_interval`'s
    Notes for why this avoids a ``scipy`` dependency.
    """
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def _bisect_decreasing(f, lo: float, hi: float, iters: int = 100) -> float:
    """Bisection root-finder for `f`, assumed MONOTONE DECREASING on
    ``[lo, hi]`` with ``f(lo) >= 0 >= f(hi)`` (the caller,
    `clopper_pearson_interval`, guarantees this from the binomial CDF's own
    monotonicity in `p` -- see that function's Notes). 100 iterations on
    ``[0, 1]`` gives roughly ``2**-100`` precision, far beyond what a
    3-significant-figure report needs.
    """
    for _ in range(iters):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial confidence interval for a proportion (Clopper-Pearson).

    Parameters
    ----------
    k : int
        Number of "successes" (here: discordant cells, ``b + c``).
    n : int
        Number of trials (here: sample size, 200).
    alpha : float, default 0.05
        Two-sided miscoverage rate; the returned interval has ``1 - alpha``
        nominal coverage (95% for the default).

    Returns
    -------
    tuple[float, float]
        ``(lower, upper)`` bounds, each in ``[0, 1]``. ``lower == 0.0`` iff
        ``k == 0``; ``upper == 1.0`` iff ``k == n`` (the standard
        Clopper-Pearson boundary convention -- there is no informative
        bound to solve for at either extreme).

    Raises
    ------
    ValueError
        ``not 0 <= k <= n``, or ``n <= 0``.

    Notes
    -----
    Implemented by bisection on the exact binomial CDF rather than via
    ``scipy.stats.beta.ppf`` (the usual closed-form route -- the CP interval
    is exactly a pair of beta quantiles): this avoids a ``scipy`` dependency
    this module does not otherwise need, and keeps the implementation
    IDENTICAL on ``.venv`` and ``.venv-lean`` (``--stage verify`` runs on
    the latter; ``--stage analyze`` can run on either, and must produce the
    same numbers regardless of which one a caller uses).

    ``_binom_cdf(k, n, p)`` is monotonically DECREASING in `p` for fixed
    `k < n` (a higher per-trial success probability makes "``k`` or fewer
    successes" less likely), which is what makes the bisection well-posed:
    solving ``_binom_cdf(k - 1, n, p) = 1 - alpha/2`` for `p` gives the
    lower bound (the value of `p` at which "at least `k` successes" has
    exactly ``alpha/2`` probability); solving ``_binom_cdf(k, n, p) =
    alpha/2`` gives the upper bound (`p` at which "at most `k` successes"
    has exactly ``alpha/2`` probability).
    """
    if n <= 0:
        raise ValueError(f"clopper_pearson_interval: n must be positive, got {n}")
    if not 0 <= k <= n:
        raise ValueError(f"clopper_pearson_interval: k must be in [0, {n}], got {k}")

    lower = (
        0.0 if k == 0
        else _bisect_decreasing(lambda p: _binom_cdf(k - 1, n, p) - (1 - alpha / 2), 0.0, 1.0)
    )
    upper = (
        1.0 if k == n
        else _bisect_decreasing(lambda p: _binom_cdf(k, n, p) - alpha / 2, 0.0, 1.0)
    )
    return lower, upper


def is_pass(verdict: str) -> bool:
    """True iff a verdict string counts as a pass@1 success."""
    return verdict == "success"


def flip_stats(pairs: Mapping[tuple, tuple[str, str]]) -> dict:
    """McNemar-style flip statistics: re-verified-original vs. rerun verdict.

    This is the PRIMARY, cross-PROCESS comparison this whole experiment
    exists to make -- both sides graded by the SAME (today's) verifier, so
    verifier-version drift cannot leak into it (see `verifier_drift_stats`
    for the separate check that isolates drift instead).

    Parameters
    ----------
    pairs : Mapping[tuple, tuple[str, str]]
        Cell key -> ``(study_reverified_verdict, rerun_verdict)`` -- the
        verdict TEXT (e.g. ``"success"``, ``"lean_error"``), not a
        pre-computed bool; this function applies `is_pass` itself so a
        caller cannot silently apply a different pass/fail rule to the two
        legs.

    Returns
    -------
    dict
        ``n``: sample size. ``a_both_pass``/``b_orig_pass_rerun_fail``/
        ``c_orig_fail_rerun_pass``/``d_both_fail``: the 2x2 contingency-table
        cells. ``discordant``: ``b + c``. ``flip_rate``: ``discordant / n``.
        ``flip_rate_ci95``: exact Clopper-Pearson ``[lower, upper]`` on
        ``discordant`` out of ``n`` at the 95% level. ``pass_at_1_se``: the
        normal-approximation standard error of `flip_rate` as a proportion
        (``sqrt(p(1-p)/n)`` at ``p = flip_rate``) -- see Notes for what this
        does and does not account for. ``pass_at_1_se_caveat``: a string
        explaining that caveat, carried in the JSON report itself so a
        reader does not need this docstring to see it.
        ``flipped_keys``: the ``b + c`` cell keys, each as a JSON-friendly
        ``list`` (not a ``tuple``).

    Notes
    -----
    **Independence caveat, stated explicitly rather than left implicit**:
    `pass_at_1_se` (and the Clopper-Pearson interval, which is exact only
    for i.i.d. Bernoulli trials) treats the `n` cells as independent. They
    are not, strictly: several cells in a 200-cell sample can share a
    theorem (different rungs/replicates of the same theorem), and a
    theorem-level effect could correlate their flips.
    ``notebooks/lean/power_analysis.py``'s block bootstrap over theorem
    blocks is this study's answer to that same problem elsewhere; THIS
    function does not implement it (block-bootstrapping this specific
    estimator is out of this task's scope -- the brief asks for the exact
    binomial CI specifically). Read `pass_at_1_se` and the CP interval as a
    likely-too-narrow bound, not a fully rigorous one.
    """
    n = len(pairs)
    a = b = c = d = 0
    flipped_keys: list[tuple] = []
    for key, (orig_verdict, rerun_verdict) in pairs.items():
        orig, rerun = is_pass(orig_verdict), is_pass(rerun_verdict)
        if orig and rerun:
            a += 1
        elif orig and not rerun:
            b += 1
            flipped_keys.append(key)
        elif not orig and rerun:
            c += 1
            flipped_keys.append(key)
        else:
            d += 1
    discordant = b + c
    flip_rate = discordant / n if n else 0.0
    ci_lo, ci_hi = clopper_pearson_interval(discordant, n) if n else (0.0, 0.0)
    se = math.sqrt(flip_rate * (1 - flip_rate) / n) if n else 0.0
    return {
        "n": n,
        "a_both_pass": a,
        "b_orig_pass_rerun_fail": b,
        "c_orig_fail_rerun_pass": c,
        "d_both_fail": d,
        "discordant": discordant,
        "flip_rate": flip_rate,
        "flip_rate_ci95": [ci_lo, ci_hi],
        "pass_at_1_se": se,
        "pass_at_1_se_caveat": (
            "Normal-approximation SE (and the Clopper-Pearson CI) assume "
            "independent cells. Several cells in this sample can share a "
            "theorem (different rungs/replicates of it), which this "
            "estimate does not account for -- see flip_stats' docstring "
            "Notes. Treat as a rough, likely-too-narrow bound, not exact."
        ),
        "flipped_keys": [list(k) for k in flipped_keys],
    }


def verifier_drift_stats(pairs: Mapping[tuple, tuple[str, str]]) -> dict:
    """Agreement of a fresh reverification against the study's own verdict.

    A SEPARATE, secondary check from `flip_stats`: this isolates VERIFIER
    drift (Lean/mathlib toolchain changes since the study ran) from
    generation-process nondeterminism, by comparing two gradings of the
    SAME original candidate text rather than two different candidates.

    Parameters
    ----------
    pairs : Mapping[tuple, tuple[str, str]]
        Cell key -> ``(study_original_verdict, study_reverified_verdict)``
        -- EXACT verdict strings, compared for equality rather than
        collapsed to pass/fail, since drift between e.g. ``"lean_error"``
        and ``"incomplete"`` is itself informative even though both are
        "not success".

    Returns
    -------
    dict
        ``n``, ``agree`` (count where the two verdict strings are equal),
        ``agreement_rate``, ``disagreements`` (a list of
        ``{"key": [...], "study_verdict": ..., "reverified_verdict": ...}``
        for every cell where they differ).
    """
    n = len(pairs)
    agree = 0
    disagreements: list[dict] = []
    for key, (study_verdict, reverified_verdict) in pairs.items():
        if study_verdict == reverified_verdict:
            agree += 1
        else:
            disagreements.append({
                "key": list(key),
                "study_verdict": study_verdict,
                "reverified_verdict": reverified_verdict,
            })
    return {
        "n": n,
        "agree": agree,
        "agreement_rate": agree / n if n else 0.0,
        "disagreements": disagreements,
    }


def _prepare_originals_rows(study_rows: Iterable[dict], whitelist: Iterable[tuple]) -> list[dict]:
    """Filters+resets the study's rows to phase-1 shape for the 200 whitelisted cells.

    Deduplicates via `dedupe_rows_earliest_wins`, then for each whitelisted
    key stashes the study's own verdict under ``"_study_verdict"``/
    ``"_study_lean_error"`` (surviving the reverification pass untouched --
    ``lean_verify_rows.fan_out_verdict`` only writes ``verdict``/
    ``lean_error``/``final_state_pp``/``verify_ms``, so these extra keys are
    never read or clobbered by it) and resets ``verdict`` to
    ``"unverified"`` (with ``lean_error``/``final_state_pp`` cleared) so
    ``lean_verify_rows.group_unverified`` picks the row up for
    reverification.

    Parameters
    ----------
    study_rows : Iterable[dict]
        Rows exactly as downloaded from the study lane's
        ``verified_rows.jsonl``.
    whitelist : Iterable[tuple]
        The 200 whitelisted cell keys.

    Returns
    -------
    list[dict]
        One row per whitelisted key, in SORTED key order.

    Raises
    ------
    ValueError
        Any whitelisted key is absent from `study_rows` after
        deduplication -- named in the message (first few, if many).
    """
    by_key = dedupe_rows_earliest_wins(study_rows)
    out: list[dict] = []
    missing: list[tuple] = []
    for key in sorted(whitelist):
        row = by_key.get(key)
        if row is None:
            missing.append(key)
            continue
        fresh = dict(row)
        fresh["_study_verdict"] = row.get("verdict")
        fresh["_study_lean_error"] = row.get("lean_error")
        fresh["verdict"] = "unverified"
        fresh["lean_error"] = None
        fresh["final_state_pp"] = None
        out.append(fresh)
    if missing:
        raise ValueError(
            f"flip_probe verify: {len(missing)} whitelisted cell key(s) not "
            f"found in the study's verified_rows.jsonl (first few: "
            f"{missing[:5]}). The sample and the study lane's data may have "
            "diverged since --stage sample ran."
        )
    return out


# ---------------------------------------------------------------------------
# Dynamic module loading -- notebooks/ and scripts/ are not importable
# packages, and both `run_study.py` files in this repo share a basename, so
# a bare `import run_study` would be ambiguous. Mirrors
# `notebooks/deduction/run_study.py`'s own loader for
# `notebooks/induction/run_study.py`, and `tests/test_deduction_study.py`'s
# `_load_by_path` (same pattern, independently re-derived here rather than
# imported, since neither of those is a shared library module).
# ---------------------------------------------------------------------------


def _load_module_by_path(path: Path, name: str) -> Any:
    """Executes `path` as a module registered under `name` in `sys.modules`.

    The `sys.modules[name] = module` line before `exec_module` is NOT
    optional -- on Python 3.14, a `@dataclass` declared inside a module
    absent from `sys.modules` raises `AttributeError` from
    `dataclasses._is_type`, which looks its own module up by
    `cls.__module__` (see `notebooks/deduction/run_study.py`'s own loader
    comment for the same note).
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_run_study() -> Any:
    """Loads ``notebooks/deduction/run_study.py``.

    ONLY call this after every ``LEAN_*``/``EC2_*`` environment variable
    ``--stage generate`` needs has already been set via PLAIN assignment
    (see `_stage_generate`): loading this module transitively imports
    ``smolbench.evals.ec2``, which freezes its ``EC2_*`` module constants
    from the process environment at that exact moment (see
    ``notebooks/deduction/run_study.py``'s own "MODULE IMPORT ORDER"
    section, which this call mirrors exactly).
    """
    return _load_module_by_path(
        REPO_ROOT / "notebooks" / "deduction" / "run_study.py",
        "flip_probe_deduction_run_study",
    )


def _load_lean_verify_rows() -> Any:
    """Loads ``scripts/lean_verify_rows.py`` (safe to import on either venv
    at module scope -- its Lean/Dojo-only parts are behind
    ``require_py312``/lazy imports; see that module's own docstring)."""
    return _load_module_by_path(
        REPO_ROOT / "scripts" / "lean_verify_rows.py", "flip_probe_lean_verify_rows"
    )


def _utc_now_iso() -> str:
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# --stage sample
# ---------------------------------------------------------------------------


def _stage_sample(args: argparse.Namespace) -> None:
    from smolbench.evals import _aws  # lazy -- keeps this module's top level AWS-free

    key = f"{SPOOL_PREFIX}/{STUDY_RUN_NAME}/{VERIFIED_FILENAME}"
    logging.info(
        "flip_probe[sample]: fetching s3://%s/%s (READ-ONLY)", SPOOL_BUCKET, key
    )
    client = _aws.fresh_client("s3", SPOOL_REGION)
    obj = client.get_object(Bucket=SPOOL_BUCKET, Key=key)
    body = obj["Body"].read()
    rows = [json.loads(line) for line in body.decode("utf-8").splitlines() if line.strip()]
    cell_rows = [r for r in rows if r.get("kind") == "cell"]

    # Sanity check on the row-key identity assumption: `runner.sweep`'s cell
    # filter is keyed on the row's "model" field (== `display_name`, see
    # `runner._execute_one_cell`); if this lane's stored rows ever carried a
    # DIFFERENT string there (e.g. the served HF id instead of the display
    # name), every whitelist key built from these rows would silently miss
    # every cell in a live sweep. Cheap to check here, expensive to discover
    # live.
    models_seen = {r.get("model") for r in cell_rows}
    if models_seen != {MODEL}:
        raise ValueError(
            f"flip_probe sample: expected every cell row's 'model' field to "
            f"be exactly {MODEL!r}, found {sorted(m for m in models_seen if m is not None)!r}. "
            "runner.sweep's cell-whitelist filter is keyed on this field "
            "(see runner._row_key / _execute_one_cell) -- a mismatch here "
            "would make every whitelist key silently miss on a live run."
        )

    by_key = dedupe_rows_earliest_wins(cell_rows)
    n_distinct = len(by_key)
    n_duplicates = len(cell_rows) - n_distinct

    measurable = measurable_cell_keys(cell_rows)
    assert_population_size(measurable, EXPECTED_MATHLIB_POPULATION)

    drawn = select_sample_keys(measurable, args.n, args.seed)
    drawn_sorted = sorted(drawn)

    run_dir = _flip_run_dir()
    run_dir.mkdir(parents=True, exist_ok=True)
    _whitelist_path().write_text(
        json.dumps([list(k) for k in drawn_sorted], indent=2) + "\n"
    )

    manifest = {
        "n": len(drawn_sorted),
        "seed": args.seed,
        "sha256": runner.hash_cell_keys(drawn_sorted),
        "study_run": STUDY_RUN_NAME,
        "study_s3_uri": f"s3://{SPOOL_BUCKET}/{key}",
        "drawn_at_utc": _utc_now_iso(),
        "n_rows_downloaded": len(rows),
        "n_cell_rows_downloaded": len(cell_rows),
        "n_distinct_cell_keys": n_distinct,
        "n_duplicate_cell_rows": n_duplicates,
        "n_measurable_mathlib_population": len(measurable),
        "expected_mathlib_population": EXPECTED_MATHLIB_POPULATION,
    }
    _sample_manifest_path().write_text(json.dumps(manifest, indent=2) + "\n")
    logging.info(
        "flip_probe[sample]: population=%d (Mathlib-only, %d distinct keys, "
        "%d duplicate row(s) collapsed) -> drew %d cells -> %s (sha256=%s)",
        len(measurable), n_distinct, n_duplicates, len(drawn_sorted),
        _whitelist_path(), manifest["sha256"],
    )


# ---------------------------------------------------------------------------
# --stage generate
# ---------------------------------------------------------------------------


def _spool_flip_run(run_dir: Path, client: Any = None) -> int:
    """Uploads `run_dir` to S3 under THIS experiment's own ``flip_*`` prefix.

    See the module docstring's HARD RULE section for why
    ``notebooks/deduction/run_study.py``'s own ``spool_to_s3`` is
    deliberately NOT reused here.

    Parameters
    ----------
    run_dir : Path
        Local run directory to upload (everything under it, recursively,
        EXCEPT the ``originals_rerun/`` subtree -- see Notes).
    client : Any, optional
        Injected S3 client (real, or a test fake exposing ``upload_file``/
        ``head_object``). ``None`` (the default) builds a real one via
        ``smolbench.evals._aws.fresh_client("s3", SPOOL_REGION)``.

    Returns
    -------
    int
        Number of files uploaded and size-verified. ``0`` if `run_dir` is
        not a directory.

    Raises
    ------
    RuntimeError
        Any uploaded file's remote size does not match its local size.

    Notes
    -----
    Deliberately does NOT prune local files after a verified upload, unlike
    ``spool_to_s3``: this is a small, one-off n=200-cell diagnostic run, not
    a 21-lane production study, so the disk cost of keeping the local copy
    is trivial -- and keeping it means ``--stage verify``'s leg (a) can read
    it locally too, with S3 only as a robustness fallback (see
    `_read_flip_run_verified_rows`).

    The ``originals_rerun/`` subtree (leg (b)'s local-only reverification of
    the STUDY's originals -- see `_stage_verify`) is excluded from the
    upload even though this function is otherwise happy to spool under the
    experiment's own permitted prefix: those files are derived from the
    study's candidate proofs, and this call can run AFTER ``--stage
    verify`` if an operator re-runs ``--stage generate`` to recover cells
    lost to a transient failure. Spooling them would not violate the HARD
    RULE (this is still the flip prefix, not the study's), but it would
    duplicate study-derived data into a second S3 location for no reason
    this experiment needs.
    """
    if not run_dir.is_dir():
        logging.info("flip_probe spool: no run directory at %s; nothing to sync.", run_dir)
        return 0

    if client is None:
        from smolbench.evals import _aws

        client = _aws.fresh_client("s3", SPOOL_REGION)

    dest_prefix = f"{SPOOL_PREFIX}/{FLIP_RUN_NAME}/"
    files = sorted(
        p for p in run_dir.rglob("*")
        if p.is_file() and "originals_rerun" not in p.relative_to(run_dir).parts
    )
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        dest_key = dest_prefix + rel
        client.upload_file(str(path), SPOOL_BUCKET, dest_key)
        local_size = path.stat().st_size
        head = client.head_object(Bucket=SPOOL_BUCKET, Key=dest_key)
        remote_size = head["ContentLength"]
        if remote_size != local_size:
            raise RuntimeError(
                f"flip_probe spool: size mismatch verifying {dest_key!r}: "
                f"local={local_size} bytes, remote={remote_size} bytes."
            )
    logging.info(
        "flip_probe[generate]: spooled %d file(s) to s3://%s/%s",
        len(files), SPOOL_BUCKET, dest_prefix,
    )
    return len(files)


def _stage_generate(args: argparse.Namespace) -> None:
    whitelist_path = _whitelist_path()
    if not whitelist_path.exists():
        raise SystemExit(
            f"flip_probe generate: {whitelist_path} not found -- run "
            "--stage sample first."
        )
    whitelist_size = len(json.loads(whitelist_path.read_text()))

    # Env MUST be set via PLAIN assignment before `_load_run_study()` is
    # ever called in this process -- see `_load_run_study`'s docstring and
    # `notebooks/deduction/run_study.py`'s own "MODULE IMPORT ORDER" note,
    # which this mirrors exactly.
    os.environ["LEAN_MODEL"] = MODEL
    os.environ["LEAN_RUN_NAME"] = FLIP_RUN_NAME
    os.environ["LEAN_CELL_WHITELIST"] = str(whitelist_path)
    os.environ["EC2_EXPERIMENT_TAG"] = EC2_TAG
    os.environ["EC2_STATE_FILE"] = str(REPO_ROOT / EC2_STATE_FILE_NAME)
    os.environ["EC2_REQUIRE_GPU"] = EC2_REQUIRE_GPU
    os.environ["EC2_INSTANCE_TYPES"] = EC2_INSTANCE_TYPE
    os.environ.setdefault("EC2_REGIONS", args.regions)

    run_study = _load_run_study()
    ec2 = run_study.ec2

    # In-process override ONLY -- the spec on disk is never edited (mirrors
    # scripts/hinge_probe.py's own comment on this exact line).
    spec = ec2.EC2_DEPLOY_SPECS[MODEL]
    determinism_args = getattr(ec2, "DETERMINISM_ARGS", [])
    stock_args = stock_vllm_args(spec.get("vllm_args", []), determinism_args)
    logging.info(
        "flip_probe[generate]: overriding vllm_args to the STOCK "
        "(pre-determinism-bundle) reconstruction: %s", stock_args,
    )
    ec2.EC2_DEPLOY_SPECS[MODEL]["vllm_args"] = stock_args

    config = run_study.build_config(MODEL)
    run_dir = run_study.runner.results_root() / "runs" / config["run_name"]
    verifier = run_study.select_verifier()

    logging.info(
        "flip_probe[generate]: provisioning %s (tag=%s, gpu=%s) ...",
        EC2_INSTANCE_TYPE, EC2_TAG, EC2_REQUIRE_GPU,
    )
    ec2.provision_spot_instance()

    n_written = 0
    try:
        with ec2.serve_model(MODEL):
            # Provenance sidecar -- copied verbatim from
            # notebooks/deduction/run_study.py's own main(): this
            # experiment's entire point is measuring cross-PROCESS
            # variation, so not recording which process generated the
            # rerun would be self-defeating.
            cfg_snapshot = ec2.server_config(MODEL)
            if cfg_snapshot is not None:
                import datetime

                import yaml

                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump(
                        [{"captured_utc": stamp, **cfg_snapshot}],
                        sink, default_flow_style=False, indent=4,
                    )
            n_written = run_study.runner.sweep(config, run_dir, verifier=verifier)
    finally:
        try:
            ec2.shutdown_instance()
        except Exception:
            logging.exception(
                "flip_probe[generate]: TEARDOWN FAILED -- terminate the box by hand "
                "(state file: %s)", os.environ["EC2_STATE_FILE"],
            )

    if n_written != whitelist_size:
        logging.warning(
            "flip_probe[generate]: sweep wrote %d cell row(s) but the "
            "whitelist requested %d. Candidates: a whitelisted theorem's "
            "sanity gate failed (SANITY-FAIL), a Dojo session failed to "
            "open (DOJO-OPEN-FAIL), or the process was interrupted. Check "
            "the sweep's own console log above before trusting the flip "
            "rate this run will produce -- --stage analyze will report "
            "whatever landed, not necessarily all 200 cells.",
            n_written, whitelist_size,
        )
    else:
        logging.info(
            "flip_probe[generate]: sweep wrote exactly the %d requested cell(s).",
            n_written,
        )

    # If `runner.sweep` above raised, control never reaches this line at
    # all (the `finally` block only tears the box down) -- so a mid-sweep
    # failure means NOTHING gets spooled this call, matching
    # `notebooks/deduction/run_study.py`'s own `main()` (`spool_to_s3` is
    # likewise only reached after a successful sweep). The correct recovery
    # is to re-run `--stage generate`: `runner.sweep`'s own on-disk resume
    # (keyed by cell, restricted to the whitelist) picks up exactly the
    # missing cells, never a full re-run. Proceeding straight to `--stage
    # verify` after a failed `generate` would fail loudly anyway (no
    # all_rows.jsonl object at the expected S3 key), but re-running
    # `generate` first is the intended path, not a fallback.
    _spool_flip_run(run_dir)


# ---------------------------------------------------------------------------
# --stage verify
# ---------------------------------------------------------------------------


class _LocalBody:
    """Stand-in for botocore's ``StreamingBody`` -- only ``.read()`` is used
    by ``lean_verify_rows.download_rows``."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class _LocalRunClient:
    """S3-client stand-in redirecting reads/writes to two local files.

    ``lean_verify_rows.verify_run`` is written against an INJECTED S3
    client purely so its own test suite can pass a fake (see that module's
    "Impure: S3 I/O" section) -- this class reuses that same seam in
    PRODUCTION, specifically because this module's HARD RULE ("no write of
    any kind under the study's ``scaling_*`` S3 prefixes") makes routing
    the study-originals reverification through a REAL S3 client
    unacceptable, while hand-rolling ``verify_run``'s group/sanity/resume/
    Dojo-failure-handling logic a second time here would duplicate ~150
    already-tested lines for no benefit. There is no real boto3 client
    anywhere in this class's call graph, so it is STRUCTURALLY IMPOSSIBLE
    for a ``verify_run`` call driven by this client to write a single byte
    to real S3.

    Parameters
    ----------
    rows_path : Path
        Local file serving ``get_object`` for the rows key -- the prepared,
        verdict-reset-to-``"unverified"`` original candidate rows (see
        `_prepare_originals_rows`).
    verified_path : Path
        Local file this client OWNS for the verified key: ``upload_file``
        copies its argument here; ``get_object`` reads back from here on a
        resumed call (mirroring a real S3 round trip). Deliberately a path
        this class owns outright -- never ``verify_run``'s own internal
        scratch path -- so a resumed call can never race a copy against
        itself (``shutil.copyfile`` truncates its destination before
        reading its source; copying a file onto itself would corrupt it).
    rows_filename, verified_filename : str
        The exact basenames ``lean_verify_rows.ROWS_FILENAME``/
        ``VERIFIED_FILENAME`` currently use -- passed in by the caller
        (which already has that module loaded) rather than imported here,
        so this class carries zero import-time coupling to
        ``lean_verify_rows``.
    """

    def __init__(
        self, *, rows_path: Path, verified_path: Path,
        rows_filename: str, verified_filename: str,
    ) -> None:
        self._rows_path = rows_path
        self._verified_path = verified_path
        self._rows_filename = rows_filename
        self._verified_filename = verified_filename

    def get_object(self, Bucket: str, Key: str) -> dict:  # boto3's own param casing
        if Key.endswith(self._verified_filename):
            path = self._verified_path
        elif Key.endswith(self._rows_filename):
            path = self._rows_path
        else:
            raise ValueError(f"_LocalRunClient.get_object: unexpected key {Key!r}")
        if not path.exists():
            from botocore.exceptions import ClientError

            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": f"local stand-in: {path} absent"}},
                "GetObject",
            )
        return {"Body": _LocalBody(path.read_bytes())}

    def upload_file(self, filename: str, Bucket: str, Key: str) -> None:  # boto3's own param casing
        if not Key.endswith(self._verified_filename):
            raise ValueError(f"_LocalRunClient.upload_file: unexpected key {Key!r}")
        self._verified_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filename, self._verified_path)


def _stage_verify(args: argparse.Namespace) -> None:
    lvr = _load_lean_verify_rows()
    lvr.require_py312()

    run_dir = _flip_run_dir()
    if not run_dir.exists():
        raise SystemExit(
            f"flip_probe verify: {run_dir} not found -- run --stage generate first."
        )
    whitelist_path = _whitelist_path()
    if not whitelist_path.exists():
        raise SystemExit(
            f"flip_probe verify: {whitelist_path} not found -- run --stage sample first."
        )

    meminfo_path = Path("/proc/meminfo")
    if meminfo_path.exists():
        lvr.check_workers(args.workers, meminfo_path.read_text())

    with lvr._dojo_cache_lock():
        from smolbench.evals import _aws

        real_client = _aws.fresh_client("s3", lvr.S3_REGION)

        # ---- Leg (a): the flip run's OWN rows -- normal S3 round-trip,
        # writes permitted under its own flip_* prefix. ----
        logging.info(
            "flip_probe[verify]: verifying %s's own rows (S3, read+write "
            "under its own prefix)", FLIP_RUN_NAME,
        )
        rc = lvr.verify_run(
            client=real_client, bucket=SPOOL_BUCKET, key_prefix=SPOOL_PREFIX,
            run=FLIP_RUN_NAME, workers=args.workers, workdir=run_dir.parent,
        )
        if rc != 0:
            raise SystemExit(
                f"flip_probe verify: lean_verify_rows.verify_run returned "
                f"{rc} for {FLIP_RUN_NAME} (no all_rows.jsonl found -- did "
                "--stage generate actually write and spool any rows?)"
            )

        # ---- Leg (b): READ-ONLY fetch of the study's ORIGINAL candidate
        # rows for exactly the whitelisted cells; reverify LOCALLY ONLY --
        # see this module's HARD RULE. ----
        whitelist = runner.load_cell_whitelist(str(whitelist_path))
        study_key = f"{SPOOL_PREFIX}/{STUDY_RUN_NAME}/{lvr.VERIFIED_FILENAME}"
        logging.info(
            "flip_probe[verify]: fetching %d whitelisted original row(s) "
            "from s3://%s/%s (READ-ONLY)", len(whitelist), SPOOL_BUCKET, study_key,
        )
        obj = real_client.get_object(Bucket=SPOOL_BUCKET, Key=study_key)
        study_rows = [
            json.loads(line)
            for line in obj["Body"].read().decode("utf-8").splitlines()
            if line.strip()
        ]
        originals = _prepare_originals_rows(study_rows, whitelist)

        originals_dir = _originals_dir()
        originals_dir.mkdir(parents=True, exist_ok=True)
        rows_path = originals_dir / "originals_all_rows.jsonl"
        new_rows_bytes = "".join(
            json.dumps(row, ensure_ascii=False) + "\n" for row in originals
        ).encode("utf-8")

        # Resume-trap guard: `_LocalRunClient` serves `verified_path` once it
        # exists, so a SECOND `--stage verify` invocation would otherwise
        # make `verify_run` compute `pending = {}` from a STALE
        # verified_rows.jsonl while `rows_path` above has just been
        # rewritten from a fresh S3 download -- exactly the trap
        # `lean_verify_rows.verify_run`'s own `no_resume` flag exists for
        # (its docstring: "six lanes were in exactly that state on
        # 2026-08-16... nemotron-3-nano-4b had had all 944 of its cells
        # regenerated"). `originals_dir`'s own local cache copy of the ROWS
        # key (written by `verify_run`'s `download_rows` call on the LAST
        # invocation, at `originals_dir/_scratch/<ROWS_FILENAME>`) is the
        # one artifact that lets this call detect
        # "did the candidate content actually change" without re-deriving
        # verify_run's own resume bookkeeping: if it differs from what we
        # are about to serve this time, the prior verified_rows.jsonl
        # describes content that no longer exists, and resuming from it
        # would silently report success while verifying nothing.
        scratch_rows_path = originals_dir / "_scratch" / lvr.ROWS_FILENAME
        no_resume_originals = (
            scratch_rows_path.exists() and scratch_rows_path.read_bytes() != new_rows_bytes
        )
        if no_resume_originals:
            logging.warning(
                "flip_probe[verify]: the study-originals candidate content "
                "changed since the last --stage verify run (stale %s) -- "
                "discarding the prior local verified_rows.jsonl and "
                "re-verifying every whitelisted cell fresh, per "
                "lean_verify_rows.verify_run's own no_resume contract.",
                scratch_rows_path,
            )
        rows_path.write_bytes(new_rows_bytes)
        verified_path = originals_dir / lvr.VERIFIED_FILENAME

        local_client = _LocalRunClient(
            rows_path=rows_path, verified_path=verified_path,
            rows_filename=lvr.ROWS_FILENAME, verified_filename=lvr.VERIFIED_FILENAME,
        )
        logging.info(
            "flip_probe[verify]: reverifying %d study-original candidate(s) "
            "LOCALLY ONLY under %s (no S3 write in this leg)",
            len(originals), originals_dir,
        )
        # Leg (a) above deliberately keeps resume=True (the default) -- the
        # flip run's own all_rows.jsonl is immutable after `--stage
        # generate` (see lean_verify_rows.py's own "original all_rows.jsonl
        # object is NEVER modified" invariant), so resuming it is always
        # safe and saves real Dojo work on a re-invocation. Leg (b) is the
        # one that can go stale, per the guard just above.
        rc2 = lvr.verify_run(
            client=local_client, bucket="local-originals-rerun", key_prefix="",
            run="_scratch", workers=args.workers, workdir=originals_dir,
            no_resume=no_resume_originals,
        )
        if rc2 != 0:
            raise SystemExit(
                f"flip_probe verify: lean_verify_rows.verify_run returned "
                f"{rc2} reverifying the study originals -- see "
                f"{originals_dir / '_scratch'} for its local scratch copy."
            )

    logging.info(
        "flip_probe[verify]: done. Flip run rows: s3://%s/%s%s/verified_rows.jsonl  "
        "Study-originals rerun: %s", SPOOL_BUCKET, SPOOL_PREFIX + "/", FLIP_RUN_NAME,
        verified_path,
    )


# ---------------------------------------------------------------------------
# --stage analyze
# ---------------------------------------------------------------------------


def _read_flip_run_verified_rows() -> list[dict]:
    """Reads the flip run's own re-verified rows.

    Local copy if present (``--stage verify`` ran on this same machine),
    else downloaded from S3 (the ``flip_*`` prefix, read-only, permitted --
    see the module docstring's HARD RULE).
    """
    local_path = _flip_run_dir() / VERIFIED_FILENAME
    if local_path.exists():
        return [
            json.loads(line) for line in local_path.read_text().splitlines() if line.strip()
        ]
    from smolbench.evals import _aws

    client = _aws.fresh_client("s3", SPOOL_REGION)
    key = f"{SPOOL_PREFIX}/{FLIP_RUN_NAME}/{VERIFIED_FILENAME}"
    logging.info(
        "flip_probe[analyze]: no local copy at %s -- downloading s3://%s/%s",
        local_path, SPOOL_BUCKET, key,
    )
    obj = client.get_object(Bucket=SPOOL_BUCKET, Key=key)
    return [
        json.loads(line)
        for line in obj["Body"].read().decode("utf-8").splitlines()
        if line.strip()
    ]


def _stage_analyze(args: argparse.Namespace) -> None:
    whitelist_path = _whitelist_path()
    if not whitelist_path.exists():
        raise SystemExit(
            f"flip_probe analyze: {whitelist_path} not found -- run "
            "--stage sample first."
        )
    whitelist = sorted(runner.load_cell_whitelist(str(whitelist_path)))

    # Provenance self-check: confirm the whitelist on disk right now is
    # still the SAME set `--stage sample` recorded, before pairing anything
    # against it. Without this, a whitelist regenerated between stages
    # (e.g. --stage sample re-run with a different --n/--seed, or the file
    # hand-edited) would silently pair a DIFFERENT cell set than the one
    # sample_manifest.json (and any downstream write-up) describes.
    sample_manifest_path = _sample_manifest_path()
    sample_manifest: dict = {}
    if sample_manifest_path.exists():
        sample_manifest = json.loads(sample_manifest_path.read_text())
        recorded_sha = sample_manifest.get("sha256")
        current_sha = runner.hash_cell_keys(whitelist)
        if recorded_sha is not None and current_sha != recorded_sha:
            raise SystemExit(
                f"flip_probe analyze: {whitelist_path}'s current content "
                f"(sha256={current_sha}) does not match "
                f"{sample_manifest_path}'s recorded sha256={recorded_sha}. "
                "The whitelist has changed since --stage sample ran -- "
                "re-run --stage sample (drawing a fresh, self-consistent "
                "sample) and --stage generate/verify against IT, rather "
                "than analyzing a mismatched pairing."
            )
    else:
        logging.warning(
            "flip_probe[analyze]: %s not found -- skipping the whitelist "
            "provenance self-check (cannot confirm this whitelist is the "
            "one --stage sample drew).", sample_manifest_path,
        )

    originals_verified_path = _originals_dir() / VERIFIED_FILENAME
    if not originals_verified_path.exists():
        raise SystemExit(
            f"flip_probe analyze: {originals_verified_path} not found -- run "
            "--stage verify first, ON THIS SAME MACHINE (or the same "
            "results/ filesystem). The re-verified study originals live "
            "only in a local originals_rerun/ directory BY DESIGN -- never "
            "uploaded to S3, per this module's HARD RULE; see the module "
            "docstring."
        )
    originals_rows = [
        json.loads(line)
        for line in originals_verified_path.read_text().splitlines()
        if line.strip()
    ]
    rerun_rows = _read_flip_run_verified_rows()

    originals_by_key = dedupe_rows_earliest_wins(originals_rows)
    rerun_by_key = dedupe_rows_earliest_wins(rerun_rows)

    flip_pairs: dict[tuple, tuple[str, str]] = {}
    drift_pairs: dict[tuple, tuple[str, str]] = {}
    missing_original: list[tuple] = []
    missing_rerun: list[tuple] = []
    empty_rerun_candidates = {"prompt_tokens_gt_0": 0, "prompt_tokens_0": 0}

    for key in whitelist:
        orig_row = originals_by_key.get(key)
        rerun_row = rerun_by_key.get(key)
        if orig_row is None:
            missing_original.append(key)
            continue
        if rerun_row is None:
            missing_rerun.append(key)
            continue
        flip_pairs[key] = (orig_row.get("verdict", ""), rerun_row.get("verdict", ""))
        drift_pairs[key] = (orig_row.get("_study_verdict", ""), orig_row.get("verdict", ""))
        if not (rerun_row.get("candidate_proof") or "").strip():
            bucket = (
                "prompt_tokens_gt_0"
                if int(rerun_row.get("prompt_tokens") or 0) > 0
                else "prompt_tokens_0"
            )
            empty_rerun_candidates[bucket] += 1

    if missing_original or missing_rerun:
        logging.warning(
            "flip_probe[analyze]: %d whitelisted cell(s) missing from the "
            "re-verified originals, %d missing from the rerun -- excluded "
            "from the pairing below (n=%d of %d requested).",
            len(missing_original), len(missing_rerun), len(flip_pairs), len(whitelist),
        )

    stats = flip_stats(flip_pairs)
    drift = verifier_drift_stats(drift_pairs)

    report = {
        "model": MODEL,
        "study_run": STUDY_RUN_NAME,
        "flip_run": FLIP_RUN_NAME,
        "n_requested": len(whitelist),
        "n_paired": len(flip_pairs),
        "missing_from_reverified_originals": [list(k) for k in missing_original],
        "missing_from_rerun": [list(k) for k in missing_rerun],
        "empty_rerun_candidate_proof": empty_rerun_candidates,
        "flip_stats": stats,
        "verifier_drift": drift,
        "generated_at_utc": _utc_now_iso(),
        # Provenance: which sample this report describes, so it self-
        # identifies rather than requiring a reader to hold
        # sample_manifest.json alongside it (see the whitelist provenance
        # self-check above).
        "sample_whitelist_sha256": runner.hash_cell_keys(whitelist),
        "sample_n_measurable_mathlib_population": sample_manifest.get(
            "n_measurable_mathlib_population"
        ),
    }
    report_path = _flip_report_path()
    _flip_run_dir().mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\n=== flip_probe[analyze] {MODEL} ===")
    print(f"  paired cells: {stats['n']} / {len(whitelist)} requested")
    print(
        f"  flip rate (b+c)/n: {stats['flip_rate']:.4f}  "
        f"95% CP CI: [{stats['flip_rate_ci95'][0]:.4f}, {stats['flip_rate_ci95'][1]:.4f}]"
    )
    print(
        f"  b (orig pass, rerun fail): {stats['b_orig_pass_rerun_fail']}   "
        f"c (orig fail, rerun pass): {stats['c_orig_fail_rerun_pass']}"
    )
    print(f"  implied SE on pass@1: {stats['pass_at_1_se']:.4f}  (see caveat in report JSON)")
    print(
        f"  verifier-drift agreement (reverified vs. study-stored): "
        f"{drift['agree']}/{drift['n']} = {drift['agreement_rate']:.4f}"
    )
    if empty_rerun_candidates["prompt_tokens_gt_0"]:
        print(
            f"  WARNING: {empty_rerun_candidates['prompt_tokens_gt_0']} rerun "
            "cell(s) have an empty candidate_proof despite prompt_tokens > 0 -- "
            "possible transport-fault signature (streaming was left OFF for "
            "this run's generation; see the module docstring's "
            "'Streaming transport' note)."
        )
    print(f"report: {report_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--stage", required=True, choices=["sample", "generate", "verify", "analyze"],
        help="which phase to run -- see the module docstring's STAGES section",
    )
    ap.add_argument(
        "--n", type=int, default=N_SAMPLE,
        help=f"(sample only) sample size (default: {N_SAMPLE}, the locked design value)",
    )
    ap.add_argument(
        "--seed", type=int, default=SAMPLE_SEED,
        help=f"(sample only) random.Random seed (default: {SAMPLE_SEED}, the locked design value)",
    )
    ap.add_argument(
        "--workers", type=int, default=4,
        help="(verify only) lean_verify_rows.verify_run ThreadPoolExecutor worker count",
    )
    ap.add_argument(
        "--regions", default="us-east-2,us-west-2,us-east-1",
        help="(generate only) EC2_REGIONS candidate list for capacity hunting",
    )
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.stage == "sample":
        _stage_sample(args)
    elif args.stage == "generate":
        _stage_generate(args)
    elif args.stage == "verify":
        _stage_verify(args)
    elif args.stage == "analyze":
        _stage_analyze(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
