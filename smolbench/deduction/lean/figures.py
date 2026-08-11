"""Shared helpers for figure scripts.

Every figure script under ``notebooks/deduction/figures/`` reads replicate rows
from ``<results_root>/runs/<run>/all_rows.jsonl`` (one JSON object per
(model, theorem, k, rung, replicate) cell, where ``results_root`` defaults to
``smolbench.deduction.lean.runner.results_root()``) and slices/aggregates them over a
shared "rung" vocabulary — the experimental condition each replicate was run
under: no hint (``stepk:2``), a positive-information hint level
(``hint:0``..``hint:3``), or a volume-matched noise control
(``noise:1``..``noise:3``).

This module itself lives under ``smolbench/deduction/lean/`` (an installed package)
rather than alongside the figure scripts it serves (``notebooks/deduction/
figures/``) — see `load_rows` and `figure_out_path` for how each accounts
for that split (a lazily-imported results root, and an explicit output
directory, respectively).

This module centralizes the logic that was previously copy-pasted (and had
begun to drift) across the six figure scripts:

- row loading (`load_rows`) and per-run model bookkeeping (`models_per_run`)
- the hint/noise rung vocabulary and rung-to-label conventions (`HINT_RUNGS`,
  `HINT_LABELS`, `HINT_LABELS_VERBOSE`, `NOISE_RUNGS`, `NOISE_RUNGS_ALIGNED`)
- the reasoning-vs-non-reasoning model split (`is_reasoning`)
- the model-exclusion list (`EXCLUDE_MODELS`)
- the "trivial-skip" intersection filter (`trivial_skip_keys`)
- model-family color-grouping helpers used by the two bar-chart scripts
  (`model_family`, `family_color_map`, `lighten`, `family_idx`,
  `order_within_group`)
- the shared `--runs` CLI flag (`parse_runs_args`) and the `plt.savefig`
  footer every script ends with (`save_figure`, `figure_out_path`)
- the "solvable-subset bucket" data-prep pipeline shared by the two hint+
  noise trendline scripts (`build_success_buckets`, `SuccessBuckets`)

Each figure script still owns its own plotting logic (and, where its
data-prep pipeline is not one of the shared ones above, its own filtering);
only the conventions actually common to multiple scripts live here.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# CLI / figure-output helpers
# ---------------------------------------------------------------------------
#
# Every figure script accepts the same `--runs` flag and ends with the same
# `plt.tight_layout(); ...; plt.savefig(...); print(...)` footer; both were
# copy-pasted six times (with the `--runs` help text drifting — three
# scripts had it, three didn't) before being centralized here.

# DEFAULT_RUNS is intentionally empty. The now-archived `main_v3`/`main_v3_2`
# sweeps this used to default to are retired, and the current study's run
# directories are named `scaling_<model>` (one per model) rather than a
# fixed pair of shared sweeps -- there is no single canonical merge set to
# fall back to any more. Callers must pass `--runs` explicitly, naming the
# `scaling_<model>` (or other) run directories under `<results_root>/runs/`
# they want merged.
DEFAULT_RUNS: list[str] = []

# DEFAULT_FIGSIZE is the (width, height) inches five of the six figure
# scripts pass to `plt.subplots(figsize=...)` — every script except
# `prompt_length_vs_hint.py`, whose single-panel box plot genuinely wants a
# narrower, taller figure (8, 5) and keeps that value locally rather than
# overriding this default.
DEFAULT_FIGSIZE = (14, 5.5)


def parse_runs_args() -> list[str]:
    """Parse the `--runs` command-line flag shared by every figure script.

    Every figure script accepts an identical `--runs` flag (one or more run
    directory names under `results/runs/` to merge, via `load_rows`) and
    nothing else; this factors out the six copy-pasted `argparse.ArgumentParser`
    blocks (which had begun to drift — some had a `help=` string, some
    didn't) into one canonical definition.

    Returns
    -------
    list of str
        The parsed `--runs` values, defaulting to `DEFAULT_RUNS` (empty --
        see that constant's comment) when the flag is omitted, in which case
        every downstream `load_rows` call sees an empty run list and no rows
        load. There is no current canonical merge set: run directories are
        named `scaling_<model>` (one per model) under `<results_root>/runs/`,
        so callers must pass `--runs` explicitly to name the ones they want
        merged. (Returns the raw list, not the `argparse.Namespace`, since
        every caller immediately does `args.runs` and nothing else with the
        parsed arguments.)

    Notes
    -----
    Calls `sys.exit` (via `argparse`) on `-h`/`--help` or malformed
    arguments, matching standard `argparse` CLI behavior.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--runs", nargs="+", default=DEFAULT_RUNS,
        help=(
            "run dirs under results/runs/ to merge, e.g. scaling_<model> "
            "(default: %(default)s -- no canonical set, must be passed explicitly)"
        ),
    )
    return ap.parse_args().runs


def figure_out_path(name: str, out_dir: Path) -> Path:
    """Resolve the output PNG path for a figure script, by figure name.

    Parameters
    ----------
    name : str
        The figure's base filename without extension (conventionally the
        script's own module name, e.g. `"success_rate_bars"`).
    out_dir : pathlib.Path
        Directory the PNG is written into. Callers pass their own
        `Path(__file__).parent` (i.e. `notebooks/deduction/figures/`) explicitly.

        Design: this module now lives under `smolbench/deduction/lean/` (an installed
        package, potentially imported from anywhere) while the figure
        scripts and their PNG outputs live under `notebooks/deduction/figures/` —
        two different directories. The previous version of this function
        introspected *its own* `__file__` to anchor the output path, which
        was correct back when `_util.py` and the figure scripts were
        siblings in `lean/figures/`; now that they live in different
        packages entirely, this module has no way to know the scripts'
        directory on its own, so callers must supply it explicitly rather
        than this function guessing (or reaching for a fragile caller-frame
        introspection trick).

    Returns
    -------
    pathlib.Path
        `<out_dir>/<name>.png`.
    """
    return out_dir / f"{name}.png"


def save_figure(out_path: Path) -> None:
    """Finalize the current matplotlib figure and write it to `out_path`.

    Runs the footer every figure script previously copy-pasted: tighten the
    layout, ensure the output directory exists, save at a fixed DPI, and log
    the path written.

    Parameters
    ----------
    out_path : pathlib.Path
        Destination PNG path (typically from `figure_out_path`). Parent
        directories are created if missing.

    Notes
    -----
    Operates on the current pyplot figure (`plt.gcf()` implicitly, via
    `plt.tight_layout()`/`plt.savefig()`) rather than taking a `Figure`
    object explicitly — matches every figure script's existing style of
    calling bare `plt.tight_layout()`/`plt.savefig()` after building exactly
    one figure per script invocation.

    The DPI (140) is fixed rather than parameterized: no script previously
    varied it, and the byte-for-byte PNG comparison used to verify this
    refactor depends on it staying fixed.
    """
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=140)
    print(f"saved {out_path}")


