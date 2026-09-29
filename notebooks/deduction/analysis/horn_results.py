"""Results table and ladder figures for the Horn-rule deduction benchmark.

Loads every stage-2 row file from the four run sources (Bedrock, spot boxes, B200,
ORCD), dedupes cells, drops transport failures and retired arms, and writes:

* ``horn_table.tex``: the induction table's layout. One row per model (family and size in
  one column, ladder order, no family rows), ``mean ± sd`` pass rate for the high-density
  (lem), high-density-+-irrelevant (pad) and low-density (both) arms, and the two
  seed-paired deltas against low density as plain point values. No marks of any kind.
* ``horn_table_full.tex``: the same grouped by family, with m, n, the disc arm and its delta.
* ``horn_table.md``: the same table in markdown with n per arm.
* ``horn_summary.json``: every number in the tables, for other scripts.
* ``horn_ladder_arms.{pdf,png}``: arm pass rates per family ladder.
* ``horn_ladder_deltas.{pdf,png}``: the three deltas per family ladder with CI bands.

Statistics. The unit is the cell mean over replicates (pass@1), paired by theory seed.
A pass rate is the mean over seeds of the per-seed pass@1; its ``±`` is the half-width
of a 95% percentile bootstrap CI over seeds (``--spread sd`` prints the sd over seeds
instead, as the induction table did). A delta is the mean seed-paired difference in
points with a 95% bootstrap CI and a sign-flip permutation p-value, both from
``smolbench.deduction.horn.stats.contrast``.

Scoring. ``--scoring iclr`` keeps each row's stored verdict, the rule the ICLR 2027
submission was scored with. ``--scoring default`` (the default) rescores every finished
row from its stored content with the default extractor (``smolbench.deduction.horn.extract``),
which needs the served rungs (``--rungs``). Outputs go to ``<out>/<scoring>/``.

usage: horn_results.py [--scratchpad DIR] [--rungs DIR] [--scoring iclr|default] [--out DIR]
                       [--pick MODEL=M ...] [--spread ci|sd]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import random
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from smolbench.deduction.horn.extract import DEFAULT_SCORING, SCORING_MODES, verdict_fields  # noqa: E402
from smolbench.deduction.horn.render import Rendered  # noqa: E402
from smolbench.deduction.horn.stats import contrast  # noqa: E402
from smolbench.deduction.horn.theory import Theory  # noqa: E402

SCRATCHPAD = Path(
    "/tmp/claude-1000/-home-fisherxue-SmolBench-stack3/5bb1813f-c09f-47cd-81ba-0a438c80d47f/scratchpad"
)
OUT = REPO / "notebooks" / "deduction" / "results"
#: A token the Bedrock DeepSeek-V3.1 endpoint inserts into atoms (``bakal(极)``). Rows
#: that contain it are scored as written and counted in the notes.
CORRUPT_TOKEN = "极"
#: The served rungs: ``<rungs>/m<m>/s<seed>/{theory.json,<arm>/{meta.json,prompt.md,system.md}}``.
RUNGS = SCRATCHPAD / "roster2"

#: Source name -> glob under the scratchpad. Order is the dedupe priority. A source may hold
#: a forward file ``<model>_m<m>.jsonl`` and a back-fill ``<model>_m<m>.fill.jsonl``; the
#: forward file is read first and wins ties.
SOURCES = (
    ("bedrock", "bedrock/stage2/*_m*.jsonl"),
    ("spot", "spot_results/*_m*.jsonl"),
    ("b200", "b200_results/results_stage2/*_m*.jsonl"),
    ("orcd", "orcd/results/stage2_*_m*.jsonl"),
)

ARMS = ("lem", "pad", "disc", "both")
RETIRED_ARMS = {"junk"}
#: (a, b) -> column "a - b", all relative to the low-density arm.
DELTAS = (("lem", "both"), ("pad", "both"), ("disc", "both"))
#: The paper table (``horn_table.tex``): three arms, two deltas, full model names, no m or n.
PAPER_ARMS = ("lem", "pad", "both")
PAPER_DELTAS = (("lem", "both"), ("pad", "both"))
ARM_NAME = {"lem": "high density", "pad": "high density + irrelevant", "both": "low density", "disc": "dead trees"}
DELTA_NAME = {("lem", "both"): "$\\Delta$ (high $-$ low)", ("pad", "both"): "$\\Delta$ (irrelevant $-$ low)"}
#: Model column of the paper table: the names the induction table used.
PAPER_NAME = {
    "gemma-4-e2b": "Gemma4 E2B-it",
    "gemma-4-12b": "Gemma4 12B-it",
    "gemma-4-31b": "Gemma4 31B-it",
    "nemotron-3-nano-4b": "Nemotron3 Nano-4B",
    "nemotron-3-nano-30b-a3b": "Nemotron3 Nano-30B",
    "nemotron-3-super-120b-a12b": "Nemotron3 Super-120B",
    "qwen3.5-27b": "Qwen3.5 27B",
    "qwen3.5-122b-a10b": "Qwen3.5 122B",
    "qwen3.5-397b-a17b": "Qwen3.5 397B",
    "deepseek-v4-flash": "Deepseek V4-Flash",
    "deepseek-v3.1": "Deepseek V3.1",
    "deepseek-v4-pro": "Deepseek V4-Pro",
    "glm-4.7-flash": "GLM-4.7-Flash",
    "glm-4.5-air": "GLM-4.5-Air",
    "glm-4.7": "GLM-4.7",
    "ministral-3-3b": "Ministral3-2512 3B",
    "ministral-3-8b": "Ministral3-2512 8B",
    "ministral-3-14b": "Ministral3-2512 14B",
    "exaone-4.0-32b": "EXAONE 4.0-32B",
    "exaone-4.5-33b": "EXAONE 4.5-33B",
    "k-exaone-236b-a23b": "K-EXAONE 236B",
}
FAIL = {"length", "invalid_step", "incomplete", "given_up", "no_answer", "missing"}

#: Dropped from every output by decision (Fisher, 2026-09-26): the three EXAONE models and
#: glm-4.5-air were stopped early; deepseek-v4-pro was never run. Their raw files stay on disk.
DROPPED = {"exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b", "glm-4.5-air", "deepseek-v4-pro"}

#: Family -> models, small to large. Family order follows the roster ladder. Dropped models
#: are removed here, so a family with none left disappears from the table and figures.
ROSTER = (
    ("Gemma 4", ("gemma-4-e2b", "gemma-4-12b", "gemma-4-31b")),
    ("Nemotron 3", ("nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b")),
    ("Qwen3.5", ("qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b")),
    ("DeepSeek", ("deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro")),
    ("GLM", ("glm-4.7-flash", "glm-4.5-air", "glm-4.7")),
    ("Ministral 3", ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b")),
    ("EXAONE", ("exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b")),
)
FAMILIES = tuple(
    (fam, tuple(m for m in ms if m not in DROPPED)) for fam, ms in ROSTER if any(m not in DROPPED for m in ms)
)
MODELS = tuple(m for _, ms in FAMILIES for m in ms)
DISPLAY = {
    "gemma-4-e2b": "E2B",
    "gemma-4-12b": "12B",
    "gemma-4-31b": "31B",
    "nemotron-3-nano-4b": "Nano-4B",
    "nemotron-3-nano-30b-a3b": "Nano-30B-A3B",
    "nemotron-3-super-120b-a12b": "Super-120B-A12B",
    "qwen3.5-27b": "27B",
    "qwen3.5-122b-a10b": "122B-A10B",
    "qwen3.5-397b-a17b": "397B-A17B",
    "deepseek-v4-flash": "V4-Flash",
    "deepseek-v3.1": "V3.1",
    "deepseek-v4-pro": "V4-Pro",
    "glm-4.7-flash": "4.7-Flash",
    "glm-4.5-air": "4.5-Air",
    "glm-4.7": "4.7",
    "ministral-3-3b": "3B",
    "ministral-3-8b": "8B",
    "ministral-3-14b": "14B",
    "exaone-4.0-32b": "4.0-32B",
    "exaone-4.5-33b": "4.5-33B",
    "k-exaone-236b-a23b": "K-236B-A23B",
}

#: Shorter names for figure tick labels where the table name would collide.
FIG_LABEL = {
    "nemotron-3-nano-30b-a3b": "Nano-30B",
    "nemotron-3-super-120b-a12b": "Super-120B",
    "qwen3.5-122b-a10b": "122B",
    "qwen3.5-397b-a17b": "397B",
    "k-exaone-236b-a23b": "K-236B",
}

#: Chain length per model from the run manifests. None: take the only m on disk.
PICKS: dict[str, int | None] = {
    "gemma-4-e2b": 6,
    "gemma-4-12b": 32,
    "gemma-4-31b": 64,
    "nemotron-3-nano-4b": 2,
    "nemotron-3-nano-30b-a3b": 6,
    "nemotron-3-super-120b-a12b": 20,
    "qwen3.5-27b": 64,
    "qwen3.5-122b-a10b": 48,
    "qwen3.5-397b-a17b": 64,
    "deepseek-v4-flash": 64,
    "deepseek-v3.1": 64,
    "deepseek-v4-pro": 64,
    "glm-4.7-flash": 10,
    "glm-4.5-air": 24,
    "glm-4.7": 48,
    "ministral-3-3b": 1,
    "ministral-3-8b": 1,
    "ministral-3-14b": 2,
    "exaone-4.0-32b": 16,
    "exaone-4.5-33b": 16,
    "k-exaone-236b-a23b": 32,
}
#: Model -> the one source whose rows count; files elsewhere are cancelled duplicates.
SOURCE_ONLY = {"nemotron-3-nano-4b": "spot"}
#: Models run live on two sources with the same protocol. Their rows merge by key until one
#: source alone holds a full run; from then on only that source counts.
PIN_WHEN_COMPLETE = {"gemma-4-31b"}
#: m was set by hand, not by the calibration rule.
FORCED = {"glm-4.5-air", "qwen3.5-397b-a17b", "deepseek-v4-pro"}
#: lem below 60% at m = 1 on the calibration seeds; run at m = 1 for the record.
BELOW_FLOOR = {"ministral-3-3b", "ministral-3-8b"}

N_FULL = 1200
N_SEEDS = 100
N_REPS = 3
SEED0 = 100
#: A model whose run stopped this close to N_FULL is complete: every cell it never wrote (or
#: wrote as an exception) is counted as a failure (verdict ``missing``). Fisher, 2026-09-26.
IMPUTE_MAX_MISSING = 24
N_BOOT = 5000
ALPHA = 0.05
#: Data checks that compare arms or judge the calibration wait for this many cells per model:
#: rows from a running box arrive in completion order, so early pass rates are biased.
MIN_CHECK_CELLS = 300
#: A point or delta with fewer seeds than this is left off the figures (still in the table).
MIN_PLOT_SEEDS = 10

# Categorical slots 1-4 of the validated default palette (dataviz skill).
ARM_COLOR = {"lem": "#2a78d6", "pad": "#eb6834", "disc": "#1baf7a", "both": "#eda100"}
ARM_MARKER = {"lem": "o", "pad": "s", "disc": "^", "both": "D"}
DELTA_COLOR = ("#2a78d6", "#eb6834", "#1baf7a")
DELTA_MARKER = ("o", "s", "^")
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


# ----------------------------------------------------------------------------- loading


def rung_m(rung: str) -> int | None:
    """``m48`` or ``stage2_m48`` -> 48."""
    mt = re.search(r"m(\d+)$", str(rung))
    return int(mt.group(1)) if mt else None


class Rescorer:
    """Rescore stored rows under a scoring mode from the served rungs."""

    def __init__(self, scoring: str, rungs: Path) -> None:
        self.scoring = scoring
        self.rungs = rungs
        self._cache: dict[tuple, tuple[Theory, Rendered]] = {}
        self.rescored = 0
        self.changed = collections.Counter()
        self.no_content = collections.Counter()

    def _load(self, m: int, seed: int, arm: str) -> tuple[Theory, Rendered]:
        key = (m, seed, arm)
        if key not in self._cache:
            sd = self.rungs / f"m{m}" / f"s{seed:04d}"
            ad = sd / arm
            theory = Theory.from_json((sd / "theory.json").read_text(encoding="utf-8"))
            rendered = Rendered.from_meta(
                json.loads((ad / "meta.json").read_text(encoding="utf-8")),
                prompt=(ad / "prompt.md").read_text(encoding="utf-8"),
                system=(ad / "system.md").read_text(encoding="utf-8"),
            )
            self._cache[key] = (theory, rendered)
        return self._cache[key]

    def __call__(self, model: str, m: int, r: dict) -> None:
        """Update ``r``'s verdict fields in place; ``iclr`` keeps the stored ones."""
        if self.scoring == "iclr":
            r["scoring"] = "iclr"
            return
        if r.get("verdict") == "exception":
            return
        if r.get("content") is None:
            self.no_content[model] += 1
            return
        theory, rendered = self._load(m, int(r["seed"]), r["arm"])
        old = r.get("verdict")
        r.update(verdict_fields(theory, rendered, r["content"], r.get("finish_reason") or "stop", self.scoring))
        self.rescored += 1
        if (old == "success") != (r["verdict"] == "success"):
            self.changed[(model, r["arm"], "gain" if r["verdict"] == "success" else "loss")] += 1


