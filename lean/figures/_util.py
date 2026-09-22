"""Shared analysis layer for figure scripts.

Every figure imports its data loading, level registry, model classification,
analysis set, pass rates, and bootstrap intervals from here. Keep this the
single source of truth so figures cannot disagree about which rows, levels,
models, or denominators they use.

Level registry
--------------
The paper defines five cumulative levels of positive information. They map
onto the harness rungs as follows (see leaneval/context.py):

    None            stepk:2   state + prior tactics + theorem identity
    MPI             hint:0    + names of premises in the true next tactic
    MPI+Signatures  hint:1    + type signatures
    One-Hop         hint:2    + full source bodies of those premises
    Two-Hop         hint:3    + 1-hop dependency closure, full bodies

`hint:4` (2-hop closure) is not a paper level. `noise:N` is `hint:(N-1)`
padded with lorem ipsum to `hint:N`'s token count, so `hint:N - noise:N` is
the marginal effect of the Nth step's content at matched length.

Analysis set
------------
Trivial-rung skipping in the sweep is per rung, so raw per-level theorem
counts differ. `load_analysis` builds one set per model: (theorem, k) pairs
with at least one scored row at EVERY rung in `ANALYSIS_RUNGS` for that
model. Rows with infrastructure verdicts (`exception`, `replay_failed`) are
missing data and never enter a denominator.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Run dirs under results/runs/ merged by default. The `_rescored` dirs are
# produced by `leaneval rescore` (current splitter + verdict taxonomy).
DEFAULT_RUNS = ["main_v3_rescored", "main_v3_2_rescored"]
# Runs that cover the full 100-theorem sample. Models appearing only in
# other runs (the frontier subset) are plotted at reduced alpha.
FULL_SIZE_RUNS = {"main_v3", "main_v3_rescored"}

# Models dropped from every figure.
EXCLUDE_MODELS = {"v3.2-speciale"}

# (rung, paper label), in paper order.
LEVELS = [
    ("stepk:2", "None"),
    ("hint:0", "MPI"),
    ("hint:1", "MPI+Signatures"),
    ("hint:2", "One-Hop"),
    ("hint:3", "Two-Hop"),
]
LEVEL_LABEL = dict(LEVELS)
NONE_RUNG = "stepk:2"
MPI_RUNG = "hint:0"
HINT_LEVELS = [(r, lbl) for r, lbl in LEVELS if r != NONE_RUNG]
# (hint rung, matched-length noise rung, label) for the marginal comparison.
NOISE_PAIRS = [
    ("hint:1", "noise:1", "MPI+Signatures"),
    ("hint:2", "noise:2", "One-Hop"),
    ("hint:3", "noise:3", "Two-Hop"),
]
# Every rung any paper figure uses; the analysis set requires all of them.
ANALYSIS_RUNGS = [r for r, _ in LEVELS] + [n for _, n, _ in NOISE_PAIRS]

# Mirror of leaneval.verify.SCORED_VERDICTS (figures do not import leaneval).
SCORED_VERDICTS = frozenset(
    {"success", "lean_error", "incomplete", "given_up", "timeout", "truncated"}
)

# Open-weight: publicly released weights.
# Closed-weight: proprietary, API-only access.
OPEN_WEIGHT_FAMILIES = {"deepseek", "kimi"}
CLOSED_WEIGHT_FAMILIES = {"gemini", "gpt-5.5", "sonnet-4.6"}

# Canonical family ordering. Colors are assigned by index into tab10, so this
# list must stay stable or the same model changes color between figures.
FAMILY_ORDER = ["gemini", "kimi", "deepseek", "gpt-5.5", "sonnet-4.6"]

BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 0


# ---------------------------------------------------------------------------
# Model naming
# ---------------------------------------------------------------------------


def pretty_model(name: str) -> str:
    """Display name for a model row's `model` field."""
    if name.startswith("v3.2-"):
        return f"deepseek {name}"
    return name


def model_family(name: str) -> str:
    if name.startswith("gemini-flash-"): return "gemini"
    if name.startswith("kimi-k2.6-"): return "kimi"
    if name.startswith("v3.2-"): return "deepseek"
    if name.startswith("gpt-5.5-"): return "gpt-5.5"
    if name.startswith("sonnet-4.6-"): return "sonnet-4.6"
    return name