# ---------------------------------------------------------------------------
# Rung vocabulary
# ---------------------------------------------------------------------------
#
# HINT_RUNGS is the "positive information" ladder: `stepk:2` carries no
# premise leak at all, and `hint:0..3` progressively reveal more about the
# true next tactic's premises (names -> signatures -> bodies -> 1-hop
# dependency closure). It is the x-axis for every hint/rate/length plot.
HINT_RUNGS = ["stepk:2", "hint:0", "hint:1", "hint:2", "hint:3"]

# Two label sets are in use across the figure scripts, and BOTH are
# preserved here (rather than collapsed to one) because they render
# different text on different figures:
#
#   HINT_LABELS          terse axis ticks: "no hint", "hint 1".."hint 4"
#                         (response_length_per_model_rung.py,
#                         success_rate_per_model_rung.py,
#                         success_rate_with_noise.py)
#   HINT_LABELS_VERBOSE   descriptive "degree of positive information" ticks
#                         (success_rate_bars.py)
#
# Both use the same shift: displayed level N corresponds to internal
# `hint:(N-1)` (`stepk:2` displays as level 0 / "no hint"/"None"). See the
# NOISE_RUNGS_ALIGNED docstring below for how this shift also applies to the
# noise rungs.
HINT_LABELS = ["no hint", "hint 1", "hint 2", "hint 3", "hint 4"]
HINT_LABELS_VERBOSE = ["None", "1: Names", "2: Signatures", "3: Derivations", "4: 1-hop deriv."]