def load_rows(
    scratchpad: Path,
    anomalies: list[str],
    scoring: str = DEFAULT_SCORING,
    rungs: Path = RUNGS,
) -> dict[tuple, dict]:
    """``(model, m, arm, seed, rep) -> row`` after rescoring, dedupe and the drops.

    Keeps the non-exception row of a duplicate pair; among non-exception duplicates,
    the first source in ``SOURCES`` order wins.
    """
    rescore = Rescorer(scoring, rungs)
    kept: dict[tuple, dict] = {}
    n_files = 0
    dup_same = collections.Counter()
    dup_cross = collections.Counter()
    exc = collections.Counter()
    retired = collections.Counter()
    wrong_source = collections.Counter()
    dropped_models = collections.Counter()
    for source, pattern in SOURCES:
        for path in sorted(glob.glob(str(scratchpad / pattern)), key=lambda x: (".fill." in Path(x).name, x)):
            if not re.search(r"_m\d+(\.fill)?\.jsonl$", Path(path).name):
                anomalies.append(f"{source}: skipped snapshot copy {Path(path).name}")
                continue
            n_files += 1
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    anomalies.append(f"{source}: unparsable line in {Path(path).name}")
                    continue
                model = r.get("spec_key") or r["model"]
                if model in DROPPED:
                    dropped_models[model] += 1
                    continue
                m = rung_m(r.get("rung", ""))
                if m is None:
                    anomalies.append(f"{source}: row without an m in rung {r.get('rung')!r} ({Path(path).name})")
                    continue
                if r["arm"] in RETIRED_ARMS:
                    retired[model] += 1
                    continue
                if SOURCE_ONLY.get(model, source) != source:
                    wrong_source[(model, source)] += 1
                    continue
                r["_source"] = source
                rescore(model, m, r)
                r["_corrupt"] = CORRUPT_TOKEN in (r.get("content") or "")
                for heavy in ("content", "reasoning", "answer"):
                    r.pop(heavy, None)
                key = (model, m, r["arm"], int(r["seed"]), int(r["rep"]))
                old = kept.get(key)
                if old is None:
                    kept[key] = r
                    continue
                (dup_same if old["_source"] == source else dup_cross)[model] += 1
                if old.get("verdict") == "exception" and r.get("verdict") != "exception":
                    kept[key] = r
    for key in list(kept):
        if kept[key].get("verdict") == "exception":
            exc[key[0]] += 1
            del kept[key]
    per_source: dict = collections.defaultdict(collections.Counter)
    for (model, m, *_), r in kept.items():
        if model in PIN_WHEN_COMPLETE:
            per_source[(model, m)][r["_source"]] += 1
    for (model, m), counts in sorted(per_source.items()):
        full = [src for src, n in counts.items() if n >= N_FULL]
        if full:
            dropped = 0
            for key in [k for k in kept if k[0] == model and k[1] == m and kept[k]["_source"] != full[0]]:
                del kept[key]
                dropped += 1
            anomalies.append(f"{model}: {full[0]} holds a full run at m={m}; pinned to it, dropped {dropped} rows from other sources")
        elif len(counts) > 1:
            anomalies.append(f"{model}: merged live rows from two sources at m={m} {dict(counts)}; pinned once one source reaches {N_FULL}")
    anomalies.append(f"read {n_files} files, kept {len(kept)} cells")
    corrupt = collections.Counter((k[0], k[2]) for k, r in kept.items() if r["_corrupt"])
    for model in sorted({mdl for mdl, _ in corrupt}):
        per_arm = {arm: corrupt[(model, arm)] for arm in ARMS}
        anomalies.append(
            f"{model}: {sum(per_arm.values())} kept rows contain the stray token {CORRUPT_TOKEN!r} "
            f"(provider output corruption; still scored) {per_arm}"
        )
    if scoring != "iclr":
        anomalies.append(f"scoring {scoring}: rescored {rescore.rescored} rows from content")
        for model, n in sorted(rescore.no_content.items()):
            anomalies.append(f"{model}: {n} rows have no content; kept their stored verdict")
        for (model, arm, kind), n in sorted(rescore.changed.items()):
            anomalies.append(f"{model}: {n} {arm} rows {'pass' if kind == 'gain' else 'fail'} only under {scoring} scoring")
    for model, n in sorted(retired.items()):
        anomalies.append(f"{model}: dropped {n} rows of retired arms {sorted(RETIRED_ARMS)}")
    for model, n in sorted(dropped_models.items()):
        anomalies.append(f"{model}: dropped model, {n} rows ignored")
    for (model, source), n in sorted(wrong_source.items()):
        anomalies.append(f"{model}: dropped {n} rows from {source}; only {SOURCE_ONLY[model]} counts for this model")
    for model, n in sorted(dup_same.items()):
        anomalies.append(f"{model}: {n} duplicate cells within one source (kept the non-exception or first)")
    for model, n in sorted(dup_cross.items()):
        anomalies.append(f"{model}: {n} cells present in two sources (kept the first in {[s for s, _ in SOURCES]} order)")
    for model, n in sorted(exc.items()):
        anomalies.append(f"{model}: {n} exception cells excluded with no replacement")
    return kept