def is_open_weight(name: str) -> bool:
    return model_family(name) in OPEN_WEIGHT_FAMILIES


def is_reasoning(model_name: str) -> bool:
    """Display-name heuristic for the CoT / non-CoT split.

    Caveat: this reads the row's display name only. The sweep itself decides
    reasoning mode from the model config (see runner._is_reasoning, which also
    consults extra_params.reasoning_effort); the two agree for every model in
    the default runs but can diverge for names lacking these substrings
    (e.g. deepseek-r1-0528 in noise_iso_r1_v1).
    """
    n = model_name.lower()
    return ("high" in n) or ("thinking" in n) or ("speciale" in n)


def model_sort_key(name: str, low_n: set[str]) -> tuple:
    """Order: open-weight first, closed-weight second. Within each group,
    full-n before low-n, then alphabetical."""
    return (0 if is_open_weight(name) else 1,
            1 if name in low_n else 0,
            name)


def family_palette():
    """family -> tab10 color, keyed by FAMILY_ORDER index."""
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap("tab10")
    return {f: cmap(i) for i, f in enumerate(FAMILY_ORDER)}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _cell_key(r):
    return (r.get("model"), r.get("theorem_id"), r.get("k"), r.get("rung"), r.get("rollout_idx"))


def load_rows(runs):
    """Load all_rows.jsonl for each run dir, tagging rows with `_run`.

    Later runs supersede earlier ones: when the same cell (model, theorem,
    k, rung, rollout) appears in more than one listed run, or more than once
    within a run (a resumed retry), only the last occurrence is kept. This is
    how a re-run of a rung (e.g. `main_v4_rerun` after the derivation-closure
    change) replaces the stale rows of an earlier run without editing it.
    """
    by_key = {}
    order = []
    for run in runs:
        path = ROOT / f"results/runs/{run}/all_rows.jsonl"
        if not path.exists():
            print(f"warning: {path} missing, skipping")
            continue
        for l in path.open():
            if not l.strip():
                continue
            r = json.loads(l)
            r["_run"] = run
            if r.get("kind") == "cell":
                key = _cell_key(r)
                if key not in by_key:
                    order.append(key)
                by_key[key] = r
            else:
                order.append(r)
    rows = []
    for item in order:
        rows.append(by_key[item] if isinstance(item, tuple) else item)
    return rows


def models_per_run(real):
    """For each run in the data, the set of models contributing rows."""
    out = {}
    for r in real:
        if r.get("model"):
            out.setdefault(r["_run"], set()).add(r["model"])
    return out


def low_n_model_set(real, models):
    """Models absent from the full-size run (frontier, fewer theorems) —
    plotted at reduced alpha."""
    full = set()
    for run, ms in models_per_run(real).items():
        if run in FULL_SIZE_RUNS:
            full |= ms
    return {m for m in models if m not in full}


def add_weight_class_arg(ap):
    """Add --weight-class open|closed|all to an argparse parser."""
    ap.add_argument("--weight-class", choices=["open", "closed", "all"],
                    default="all",
                    help="filter to open-weight, closed-weight, or all models")


def filter_by_weight_class(rows, weight_class):
    """Drop rows whose model doesn't match the requested weight class."""
    if weight_class == "all":
        return rows
    keep_open = (weight_class == "open")
    return [r for r in rows if not r.get("model") or is_open_weight(r["model"]) == keep_open]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