# NOISE_RUNGS is the plain list of noise (volume-control) rungs, each
# padded-filler-token-matched to the hint rung of the same internal number
# (noise:1 is padded to hint:1's token count, etc). Used wherever the noise
# rungs need to be considered as a flat set (e.g. building the "solvable at
# any hint/noise rung" filter, or the trivial-skip intersection).
NOISE_RUNGS = ["noise:1", "noise:2", "noise:3"]

# NOISE_RUNGS_ALIGNED is NOISE_RUNGS positioned to line up with HINT_RUNGS /
# HINT_LABELS on a shared x-axis, for scripts that draw a noise trendline
# alongside the hint trendline (response_length_per_model_rung.py,
# success_rate_per_model_rung.py, success_rate_with_noise.py).
#
# DESIGN NOTE — the rung-label shift: there is no noise control for the
# `stepk:2` ("no hint") or `hint:0` ("hint 1") positions (there is nothing to
# volume-match a hint of "no premise info" or "just names" against), so the
# first two slots are None. This means `noise:1` sits at x-position 2 in
# HINT_LABELS terms ("hint 2"), even though its *internal* rung number is 1.
# Colloquially this has been described elsewhere in this codebase as "user
# labels shifted up by 1, so internal noise:1 == user 'noise 2'" — i.e. if
# you were to label the noise rungs analogously to HINT_LABELS ("noise 1"
# .."noise 4"), the padded-to-hint:1 rung would be called "noise 2" (it sits
# at the same x-position as "hint 2"), not "noise 1". NOISE_RUNGS_ALIGNED
# encodes this shift structurally (via the two leading Nones) instead of via
# a separate NOISE_LABELS list, so callers index NOISE_RUNGS_ALIGNED and
# HINT_RUNGS/HINT_LABELS with the same x-position.
NOISE_RUNGS_ALIGNED = [None, None] + NOISE_RUNGS

# Models dropped from every cross-model figure. `v3.2-speciale` is DeepSeek
# V3.2's separate, always-on reasoning fine-tune (see configs/main_v3.yaml) —
# unlike the `*-high` / `*-none` toggle pairs (gemini-flash, kimi-k2.6,
# v3.2-high/v3.2-none) it has no reasoning-off sibling, so it doesn't fit the
# toggle-pair family/color grouping these figures are built around: including
# it would put a second "deepseek family, reasoning" bar/line alongside
# v3.2-high with no matching non-reasoning counterpart to pair it against.
EXCLUDE_MODELS = {"v3.2-speciale"}


def is_reasoning(model_name: str) -> bool:
    """Classify a model's display name as reasoning or non-reasoning.

    Parameters
    ----------
    model_name : str
        A row's `model` field (the config's `display_name`, e.g.
        `"v3.2-high"`, `"gemini-flash-none"`, `"v3.2-speciale"`).

    Returns
    -------
    bool
        True if the name contains ``"high"``, ``"thinking"``, or
        ``"speciale"`` (case-insensitively) — the markers used across the
        model configs (see `configs/main_v3.yaml`) for reasoning-mode
        variants and the always-on DeepSeek speciale fine-tune.

    Notes
    -----
    This mirrors (independently) the reasoning heuristic used at collection
    time in `smolbench/deduction/lean/runner.py`'s `_is_reasoning`, which additionally checks
    `extra_params.reasoning_effort` before falling back to the substring
    check. Figure scripts only see display names, not model configs, so they
    use the substring-only fallback.
    """
    n = model_name.lower()
    return ("high" in n) or ("thinking" in n) or ("speciale" in n)