def pick_m(rows: dict[tuple, dict], picks: dict[str, int | None], anomalies: list[str]) -> dict[str, int]:
    """Model -> chain length used in the table."""
    on_disk: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for (model, m, *_), _ in rows.items():
        on_disk[model][m] += 1
    chosen: dict[str, int] = {}
    for model, counts in sorted(on_disk.items()):
        want = picks.get(model)
        if want is None:
            m = counts.most_common(1)[0][0]
            if len(counts) > 1:
                anomalies.append(f"{model}: no pick recorded and several m on disk {dict(counts)}; using m={m} (most rows)")
        else:
            m = want
            if m not in counts:
                anomalies.append(f"{model}: pick m={m} has no rows; on disk {dict(counts)}; model shown as missing")
                continue
        extra = {k: v for k, v in counts.items() if k != m}
        if extra:
            anomalies.append(f"{model}: ignored rows at other m {extra}")
        chosen[model] = m
    for model in MODELS:
        if model not in chosen:
            anomalies.append(f"{model}: no stage-2 rows yet")
    return chosen


def impute_missing(rows: dict[tuple, dict], chosen: dict[str, int], anomalies: list[str]) -> set[str]:
    """Add a ``missing`` failure row for every absent cell of a model within
    ``IMPUTE_MAX_MISSING`` of a full run. Returns the models touched."""
    touched: set[str] = set()
    for model, m in chosen.items():
        have = {k for k in rows if k[0] == model and k[1] == m}
        n = len(have)
        if n >= N_FULL or n < N_FULL - IMPUTE_MAX_MISSING:
            continue
        added = 0
        for arm in ARMS:
            for seed in range(SEED0, SEED0 + N_SEEDS):
                for rep in range(N_REPS):
                    key = (model, m, arm, seed, rep)
                    if key not in have:
                        rows[key] = {"spec_key": model, "rung": f"m{m}", "arm": arm, "seed": seed, "rep": rep,
                                     "verdict": "missing", "_source": "imputed"}
                        added += 1
        touched.add(model)
        anomalies.append(f"{model}: {n} cells on disk, {added} missing cells counted as failures (flag d)")
    return touched