class Analysis:
    """Per-model analysis sets and per-theorem cells over scored rows.

    `cells[(model, rung)][(theorem_id, k)]` is the list of scored rows for
    that cell. Only (theorem, k) pairs in `keep[model]` are stored.
    """

    def __init__(self, rows, rungs):
        real = [r for r in rows if r.get("model") and r["model"] not in EXCLUDE_MODELS]
        scored = [r for r in real if r.get("verdict") in SCORED_VERDICTS]

        # presence[model][rung] = set of (theorem, k) with >= 1 scored row
        presence: dict[str, dict[str, set]] = {}
        for r in scored:
            presence.setdefault(r["model"], {}).setdefault(r["rung"], set()).add(
                (r["theorem_id"], r["k"])
            )
        self.keep: dict[str, set] = {}
        for model, by_rung in presence.items():
            sets = [by_rung.get(rung, set()) for rung in rungs]
            self.keep[model] = set.intersection(*sets) if sets else set()

        self.cells: dict[tuple[str, str], dict[tuple, list[dict]]] = {}
        for r in scored:
            key = (r["theorem_id"], r["k"])
            if key not in self.keep.get(r["model"], ()):
                continue
            self.cells.setdefault((r["model"], r["rung"]), {}).setdefault(key, []).append(r)

        self.models = sorted(m for m, ks in self.keep.items() if ks)
        self.low_n_models = low_n_model_set(real, set(self.models))
        self.rungs = list(rungs)

    def n_theorems(self, model) -> int:
        return len(self.keep.get(model, ()))

    def sorted_models(self, reasoning: bool | None = None):
        ms = [m for m in self.models if reasoning is None or is_reasoning(m) == reasoning]
        return sorted(ms, key=lambda m: model_sort_key(m, self.low_n_models))

    def label(self, model) -> str:
        return f"{pretty_model(model)} (n={self.n_theorems(model)})"

    # -- rates --------------------------------------------------------------

    def _counts(self, model, rung, keys):
        """(successes, scored) pooled over rollouts of the given theorem keys."""
        cell = self.cells.get((model, rung), {})
        s = n = 0
        for key in keys:
            for r in cell.get(key, ()):
                n += 1
                s += r.get("verdict") == "success"
        return s, n

    def rate(self, model, rung) -> float:
        """Pass rate (%) pooled over all rollouts of the model's analysis set;
        NaN when the cell is empty."""
        s, n = self._counts(model, rung, self.keep.get(model, ()))
        return 100 * s / n if n else float("nan")

    def _resamples(self, model):
        keys = sorted(self.keep.get(model, ()))
        rng = random.Random(BOOTSTRAP_SEED)
        for _ in range(BOOTSTRAP_B):
            yield [keys[rng.randrange(len(keys))] for _ in keys]

    def bootstrap_delta(self, model, rung_a, rung_b):
        """`rate(rung_a) - rate(rung_b)` with a 95% paired bootstrap interval.

        Theorems are resampled with replacement and the same resample is used
        for both rungs, so the interval reflects the within-theorem pairing.
        Returns (delta, lo, hi) in percentage points; NaNs if a cell is empty.
        """
        point = self.rate(model, rung_a) - self.rate(model, rung_b)
        if point != point:  # NaN
            return point, point, point
        deltas = []
        for keys in self._resamples(model):
            sa, na = self._counts(model, rung_a, keys)
            sb, nb = self._counts(model, rung_b, keys)
            if na and nb:
                deltas.append(100 * (sa / na - sb / nb))
        if not deltas:
            return point, float("nan"), float("nan")
        deltas.sort()
        lo = deltas[int(0.025 * (len(deltas) - 1))]
        hi = deltas[int(0.975 * (len(deltas) - 1))]
        return point, lo, hi

    def bootstrap_rate(self, model, rung):
        """Pass rate with a 95% bootstrap interval over theorems."""
        point = self.rate(model, rung)
        if point != point:
            return point, point, point
        rates = []
        for keys in self._resamples(model):
            s, n = self._counts(model, rung, keys)
            if n:
                rates.append(100 * s / n)
        rates.sort()
        lo = rates[int(0.025 * (len(rates) - 1))]
        hi = rates[int(0.975 * (len(rates) - 1))]
        return point, lo, hi


def load_analysis(runs, weight_class="all", rungs=ANALYSIS_RUNGS) -> Analysis:
    rows = filter_by_weight_class(load_rows(runs), weight_class)
    a = Analysis(rows, rungs)
    print(f"runs: {list(runs)}, weight_class: {weight_class}")
    print("analysis set (theorems present at every level, per model): "
          + ", ".join(f"{m}={a.n_theorems(m)}" for m in a.models))
    return a


def errorbar(ax, x, point, lo, hi, **kw):
    """Draw one point with an asymmetric 95% interval."""
    import numpy as np
    if np.isnan(point):
        return
    yerr = [[point - lo], [hi - point]]
    ax.errorbar([x], [point], yerr=yerr, **kw)