def load_rows(runs: list[str], results_root: Path | None = None) -> list[dict]:
    """Load and concatenate `all_rows.jsonl` rows for a list of run names.

    Each row is tagged with a `_run` key identifying which run directory it
    came from (needed by `models_per_run` to determine, e.g., which models
    are only present in the smaller `main_v3_2` sweep). Scripts that never
    consult `_run` are unaffected by the extra key.

    Parameters
    ----------
    runs : list of str
        Run directory names under `<results_root>/runs/` (e.g. `["main_v3",
        "main_v3_2"]`).
    results_root : pathlib.Path or None, default None
        Root of the results tree, i.e. the directory containing `runs/`.
        Each run resolves to `<results_root>/runs/<run>/all_rows.jsonl`. If
        `None` (the default used by every figure script), resolved via
        `smolbench.deduction.lean.runner.results_root()`.

        Design: the import of `runner.results_root` is deliberately LAZY
        (done here, inside the function body, rather than at module level).
        `runner.py` pulls in the whole sweep engine — context/premise
        rendering (tiktoken) and the provider dispatch stack — which is far
        heavier than anything else this `figures` module needs, so a bare
        `import smolbench.deduction.lean.figures` stays cheap. (It does NOT pull in
        LeanDojo: the runner loads `verify.py` lazily through its
        `verifier=` seam, which is why the figure scripts run on the main
        3.14 venv.) Callers who already have a `results_root` handy (e.g. a
        caller under test, or a notebook that resolved it once) can pass it
        explicitly and skip the import entirely.

    Returns
    -------
    list of dict
        One dict per non-blank JSONL line across all requested runs, each
        with an added `_run` key. Order is run-major, then file order within
        a run. Rows are not deduplicated or filtered here.

    Notes
    -----
    Missing run directories are skipped with a printed warning rather than
    raising, since figure scripts are commonly re-run against whichever
    subset of sweeps happens to be checked out locally.
    """
    if results_root is None:
        # Lazy import — see the parameter docstring above for why.
        from .runner import results_root as _results_root
        results_root = _results_root()
    rows = []
    for run in runs:
        path = results_root / f"runs/{run}/all_rows.jsonl"
        if not path.exists():
            print(f"warning: {path} missing, skipping")
            continue
        for l in path.open():
            if not l.strip():
                continue
            r = json.loads(l)
            r["_run"] = run
            rows.append(r)
    return rows


def models_per_run(rows: list[dict]) -> dict[str, set[str]]:
    """For each run present in `rows`, the set of models contributing rows.

    Parameters
    ----------
    rows : list of dict
        Rows produced by `load_rows` (each must carry a `_run` key and, for
        real replicate rows, a `model` key).

    Returns
    -------
    dict of str to set of str
        Maps run name to the set of `model` display names with at least one
        row in that run. Rows without a `model` field (e.g. summary/meta
        rows) are ignored.
    """
    out: dict[str, set[str]] = {}
    for r in rows:
        if r.get("model"):
            out.setdefault(r["_run"], set()).add(r["model"])
    return out


def trivial_skip_keys(rows: list[dict], rungs: list[str]) -> set[tuple]:
    """Intersection of (theorem_id, k) pairs present at every given rung.

    Some (theorem, k) cells are "trivial-skipped" at collection time for
    certain rungs (e.g. already solved, or not applicable), so not every
    theorem contributes a row at every rung. Restricting to the intersection
    keeps cross-rung comparisons (bar heights, trendline points) apples-to-
    apples: every plotted rung is describing the exact same set of theorems.

    Parameters
    ----------
    rows : list of dict
        Rows to scan (typically the `real` subset of `load_rows` output,
        i.e. rows with a non-empty `model` field — though this function
        itself does not filter on `model`).
    rungs : list of str
        Rung names whose presence must be checked (e.g. `HINT_RUNGS`, or
        `HINT_RUNGS + NOISE_RUNGS` for figures that also draw noise
        trendlines).

    Returns
    -------
    set of tuple
        Set of `(theorem_id, k)` pairs that have at least one row at every
        rung in `rungs`.

    Raises
    ------
    ValueError
        If `rungs` is empty (there is nothing to intersect).
    """
    if not rungs:
        raise ValueError("rungs must be non-empty")
    rung_to_keys: dict[str, set[tuple]] = {r: set() for r in rungs}
    for r in rows:
        rung = r.get("rung")
        if rung in rung_to_keys:
            rung_to_keys[rung].add((r.get("theorem_id"), r.get("k")))
    return set.intersection(*rung_to_keys.values())


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


# ---------------------------------------------------------------------------
# Model-family color grouping (success_rate_bars.py, marginal_content_vs_noise.py)
# ---------------------------------------------------------------------------
#
# Both scripts draw one bar/set of bars per model, grouped so that each
# reasoning/non-reasoning "toggle pair" (e.g. gemini-flash-high /
# gemini-flash-none) shares a single family color: the reasoning member in
# the saturated color, the non-reasoning member in a lightened blend of it.
FAMILY_ORDER = ["gemini", "kimi", "deepseek", "gpt-5.5", "sonnet-4.6"]