def cells(rows: dict[tuple, dict], model: str, m: int) -> dict[str, dict[int, list[bool]]]:
    """``arm -> seed -> [pass per replicate]`` as ``rows_contrast`` expects."""
    out: dict[str, dict[int, list[bool]]] = {a: collections.defaultdict(list) for a in ARMS}
    for (mo, mm, arm, seed, _rep), r in rows.items():
        if mo == model and mm == m and arm in out:
            v = r.get("verdict")
            if v != "success" and v not in FAIL:
                raise ValueError(f"{model}: unknown verdict {v!r}")
            out[arm][seed].append(v == "success")
    return out


# --------------------------------------------------------------------------- statistics


def arm_stats(per_seed: dict[int, list[bool]], rng: np.random.Generator) -> dict:
    """Mean over seeds of per-seed pass@1, bootstrap CI over seeds, sd over seeds, n cells."""
    means = np.array([sum(v) / len(v) for v in per_seed.values()], dtype=float)
    n_cells = sum(len(v) for v in per_seed.values())
    if means.size == 0:
        return {"mean": None, "lo": None, "hi": None, "sd": None, "n": 0, "n_seeds": 0}
    idx = rng.integers(0, means.size, size=(N_BOOT, means.size))
    bs = means[idx].mean(axis=1)
    return {
        "mean": float(means.mean()),
        "lo": float(np.percentile(bs, 2.5)),
        "hi": float(np.percentile(bs, 97.5)),
        "sd": float(means.std(ddof=1)) if means.size > 1 else 0.0,
        "n": n_cells,
        "n_seeds": int(means.size),
    }


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> set[str]:
    """Keys whose p survives Holm step-down at ``alpha``."""
    items = sorted((p, k) for k, p in pvals.items() if p == p)
    survivors: set[str] = set()
    n = len(items)
    for i, (p, k) in enumerate(items):
        if p > alpha / (n - i):
            break
        survivors.add(k)
    return survivors


