"""Shared helpers for figure scripts.

Every figure script under ``lean/figures/`` reads rollout rows from
``results/runs/<run>/all_rows.jsonl`` (one JSON object per (model, theorem,
k, rung, rollout) cell) and slices/aggregates them over a shared "rung"
vocabulary — the experimental condition each rollout was run under: no hint
(``stepk:2``), a positive-information hint level (``hint:0``..``hint:3``), or
a volume-matched noise control (``noise:1``..``noise:3``).

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

Each figure script still owns its own plotting/argparse logic; only the data
loading and filtering conventions common to multiple scripts live here.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

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
    time in `leaneval/runner.py`'s `_is_reasoning`, which additionally checks
    `extra_params.reasoning_effort` before falling back to the substring
    check. Figure scripts only see display names, not model configs, so they
    use the substring-only fallback.
    """
    n = model_name.lower()
    return ("high" in n) or ("thinking" in n) or ("speciale" in n)


def load_rows(runs: list[str]) -> list[dict]:
    """Load and concatenate `all_rows.jsonl` rows for a list of run names.

    Each row is tagged with a `_run` key identifying which run directory it
    came from (needed by `models_per_run` to determine, e.g., which models
    are only present in the smaller `main_v3_2` sweep). Scripts that never
    consult `_run` are unaffected by the extra key.

    Parameters
    ----------
    runs : list of str
        Run directory names under `results/runs/` (e.g. `["main_v3",
        "main_v3_2"]`). Resolved relative to this file's parent's parent
        (the `lean/` directory), i.e. `lean/results/runs/<run>/all_rows.jsonl`.

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
    root = Path(__file__).resolve().parents[1]
    rows = []
    for run in runs:
        path = root / f"results/runs/{run}/all_rows.jsonl"
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
        real rollout rows, a `model` key).

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