def model_family(model: str) -> str:
    """Map a model display name to its color-grouping family.

    Parameters
    ----------
    model : str
        A row's `model` field, e.g. `"gemini-flash-high"`, `"v3.2-none"`.

    Returns
    -------
    str
        One of `FAMILY_ORDER`'s entries if the name matches a known prefix,
        otherwise `model` itself unchanged (so unrecognized models still get
        a stable (if unshared) "family" to key off of).
    """
    if model.startswith("gemini-flash-"):
        return "gemini"
    if model.startswith("kimi-k2.6-"):
        return "kimi"
    if model.startswith("v3.2-"):
        return "deepseek"
    if model.startswith("gpt-5.5-"):
        return "gpt-5.5"
    if model.startswith("sonnet-4.6-"):
        return "sonnet-4.6"
    return model


def family_color_map(cmap_name: str = "tab10") -> dict[str, tuple]:
    """Assign one color per `FAMILY_ORDER` entry from a matplotlib colormap.

    Parameters
    ----------
    cmap_name : str, default "tab10"
        Name of a registered matplotlib colormap, sampled once per family in
        `FAMILY_ORDER` order (so re-running with the same colormap always
        assigns the same family the same color).

    Returns
    -------
    dict of str to tuple
        Maps each family name to an RGBA tuple.
    """
    cmap = plt.get_cmap(cmap_name)
    return {f: cmap(i) for i, f in enumerate(FAMILY_ORDER)}


def lighten(c, factor: float = 0.55) -> tuple:
    """Blend a color toward white, for a family's non-reasoning sibling swatch.

    Parameters
    ----------
    c : color-like
        Any value accepted by `matplotlib.colors.to_rgb` (e.g. an RGBA
        tuple, hex string, or named color).
    factor : float, default 0.55
        Fraction of the distance from `c` to white to travel. 0 returns `c`
        unchanged; 1 returns white.

    Returns
    -------
    tuple of float
        The blended RGB tuple (alpha channel, if any, is dropped since
        `to_rgb` discards it).
    """
    rgb = mcolors.to_rgb(c)
    return tuple(rgb[i] + (1.0 - rgb[i]) * factor for i in range(3))


def family_idx(model: str) -> int:
    """Sort index of `model`'s family within `FAMILY_ORDER`.

    Parameters
    ----------
    model : str
        A model display name (see `model_family`).

    Returns
    -------
    int
        Position of `model_family(model)` in `FAMILY_ORDER`, or 999 if the
        family is not one of the known ones (sorts unknown families last).
    """
    f = model_family(model)
    return FAMILY_ORDER.index(f) if f in FAMILY_ORDER else 999


def order_within_group(models, low_n_models: set[str]) -> list:
    """Sort models for display within a reasoning/non-reasoning group.

    Full-n models (present in the larger `main_v3` sweep) are ordered
    before low-n models (only present in `main_v3_2`), so low-n models sit
    at the right edge of each group's bar/legend block; within each of those
    two buckets, models are ordered by family (per `FAMILY_ORDER`) and then
    alphabetically, so toggle-pair siblings land adjacent to each other.

    Parameters
    ----------
    models : iterable of str
        Model display names to order (typically all reasoning-flagged or
        all non-reasoning-flagged models present in the figure's data).
    low_n_models : set of str
        Model names considered "low-n" (i.e. absent from `main_v3`).

    Returns
    -------
    list of str
        `models` sorted as described above. Does not mutate `models`.
    """
    return sorted(models, key=lambda m: (1 if m in low_n_models else 0, family_idx(m), m))