def summarise(rows: dict[tuple, dict], chosen: dict[str, int], imputed: set[str] = frozenset()) -> dict[str, dict]:
    """Per model: m, arm stats, deltas, flags."""
    rng_np = np.random.default_rng(0)
    rng_py = random.Random(0)
    out: dict[str, dict] = {}
    for model in MODELS:
        if model not in chosen:
            continue
        m = chosen[model]
        c = cells(rows, model, m)
        arms = {a: arm_stats(c[a], rng_np) for a in ARMS}
        deltas = {}
        for a, b in DELTAS:
            mean, lo, hi, p, n = contrast(c[a], c[b], rng_py)
            deltas[f"{a}-{b}"] = {"mean": mean, "lo": lo, "hi": hi, "p": p, "n_seeds": n}
        n_total = sum(s["n"] for s in arms.values())
        out[model] = {
            "m": m,
            "arms": arms,
            "deltas": deltas,
            "n": n_total,
            "incomplete": n_total < N_FULL,
            "forced": model in FORCED,
            "below_floor": model in BELOW_FLOOR,
            "imputed": model in imputed,
        }
    for name in (f"{a}-{b}" for a, b in DELTAS):
        pv = {mo: s["deltas"][name]["p"] for mo, s in out.items() if s["deltas"][name]["n_seeds"] > 0}
        for mo in holm(pv):
            out[mo]["deltas"][name]["holm"] = True
    return out


# ------------------------------------------------------------------------- diagnostics

VERDICTS = ("success", "length", "invalid_step", "incomplete", "given_up", "no_answer", "missing")


def diagnostics(rows: dict[tuple, dict], chosen: dict[str, int]) -> dict[str, dict[str, dict]]:
    """Per model and arm: verdict counts, cap hits and mean output tokens."""
    out: dict[str, dict[str, dict]] = {}
    for model in MODELS:
        if model not in chosen:
            continue
        per_arm: dict[str, dict] = {}
        for arm in ARMS:
            sel = [r for (mo, mm, a, _s, _r), r in rows.items() if mo == model and mm == chosen[model] and a == arm]
            counts = collections.Counter(r.get("verdict") for r in sel)
            toks = [r["completion_tokens"] for r in sel if isinstance(r.get("completion_tokens"), (int, float))]
            per_arm[arm] = {
                "n": len(sel),
                **{v: counts.get(v, 0) for v in VERDICTS},
                "finish_length": sum(r.get("finish_reason") == "length" for r in sel),
                "mean_completion_tokens": float(np.mean(toks)) if toks else None,
                "mean_prompt_tokens": float(np.mean([r["prompt_tokens"] for r in sel if r.get("prompt_tokens") is not None])) if sel else None,
            }
        out[model] = per_arm
    return out


def diagnostics_markdown(diag: dict[str, dict[str, dict]], only: set[str] | None = None) -> str:
    heads = ["Model", "arm", "n", "success", "length", "invalid_step", "incomplete", "no_answer", "missing", "mean out tok", "mean in tok"]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for model, per_arm in diag.items():
        if only and model not in only:
            continue
        for arm in ARMS:
            d = per_arm[arm]
            if d["n"] == 0:
                continue
            tok = f"{d['mean_completion_tokens']:,.0f}" if d["mean_completion_tokens"] is not None else "—"
            ptok = f"{d['mean_prompt_tokens']:,.0f}" if d["mean_prompt_tokens"] is not None else "—"
            lines.append(
                f"| {model} | {arm} | {d['n']} | {d['success']} | {d['length']} | {d['invalid_step']} | "
                f"{d['incomplete']} | {d['no_answer']} | {d['missing']} | {tok} | {ptok} |"
            )
    note = ("\n`length` = verdict length (output cap hit before an answer). Cells whose finish_reason is "
            "length but that still parsed an answer keep their checker verdict. `missing` = cell never written by a run "
            "that stopped just short of 1200, counted as a failure. Token means are over the arm's cells.\n")
    return "\n".join(lines) + "\n" + note


# ------------------------------------------------------------------------------ tables


def stars(p: float) -> str:
    if p != p:
        return ""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""


def flags(s: dict) -> str:
    f = ""
    if s["incomplete"]:
        f += "a"
    if s["forced"]:
        f += "b"
    if s["below_floor"]:
        f += "c"
    if s.get("imputed"):
        f += "d"
    return f