# ---------------------------------------------------------------------------
# Solvable-subset success bucket (success_rate_per_model_rung.py,
# success_rate_with_noise.py)
# ---------------------------------------------------------------------------
#
# Both of these scripts build a (model, rung) -> [verdict] bucket by the
# exact same ~40-line pipeline (trivial-skip intersection -> per-model
# "solvable at some hint/noise rung" set -> verdict bucket restricted to
# both -> low-n model tagging -> reasoning/non-reasoning split), differing
# only in which rungs the trivial-skip intersection is computed over. That
# pipeline is centralized here as `build_success_buckets`.
#
# response_length_per_model_rung.py and success_rate_bars.py have
# structurally similar (but NOT identical) pipelines:
#   - response_length_per_model_rung.py accumulates `completion_tokens`
#     values keyed by (model, rung) instead of `verdict` strings, and has no
#     accepted-verdict allowlist check (its own "is this row usable" test is
#     `completion_tokens > 0`) — a genuinely different bucket value type and
#     filter, not just a parameter difference.
#   - success_rate_bars.py's pipeline is actually parameter-identical to
#     `build_success_buckets(real, HINT_RUNGS, NOISE_RUNGS)` (its default
#     `keep_rungs`), but it additionally needs `order_within_group`/
#     `family_color_map`-based grouping rather than the plain
#     reasoning/non_reasoning split this helper returns, so folding it in
#     would mean immediately discarding half of `SuccessBuckets`.
# Per the refactor spec this helper was written for, only the two scripts
# with a genuinely identical pipeline (module docstring above) were folded
# in; the other two were deliberately left as-is rather than forced into a
# shape that doesn't fit them.
@dataclass(frozen=True)
class SuccessBuckets:
    """Container for `build_success_buckets`'s outputs.

    A small dataclass (rather than a plain tuple) so call sites read
    `result.bucket`, `result.reasoning`, etc. by name instead of position —
    with five differently-shaped return values (a dict, a set of str, two
    lists of str, and a set of tuples) a positional tuple would be an easy
    place to introduce a silent transposition bug (e.g. swapping
    `low_n_models` and `keep`, both sets).

    Attributes
    ----------
    bucket : dict of (str, str) to list of str
        Maps `(model, rung)` to the list of `verdict` strings observed for
        that cell, after all of `build_success_buckets`'s filtering.
    low_n_models : set of str
        Models present in `bucket` but absent from the `main_v3` run (i.e.
        contributing rows only via the smaller `main_v3_2` sweep) — callers
        plot these at reduced alpha.
    reasoning : list of str
        Reasoning-flagged models (`is_reasoning`) present in `bucket`,
        ordered by `model_sort_key` (full-n models first, alphabetical
        within each of the full-n/low-n groups).
    non_reasoning : list of str
        Non-reasoning models present in `bucket`, ordered the same way as
        `reasoning`.
    keep : set of tuple
        The `(theorem_id, k)` intersection set `bucket` was restricted to —
        exposed so callers can log its size (both current callers print
        `f"... {len(sb.keep)}"` with their own wording, since the two
        scripts describe slightly different rung sets).
    """

    bucket: dict[tuple[str, str], list[str]]
    low_n_models: set[str]
    reasoning: list[str]
    non_reasoning: list[str]
    keep: set[tuple]