def best_worst(arms: dict[str, dict]) -> tuple[str | None, str | None]:
    vals = {a: s["mean"] for a, s in arms.items() if s["mean"] is not None}
    if len(vals) < 2 or len(set(vals.values())) == 1:
        return None, None
    return max(vals, key=vals.get), min(vals, key=vals.get)


def latex_table(summary: dict[str, dict], spread: str, with_n: bool, layout: str = "full") -> str:
    """``layout="full"``: family groups, short ``DISPLAY`` names, m, n, four arms, three deltas.
    ``layout="paper"``: the induction table's layout. ``PAPER_NAME`` (family and size) in
    one flat column, ladder order, no family rows, no m or n, the three arms in
    ``PAPER_ARMS`` under their ``ARM_NAME`` headings, and the two ``PAPER_DELTAS`` as plain
    point values. Values are ``mean ± sd`` over seeds with no bold, italic, stars, daggers,
    flags or CI, exactly as the induction table printed them."""
    paper = layout == "paper"
    arms = PAPER_ARMS if paper else ARMS
    deltas = PAPER_DELTAS if paper else DELTAS
    with_m = not paper
    with_n = with_n and not paper
    ncol = 1 + (1 if with_m else 0) + (1 if with_n else 0) + len(arms) + len(deltas)
    heads = ["Model"] + (["$m$"] if with_m else []) + (["$n$"] if with_n else [])
    heads += [ARM_NAME[a] if paper else a for a in arms]
    heads += [DELTA_NAME[(a, b)] if paper else f"{a}$-${b}" for a, b in deltas]
    align = "l" + ("r" if with_m else "") + ("r" if with_n else "") + "c" * len(arms) + "r" * len(deltas)
    lines = [f"\\begin{{tabular}}{{{align}}}", "\\toprule", " & ".join(heads) + " \\\\", "\\midrule"]
    first = True
    for family, models in FAMILIES:
        if not paper:
            if not first:
                lines.append("\\addlinespace")
            lines.append(f"\\multicolumn{{{ncol}}}{{l}}{{\\emph{{{family}}}}} \\\\")
        first = False
        for model in models:
            s = summary.get(model)
            name = PAPER_NAME[model] if paper else DISPLAY[model]
            if s is None:
                lines.append(f"{name} & \\multicolumn{{{ncol - 1}}}{{l}}{{\\textit{{not run}}}} \\\\")
                continue
            f = flags(s)
            if f and not paper:
                name += f"$^{{{f}}}$"
            row = [name] + ([str(s["m"])] if with_m else []) + ([str(s["n"])] if with_n else [])
            best, worst = best_worst({a: s["arms"][a] for a in arms})
            for arm in arms:
                st = s["arms"][arm]
                if st["mean"] is None:
                    row.append("--")
                    continue
                pm = st["sd"] if spread == "sd" or paper else (st["hi"] - st["lo"]) / 2
                cell = f"{st['mean']:.3f} \\pm {pm:.3f}"
                if paper:
                    row.append(f"${cell}$")
                    continue
                if arm == best:
                    cell = f"\\mathbf{{{cell}}}"
                elif arm == worst:
                    cell = f"\\mathit{{{cell}}}"
                row.append(f"${cell}$")
            for a, b in deltas:
                d = s["deltas"][f"{a}-{b}"]
                if d["n_seeds"] == 0:
                    row.append("--")
                    continue
                mark = stars(d["p"]) + ("\\dagger" if d.get("holm") else "")
                sup = f"^{{{mark}}}" if mark else ""
                if paper:
                    row.append(f"${d['mean']:.1f}$")
                else:
                    row.append(f"${d['mean']:+.1f}{sup}$ {{\\scriptsize $[{d['lo']:+.1f}, {d['hi']:+.1f}]$}}")
            lines.append(" & ".join(row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def markdown_table(summary: dict[str, dict], spread: str) -> str:
    pm_name = "sd" if spread == "sd" else "95% CI half-width"
    heads = ["Family", "Model", "m", "n"] + [f"{a} (n)" for a in ARMS] + [f"{a} − {b}" for a, b in DELTAS]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for family, models in FAMILIES:
        for model in models:
            s = summary.get(model)
            if s is None:
                lines.append(f"| {family} | {DISPLAY[model]} | | 0 | " + " | ".join(["—"] * (len(ARMS) + len(DELTAS))) + " |")
                continue
            name = DISPLAY[model] + (f" ^{flags(s)}" if flags(s) else "")
            row = [family, name, str(s["m"]), str(s["n"])]
            best, worst = best_worst(s["arms"])
            for arm in ARMS:
                st = s["arms"][arm]
                if st["mean"] is None:
                    row.append("—")
                    continue
                pm = st["sd"] if spread == "sd" else (st["hi"] - st["lo"]) / 2
                cell = f"{st['mean']:.3f} ± {pm:.3f} ({st['n']})"
                if arm == best:
                    cell = f"**{cell}**"
                elif arm == worst:
                    cell = f"*{cell}*"
                row.append(cell)
            for a, b in DELTAS:
                d = s["deltas"][f"{a}-{b}"]
                if d["n_seeds"] == 0:
                    row.append("—")
                    continue
                mark = stars(d["p"]) + ("†" if d.get("holm") else "")
                row.append(f"{d['mean']:+.1f}{mark} [{d['lo']:+.1f}, {d['hi']:+.1f}]")
            lines.append("| " + " | ".join(row) + " |")
    note = (
        f"\nPass rate = mean over theory seeds of per-seed pass@1 (3 replicates); ± = {pm_name} "
        "over seeds. Bold = best arm, italic = worst arm in the row. Deltas in points, "
        "seed-paired, with 95% bootstrap CI; * p<0.05, ** p<0.01, *** p<0.001 (sign-flip), "
        "† survives Holm across models in that column. Flags: a = incomplete "
        f"(n < {N_FULL} cells, still running), b = m set by hand, c = below floor (lem < 60% at m=1 on "
        "calibration seeds), d = a few missing cells counted as failures. Dropped by decision and absent here: exaone-4.0-32b, exaone-4.5-33b, "
        "k-exaone-236b-a23b, glm-4.5-air (stopped early), deepseek-v4-pro (not run).\n"
        "Rows for a running box arrive in completion order, so a partial pass rate (flag a) is biased "
        "toward short generations: quick failures for hard models, quick successes for easy ones. Do not "
        f"read a flagged row until n is a good fraction of {N_FULL}.\n"
    )
    return "\n".join(lines) + "\n" + note


# ----------------------------------------------------------------------------- figures


def _style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _tick_labels(models: tuple[str, ...], summary: dict[str, dict]) -> list[str]:
    return [
        FIG_LABEL.get(mo, DISPLAY[mo]) + (f"\nm={summary[mo]['m']}" if mo in summary else "\n(not run)")
        for mo in models
    ]


def _panels(plt):
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.4), sharey=True)
    axes = axes.ravel()
    for ax in axes[len(FAMILIES):]:
        ax.axis("off")
    return fig, axes


def figure_arms(summary: dict[str, dict], out: Path | None = None):
    """Arm pass rates along each family ladder. Saves PDF and PNG when ``out`` is given."""
    import matplotlib.pyplot as plt

    fig, axes = _panels(plt)
    for ax, (family, models) in zip(axes, FAMILIES):
        _style(ax)
        xs = np.arange(len(models))
        for k, arm in enumerate(ARMS):
            off = (k - 1.5) * 0.08
            y, lo, hi, x = [], [], [], []
            for i, model in enumerate(models):
                st = summary.get(model, {}).get("arms", {}).get(arm)
                if not st or st["mean"] is None or st["n_seeds"] < MIN_PLOT_SEEDS:
                    continue
                x.append(i + off)
                y.append(st["mean"])
                lo.append(st["mean"] - st["lo"])
                hi.append(st["hi"] - st["mean"])
            if x:
                ax.errorbar(x, y, yerr=[lo, hi], color=ARM_COLOR[arm], marker=ARM_MARKER[arm], markersize=5,
                            linewidth=1.5, capsize=2, elinewidth=1, label=arm)
        ax.set_xticks(xs, _tick_labels(models, summary))
        ax.set_xlim(-0.5, len(models) - 0.5)
        ax.set_ylim(0, 1.02)
        ax.set_title(family, fontsize=10, color=INK, loc="left")
    for ax in axes[::4]:
        ax.set_ylabel("pass@1", color=INK, fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    axes[-1].legend(handles, labels, loc="center", frameon=False, fontsize=9, title="arm", title_fontsize=9)
    fig.suptitle("Horn bench: pass rate per arm along each family ladder (95% CI over seeds)",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if out is not None:
        fig.savefig(out / "horn_ladder_arms.pdf")
        fig.savefig(out / "horn_ladder_arms.png", dpi=200)
    return fig


def figure_deltas(summary: dict[str, dict], out: Path | None = None):
    """The three deltas along each family ladder with CI bands. Saves when ``out`` is given."""
    import matplotlib.pyplot as plt

    fig, axes = _panels(plt)
    for ax, (family, models) in zip(axes, FAMILIES):
        _style(ax)
        ax.axhline(0, color=AXIS, linewidth=1)
        for k, (a, b) in enumerate(DELTAS):
            name = f"{a}-{b}"
            x, y, lo, hi = [], [], [], []
            for i, model in enumerate(models):
                d = summary.get(model, {}).get("deltas", {}).get(name)
                if not d or d["n_seeds"] < MIN_PLOT_SEEDS:
                    continue
                x.append(i)
                y.append(d["mean"])
                lo.append(d["lo"])
                hi.append(d["hi"])
            if not x:
                continue
            color = DELTA_COLOR[k]
            if len(x) == 1:
                ax.errorbar(x, y, yerr=[[y[0] - lo[0]], [hi[0] - y[0]]], color=color, capsize=2, elinewidth=1, linewidth=0)
            else:
                ax.fill_between(x, lo, hi, color=color, alpha=0.15, linewidth=0)
            ax.plot(x, y, color=color, marker=DELTA_MARKER[k], markersize=5, linewidth=1.5, label=f"{a} − {b}")
        ax.set_xticks(np.arange(len(models)), _tick_labels(models, summary))
        ax.set_xlim(-0.5, len(models) - 0.5)
        ax.set_title(family, fontsize=10, color=INK, loc="left")
    for ax in axes[::4]:
        ax.set_ylabel("Δ pass@1 (points) vs both", color=INK, fontsize=9)
    handles, labels = None, None
    for ax in axes[:7]:
        h, l = ax.get_legend_handles_labels()
        if len(l) == len(DELTAS):
            handles, labels = h, l
            break
    if handles:
        axes[-1].legend(handles, labels, loc="center", frameon=False, fontsize=9, title="contrast", title_fontsize=9)
    fig.suptitle("Horn bench: arm minus both along each family ladder (band = seed-paired 95% CI)",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if out is not None:
        fig.savefig(out / "horn_ladder_deltas.pdf")
        fig.savefig(out / "horn_ladder_deltas.png", dpi=200)
    return fig


# -------------------------------------------------------------------------------- main


def data_checks(summary: dict[str, dict], anomalies: list[str]) -> None:
    """Flag readings that need a second look."""
    for model, s in summary.items():
        a = s["arms"]
        ns = {arm: a[arm]["n"] for arm in ARMS}
        for arm in ARMS:
            if 0 < a[arm]["n"] and a[arm]["n"] > N_SEEDS * N_REPS:
                anomalies.append(f"{model}/{arm}: {a[arm]['n']} cells, more than {N_SEEDS * N_REPS}")
        if s["n"] < MIN_CHECK_CELLS:
            anomalies.append(f"{model}: n={s['n']} < {MIN_CHECK_CELLS}, early rows only; arm checks skipped")
            continue
        if max(ns.values()) - min(ns.values()) > 30:
            anomalies.append(f"{model}: unbalanced arms {ns}")
        if a["pad"]["mean"] is not None and a["lem"]["mean"] is not None and a["pad"]["mean"] > a["lem"]["mean"] + 0.02:
            anomalies.append(f"{model}: pad ({a['pad']['mean']:.3f}) above lem ({a['lem']['mean']:.3f})")
        if a["lem"]["mean"] is not None and not (0.5 <= a["lem"]["mean"] <= 0.95):
            anomalies.append(f"{model}: lem = {a['lem']['mean']:.3f} at m={s['m']}, outside the 50-95% band")


class Results:
    """Everything one run of the pipeline produces, before any file is written."""

    def __init__(self, rows: dict[tuple, dict], chosen: dict[str, int], summary: dict[str, dict],
                 diag: dict[str, dict[str, dict]], anomalies: list[str]) -> None:
        self.rows = rows
        self.chosen = chosen
        self.summary = summary
        self.diag = diag
        self.anomalies = anomalies


def run_pipeline(
    scratchpad: Path = SCRATCHPAD,
    picks: dict[str, int | None] | None = None,
    scoring: str = DEFAULT_SCORING,
    rungs: Path = RUNGS,
) -> Results:
    """Load, rescore, dedupe, pick m, summarise, check and diagnose. No files are written."""
    anomalies: list[str] = []
    rows = load_rows(scratchpad, anomalies, scoring, rungs)
    chosen = pick_m(rows, {**PICKS, **(picks or {})}, anomalies)
    imputed = impute_missing(rows, chosen, anomalies)
    summary = summarise(rows, chosen, imputed)
    data_checks(summary, anomalies)
    diag = diagnostics(rows, chosen)
    return Results(rows, chosen, summary, diag, anomalies)


def write_outputs(res: Results, out: Path = OUT, spread: str = "ci", with_n: bool = True, figures: bool = True) -> list[Path]:
    """Write the tables, the JSON summary and (optionally) the figures under ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    md = markdown_table(res.summary, spread)
    diag_md = diagnostics_markdown(res.diag)
    written = [
        out / "horn_table.md",
        out / "horn_diagnostics.md",
        out / "horn_table.tex",
        out / "horn_table_full.tex",
        out / "horn_summary.json",
    ]
    written[0].write_text(md + "\n## Diagnostics per arm\n\n" + diag_md, encoding="utf-8")
    written[1].write_text(diag_md, encoding="utf-8")
    written[2].write_text(latex_table(res.summary, spread, with_n, "paper"), encoding="utf-8")
    written[3].write_text(latex_table(res.summary, spread, with_n, "full"), encoding="utf-8")
    written[4].write_text(
        json.dumps({"models": res.summary, "diagnostics": res.diag, "anomalies": res.anomalies}, indent=1),
        encoding="utf-8",
    )
    if figures:
        import matplotlib.pyplot as plt

        plt.close(figure_arms(res.summary, out))
        plt.close(figure_deltas(res.summary, out))
        written += [out / f"horn_ladder_{k}.{ext}" for k in ("arms", "deltas") for ext in ("pdf", "png")]
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--scratchpad", type=Path, default=SCRATCHPAD)
    ap.add_argument("--rungs", type=Path, default=None, help="served rungs (default <scratchpad>/roster2)")
    ap.add_argument("--scoring", choices=list(SCORING_MODES), default=DEFAULT_SCORING)
    ap.add_argument("--out", type=Path, default=OUT, help="outputs go to <out>/<scoring>/")
    ap.add_argument("--pick", action="append", default=[], metavar="MODEL=M", help="override a chain length")
    ap.add_argument("--spread", choices=("ci", "sd"), default="ci", help="what ± means in the arm columns")
    ap.add_argument("--no-n", action="store_true", help="drop the n column from the LaTeX table")
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)

    picks: dict[str, int | None] = {}
    for item in a.pick:
        model, m = item.split("=")
        picks[model] = int(m)

    if not a.no_figures:
        import matplotlib

        matplotlib.use("Agg")
    res = run_pipeline(a.scratchpad, picks, a.scoring, a.rungs or a.scratchpad / "roster2")
    written = write_outputs(res, a.out / a.scoring, a.spread, not a.no_n, not a.no_figures)

    print(markdown_table(res.summary, a.spread))
    print("## Diagnostics per arm\n")
    print(diagnostics_markdown(res.diag))
    print("Notes:")
    for line in res.anomalies:
        print(f"- {line}")
    print("\nWrote " + ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