def build_success_buckets(
    real: list[dict],
    hint_rungs: list[str],
    noise_rungs: list[str | None],
    *,
    keep_rungs: list[str] | None = None,
) -> SuccessBuckets:
    """Build the (model, rung) -> [verdict] bucket shared by the hint/noise
    success-rate trendline figures.

    Implements, in order:

    1. Restrict to the `(theorem_id, k)` pairs present at every rung in
       `keep_rungs` (via `trivial_skip_keys`), so every rung plotted on a
       shared x-axis describes the exact same set of theorems.
    2. Compute, per model, the set of `(theorem_id, k)` pairs that model
       solved (`verdict == "success"`) at *some* hint rung beyond the first
       or *some* noise rung — the "solvable" set.
    3. Build the verdict bucket: for each row with a recognized verdict
       (`"success"`, `"lean_error"`, `"exception"`, `"incomplete"` — other
       verdicts, e.g. `"timeout"`, are silently dropped) whose model is not
       in `EXCLUDE_MODELS` and whose `(theorem_id, k)` survived step 1,
       accumulate its `verdict` into `bucket[(model, rung)]`. The `stepk:2`
       ("no hint") cell is further restricted, per model, to that model's
       own "solvable" set from step 2 — so the no-hint baseline reflects
       only theorems the model could solve *somewhere*, not hopeless ones.
    4. Tag `low_n_models`: models present in `bucket` but not in the
       `main_v3` run (`models_per_run`), for reduced-alpha plotting.
    5. Split the bucket's models into `reasoning`/`non_reasoning` lists
       (`is_reasoning`), each ordered by `model_sort_key`.

    Parameters
    ----------
    real : list of dict
        Rows already filtered to `r.get("model")` truthy (i.e. the `real`
        subset of `load_rows`'s output — this function does not itself
        filter out summary/meta rows).
    hint_rungs : list of str
        The hint-ladder rungs (conventionally `_util.HINT_RUNGS`:
        `stepk:2`, `hint:0`..`hint:3`). `hint_rungs[0]` is treated as the
        "no hint" rung subject to the step-2 solvability restriction; the
        rest are treated as positive-information rungs.
    noise_rungs : list of str or None
        The noise-ladder rungs, aligned to `hint_rungs` by position
        (conventionally `_util.NOISE_RUNGS_ALIGNED`, whose leading `None`
        entries mark hint positions with no noise counterpart). `None`
        entries are dropped before use.
    keep_rungs : list of str or None, default None
        Rungs to intersect over in step 1. Defaults to `hint_rungs` when
        omitted — matching `success_rate_per_model_rung.py`'s "present at
        every hint level" restriction. Pass `hint_rungs + noise_present` to
        additionally require every noise rung, matching
        `success_rate_with_noise.py`'s "present at every (hint, noise)
        level" restriction (this is the one input difference between the
        two scripts' otherwise-identical pipelines).

    Returns
    -------
    SuccessBuckets
        See `SuccessBuckets` for field documentation.

    Raises
    ------
    ValueError
        Propagated from `trivial_skip_keys` if the effective `keep_rungs`
        (after defaulting) is empty.

    Notes
    -----
    Time complexity is O(len(real)) for each of the two passes over `real`
    (steps 2 and 3), plus the O(len(real)) work inside `trivial_skip_keys`
    and `models_per_run` — linear overall in the number of input rows.
    """
    noise_present = [r for r in noise_rungs if r is not None]
    if keep_rungs is None:
        keep_rungs = hint_rungs
    keep = trivial_skip_keys(real, keep_rungs)

    # Per-model "solved somewhere beyond the bare no-hint rung" set, used
    # below to restrict the stepk:2 cell to theorems this model could
    # actually make progress on (rather than diluting it with theorems the
    # model was always going to fail regardless of hint/noise).
    hint_noise_rungs = hint_rungs[1:] + noise_present
    solvable: set[tuple] = set()
    for r in real:
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        if r.get("rung") in hint_noise_rungs and r.get("verdict") == "success":
            solvable.add((r.get("model"), r.get("theorem_id"), r.get("k")))

    bucket: dict[tuple[str, str], list[str]] = {}
    for r in real:
        m = r.get("model")
        if m in EXCLUDE_MODELS:
            continue
        rung = r.get("rung")
        v = r.get("verdict")
        if v not in ("success", "lean_error", "exception", "incomplete"):
            continue
        if (r.get("theorem_id"), r.get("k")) not in keep:
            continue
        # Design: both original call sites hardcoded the literal "stepk:2"
        # here; generalized to `hint_rungs[0]` since that's exactly what
        # "stepk:2" *means* in both callers (the no-hint rung) and this
        # function otherwise treats `hint_rungs[0]` as that rung throughout
        # (see the `hint_noise_rungs = hint_rungs[1:] + ...` line above) —
        # for both current callers `hint_rungs[0] == "stepk:2"`, so this is
        # a zero-behavior-change generalization, not a semantic one.
        if rung == hint_rungs[0]:
            triple = (m, r.get("theorem_id"), r.get("k"))
            if triple not in solvable:
                continue
        bucket.setdefault((m, rung), []).append(v)

    by_run = models_per_run(real)
    main_v3_models = by_run.get("main_v3", set())
    low_n_models = {m for m in {k[0] for k in bucket} if m not in main_v3_models}

    models = sorted({k[0] for k in bucket}, key=lambda m: model_sort_key(m, low_n_models))
    reasoning = [m for m in models if is_reasoning(m)]
    non_reasoning = [m for m in models if not is_reasoning(m)]

    return SuccessBuckets(bucket, low_n_models, reasoning, non_reasoning, keep)
