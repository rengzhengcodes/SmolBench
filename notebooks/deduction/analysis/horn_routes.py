"""Route choice and proof length per model and arm for the Horn bench.

Reads the deduped released rows through ``horn_results.run_pipeline`` and writes
``horn_routes.md``, ``horn_routes.tex``, ``horn_routes.json`` and
``horn_routes.{png,pdf}`` into ``notebooks/deduction/results/``.

Route (``smolbench.deduction.horn.checker.route_of``): ``short`` = only chain lemmas
applied, ``long`` = only derivation-tree rules, ``mixed`` = both. For a failure the
failing step's rule is included, so a failure whose route is ``long`` or ``mixed`` applied
or tried a tree rule (``both``) or a dead-tree rule (``disc``) before failing. A failure
with an empty route had no recognised rule at all (output-cap hit, no answer, or an
invented rule on the first step). Only ``both`` has a valid tree route. In ``disc`` a
non-lemma step is a detour into a dead rule, which can never be a valid step, so every
``disc`` success is lemma-only. ``lem`` and ``pad`` show no non-lemma rule, so the share
is 0 there by construction.

Proof length is ``steps`` (valid derive lines) on successes divided by the theory's chain
length ``m``. 1.0 is the designed lemma route; the full tree route at depth 2 is about 3.
A lemma-only proof above 1.0 applied redundant alternative lemmas.

usage: horn_routes.py --data DIR [--scoring iclr|default] [--out DIR] [--no-figures]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import horn_results as hr  # noqa: E402

ARMS = ("lem", "pad", "disc", "both")
NON_LEMMA = {"long", "mixed"}
ROUTES = (("short", "lemma only"), ("mixed", "mixed"), ("long", "tree only"))
LENGTH_ARMS = (("lem", "high density (lem)"), ("both", "low density (both)"))
N_BOOT = 5000
#: Output cap of the roster runs (tokens).
OUTPUT_CAP = "131k"
#: Failure kinds, in table order. ``no_route`` = an invalid or incomplete answer whose first
#: step matched no rule, so the checker records no route.
FAIL_KINDS = (
    ("cap", f"hit the output cap ({OUTPUT_CAP}), no answer"),
    ("no_route", "invalid first step, no recognised rule"),
    ("no_answer", "no answer or gave up"),
    ("lemma", "invalid step after valid lemma steps"),
    ("tree", "invalid step after entering a tree"),
)
#: Upper limit of the steps/m panel. Ministral 3B and 8B run at m = 1, where whiskers reach 8.
Y_CLIP = 4.5


# --------------------------------------------------------------------------- statistics


def _pct(k: int, n: int) -> float | None:
    return 100.0 * k / n if n else None


def _mean_ci(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float] | None:
    """Mean and 95% percentile-bootstrap CI over cells."""
    if x.size == 0:
        return None
    if x.size == 1:
        return float(x[0]), float(x[0]), float(x[0])
    draws = rng.choice(x, size=(N_BOOT, x.size), replace=True).mean(axis=1)
    return float(x.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def _fail_kind(r: dict) -> str:
    v = r.get("verdict")
    if v == "length":
        return "cap"
    if v in ("no_answer", "given_up"):
        return "no_answer"
    route = r.get("route")
    if route in NON_LEMMA:
        return "tree"
    return "lemma" if route == "short" else "no_route"


def arm_stats(rows: list[dict], m: int, rng: np.random.Generator) -> dict:
    """Counts, non-lemma shares and steps/m on successes for one model and arm."""
    succ = [r for r in rows if r.get("verdict") == "success"]
    fail = [r for r in rows if r.get("verdict") != "success"]
    fail_routed = [r for r in fail if r.get("route")]
    steps_m = np.array(
        [r["steps"] / m for r in succ if isinstance(r.get("steps"), (int, float))], dtype=float
    )
    ci = _mean_ci(steps_m, rng)
    routes = {k: sum(r.get("route") == k for r in succ) for k, _ in ROUTES}
    return {
        "n": len(rows),
        "n_success": len(succ),
        "n_fail": len(fail),
        "n_fail_routed": len(fail_routed),
        "pass_rate": _pct(len(succ), len(rows)),
        "non_lemma_all": _pct(sum(r.get("route") in NON_LEMMA for r in rows), len(rows)),
        "non_lemma_success": _pct(sum(r.get("route") in NON_LEMMA for r in succ), len(succ)),
        "non_lemma_fail": _pct(sum(r.get("route") in NON_LEMMA for r in fail), len(fail)),
        "non_lemma_fail_routed": _pct(
            sum(r.get("route") in NON_LEMMA for r in fail_routed), len(fail_routed)
        ),
        "success_routes": routes,
        "n_non_lemma_success": sum(r.get("route") in NON_LEMMA for r in succ),
        "n_non_lemma_fail": sum(r.get("route") in NON_LEMMA for r in fail),
        "fail_breakdown": {k: sum(_fail_kind(r) == k for r in fail) for k, _ in FAIL_KINDS},
        "success_routes_pct_attempts": {k: _pct(v, len(rows)) for k, v in routes.items()},
        "steps_m_mean": ci[0] if ci else None,
        "steps_m_ci": [ci[1], ci[2]] if ci else None,
        "steps_m_median": float(np.median(steps_m)) if steps_m.size else None,
        "steps_m_p25": float(np.percentile(steps_m, 25)) if steps_m.size else None,
        "steps_m_p75": float(np.percentile(steps_m, 75)) if steps_m.size else None,
        "steps_m_max": float(steps_m.max()) if steps_m.size else None,
        "steps_m": steps_m.tolist(),
    }


def route_stats(res: hr.Results, seed: int = 0) -> dict[str, dict]:
    """Model (ladder order) -> ``{"m": m, "arms": {arm: stats}}``.

    Imputed ``missing`` cells (flag ``d`` in the main table) carry no route or steps
    and are left out, so ``n`` can be a few cells short of the main table's.
    """
    rng = np.random.default_rng(seed)
    out: dict[str, dict] = {}
    for model in hr.MODELS:
        if model not in res.chosen:
            continue
        m = res.chosen[model]
        by_arm: dict[str, list[dict]] = {a: [] for a in ARMS}
        for (mo, mm, a, _s, _r), r in res.rows.items():
            if mo == model and mm == m and a in by_arm and r.get("verdict") != "missing":
                by_arm[a].append(r)
        out[model] = {"m": m, "arms": {a: arm_stats(by_arm[a], m, rng) for a in ARMS}}
    return out


# --------------------------------------------------------------------------- tables


def _f(v: float | None, fmt: str = "{:.0f}") -> str:
    return "—" if v is None else fmt.format(v)


COLUMNS = (
    "Model",
    "arm",
    "n",
    "pass %",
    "non-lemma % of attempts",
    "non-lemma % of successes",
    "non-lemma % of failures",
    "same, failures with a recognised rule (count)",
    "success routes lemma/mixed/tree",
    "steps/m mean",
    "median",
    "p25–p75",
    "max",
)


def _row(model: str, m: int, arm: str, d: dict) -> list[str]:
    sr = d["success_routes"]
    return [
        f"{hr.PAPER_NAME[model]} (m={m})",
        arm,
        str(d["n"]),
        _f(d["pass_rate"]),
        _f(d["non_lemma_all"]),
        _f(d["non_lemma_success"]),
        _f(d["non_lemma_fail"]),
        f"{_f(d['non_lemma_fail_routed'])} ({d['n_fail_routed']})",
        f"{sr['short']}/{sr['mixed']}/{sr['long']}",
        _f(d["steps_m_mean"], "{:.2f}"),
        _f(d["steps_m_median"], "{:.2f}"),
        f"{_f(d['steps_m_p25'], '{:.2f}')}–{_f(d['steps_m_p75'], '{:.2f}')}",
        _f(d["steps_m_max"], "{:.1f}"),
    ]


def markdown_table(stats: dict[str, dict]) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "|".join(["---"] * len(COLUMNS)) + "|"]
    for model, s in stats.items():
        for arm in ARMS:
            d = s["arms"][arm]
            if d["n"]:
                lines.append("| " + " | ".join(_row(model, s["m"], arm, d)) + " |")
    return "\n".join(lines) + "\n"


def length_table(stats: dict[str, dict]) -> str:
    """Proof length on successes, lem vs both, one row per model."""
    heads = ["Model", "m", "lem n succ", "lem mean [95% CI]", "lem median", "both n succ", "both mean [95% CI]", "both median", "both − lem (mean)"]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for model, s in stats.items():
        l, b = s["arms"]["lem"], s["arms"]["both"]
        if not l["n"] and not b["n"]:
            continue
        diff = (b["steps_m_mean"] - l["steps_m_mean"]) if b["steps_m_mean"] is not None and l["steps_m_mean"] is not None else None
        lines.append(
            f"| {hr.PAPER_NAME[model]} | {s['m']} | {l['n_success']} | {_ci(l)} | {_f(l['steps_m_median'], '{:.2f}')} | "
            f"{b['n_success']} | {_ci(b)} | {_f(b['steps_m_median'], '{:.2f}')} | {_f(diff, '{:+.2f}')} |"
        )
    return "\n".join(lines) + "\n"


def _ci(d: dict) -> str:
    if d["steps_m_mean"] is None:
        return "—"
    lo, hi = d["steps_m_ci"]
    return f"{d['steps_m_mean']:.2f} [{lo:.2f}, {hi:.2f}]"


def _span(xs: list[float], fmt: str = "{:.0f}") -> str:
    """``lo–hi`` of ``xs``, or ``—`` when ``xs`` is empty."""
    return f"{fmt.format(min(xs))}–{fmt.format(max(xs))}" if xs else "—"


def reading(stats: dict[str, dict]) -> str:
    """Two or three plain sentences computed from the current numbers."""
    both = [(m, s["arms"]["both"]) for m, s in stats.items() if s["arms"]["both"]["n_success"]]
    if not both:
        return "No both-arm successes yet.\n"
    succ_share = [d["non_lemma_success"] for _, d in both]
    fail_share = [d["non_lemma_fail"] for _, d in both if d["n_fail"]]
    disc_fail = [s["arms"]["disc"]["non_lemma_fail"] for s in stats.values() if s["arms"]["disc"]["n_fail"]]
    lost = [
        (m, s["arms"]["pad"]["pass_rate"], s["arms"]["both"]["success_routes_pct_attempts"]["short"])
        for m, s in stats.items()
        if s["arms"]["pad"]["n"] and s["arms"]["both"]["n"]
    ]
    n_lost = sum(pad > short for _, pad, short in lost)
    lens = [
        (s["arms"]["lem"]["steps_m_mean"], s["arms"]["both"]["steps_m_mean"])
        for s in stats.values()
        if s["arms"]["lem"]["steps_m_mean"] is not None and s["arms"]["both"]["steps_m_mean"] is not None and s["m"] > 1
    ]
    n_longer = sum(b > l for l, b in lens)
    return (
        f"In the both arm, {_span(succ_share)}% of a model's successful proofs apply at "
        f"least one derivation-tree rule (median over models {np.median(succ_share):.0f}%), and "
        f"{_span(fail_share)}% of its failures had entered a tree before the failing step, "
        f"against {_span(disc_fail)}% of failures touching a dead rule in disc. "
        f"The lemma-only success rate in both is below pad's success rate for {n_lost} of {len(lost)} models: "
        f"usable trees pull attempts off the short route, and the tree-route successes do not make up the loss. "
        f"Successful both-arm proofs are longer than lem proofs for {n_longer} of {len(lens)} models with m > 1, "
        f"with means of {_span([b for _, b in lens], '{:.2f}')} m against "
        f"{_span([l for l, _ in lens], '{:.2f}')} m, far below the 3 m of a full tree route, "
        f"so models mix a few tree steps into a mostly lemma proof rather than replacing it.\n"
    )


def markdown(stats: dict[str, dict]) -> str:
    return (
        "# Horn bench: proof routes and proof length\n\n"
        "Generated by `notebooks/deduction/analysis/horn_routes.py`. Do not edit by hand.\n\n"
        "## Reading\n\n" + reading(stats) + "\n"
        "## Routes per model and arm\n\n" + markdown_table(stats) + "\n"
        "non-lemma = route `long` or `mixed` from the checker: a derivation-tree rule in `both`, a dead-tree rule in "
        "`disc`. Only `both` has a valid tree route; a non-lemma step in `disc` is a detour into a dead rule and "
        "fails, so every `disc` success is lemma-only; `lem` and `pad` show no non-lemma rule, so the share is 0 "
        "there by construction. For a failure the failing step's rule counts, so 'non-lemma % of failures' is the "
        "share of failures that applied or tried a non-lemma rule before failing. The next column restricts the "
        "denominator to failures with at least one recognised rule (it drops output-cap hits, empty answers and "
        "an invented first rule), count in parentheses. steps/m = valid derive lines on successes over the chain "
        "length; 1 = the lemma route, about 3 = the full depth-2 tree route; a lemma-only proof above 1 applied "
        "redundant alternative lemmas. n counts cells on disk; imputed missing cells (flag d in the main table) "
        "are left out.\n\n"
        "## Route by outcome, % of attempts, mean over models\n\n" + outcomes_markdown(stats) + "\n"
        "Figure `horn_route_outcomes.png`. Lemma route = no non-lemma rule applied, which includes failures with "
        "no valid step (cap hit, no answer, invented first rule). Each model weighs equally at its own m.\n\n"
        "### With no-proof failures split out\n\n" + outcomes5_markdown(stats) + "\n"
        f"Figure `horn_route_outcomes5.png`. 'no proof' = output-cap hit ({OUTPUT_CAP}), no answer, or no recognised "
        "step; 'lemma, failure' is then only a proof of valid lemma steps that broke.\n\n"
        "### Per model\n\n" + outcomes5_models_markdown(stats) + "\n"
        "Figure `horn_route_outcomes5_models.png`. `mean` is the arithmetic mean of each segment over models.\n\n"
        "### Failure kinds, % of attempts, pooled over all cells\n\n" + decomposition_markdown(stats) + "\n"
        f"The output cap is {OUTPUT_CAP} tokens; the largest prompts "
        "leave about 101k-126k). A cap hit has no derive lines. 'invalid step after valid lemma steps' is a "
        "lemma-only route that broke: an invented rule or a lemma whose premise was not yet derived. 'after "
        "entering a tree' exists only in both (dead-tree detours in disc count here too). Pooled, not "
        "model-averaged, so it differs slightly from the tables above.\n\n"
        "## Proof length on successes, high (lem) vs low density (both)\n\n" + length_table(stats) + "\n"
        "Mean steps/m with a 95% percentile-bootstrap CI over cells (5000 draws). The distribution is the right "
        "panel of `horn_routes.png`: boxes give the median and quartiles, whiskers 1.5 IQR, no outliers, and the "
        f"axis is clipped at {Y_CLIP}. Ministral 3B and 8B run at m = 1, where one extra step doubles the ratio.\n"
    )


def latex(stats: dict[str, dict]) -> str:
    """One row per model and arm: n, pass rate, the three non-lemma shares, steps/m."""
    heads = [
        "Model", "arm", "$n$", "pass \\%", "non-lemma \\% attempts", "non-lemma \\% successes",
        "non-lemma \\% failures", "steps/$m$ mean", "steps/$m$ median",
    ]
    lines = [
        "% Generated by notebooks/deduction/analysis/horn_routes.py. Needs booktabs.",
        "\\begin{tabular}{llrrrrrrr}",
        "\\toprule",
        " & ".join(heads) + " \\\\",
        "\\midrule",
    ]
    first = True
    for model, s in stats.items():
        if not any(s["arms"][a]["n"] for a in ARMS):
            continue
        if not first:
            lines.append("\\addlinespace")
        first = False
        for i, arm in enumerate(ARMS):
            d = s["arms"][arm]
            if not d["n"]:
                continue
            name = f"{hr.PAPER_NAME[model]} ($m={s['m']}$)" if i == 0 else ""
            lines.append(
                f"{name} & {arm} & {d['n']} & {_f(d['pass_rate'])} & {_f(d['non_lemma_all'])} & "
                f"{_f(d['non_lemma_success'])} & {_f(d['non_lemma_fail'])} & "
                f"{_f(d['steps_m_mean'], '{:.2f}')} & {_f(d['steps_m_median'], '{:.2f}')} \\\\"
            )
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- figure


def figure(stats: dict[str, dict], out: Path | None = None):
    """Left: both-arm successes by route as % of attempts (stacked), pad's pass rate as a
    marker. Right: steps/m on successes, lem vs both, boxes (median, quartiles, 1.5 IQR
    whiskers, no outliers) clipped at ``Y_CLIP``."""
    import matplotlib.pyplot as plt

    models = [m for m in stats if stats[m]["arms"]["both"]["n"] and stats[m]["arms"]["lem"]["n"]]
    names = [hr.PAPER_NAME[m] for m in models]
    xs = np.arange(len(models))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    bottom = np.zeros(len(models))
    for key, label in ROUTES:
        vals = np.array([stats[m]["arms"]["both"]["success_routes_pct_attempts"][key] or 0.0 for m in models])
        ax1.bar(xs, vals, bottom=bottom, label=f"both: {label}")
        bottom += vals
    pad = [stats[m]["arms"]["pad"]["pass_rate"] if stats[m]["arms"]["pad"]["n"] else np.nan for m in models]
    ax1.plot(xs, pad, linestyle="none", marker="_", markersize=14, markeredgewidth=2, color="black", label="pad: pass rate (all lemma only)")
    ax1.set_xticks(xs)
    ax1.set_xticklabels(names, rotation=45, ha="right")
    ax1.set_ylabel("% of attempts, low density (both)")
    ax1.set_ylim(0, 100)
    ax1.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8, frameon=False)

    width = 0.38
    for k, (arm, label) in enumerate(LENGTH_ARMS):
        data = [stats[m]["arms"][arm]["steps_m"] or [np.nan] for m in models]
        bp = ax2.boxplot(
            data,
            positions=xs + (k - 0.5) * width,
            widths=width * 0.9,
            showfliers=False,
            patch_artist=True,
            medianprops={"color": "black"},
        )
        color = f"C{k}"
        for box in bp["boxes"]:
            box.set_facecolor(color)
            box.set_alpha(0.6)
        ax2.bar([np.nan], [np.nan], color=color, alpha=0.6, label=label)
    ax2.axhline(1.0, linestyle=":", color="black", linewidth=1)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(names, rotation=45, ha="right")
    ax2.set_ylabel("proof steps / m (successes)")
    ax2.set_ylim(0.8, Y_CLIP)
    ax2.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()

    if out is not None:
        fig.savefig(out / "horn_routes.pdf", bbox_inches="tight")
        fig.savefig(out / "horn_routes.png", dpi=150, bbox_inches="tight")
    return fig


OUTCOME_ARMS = ("lem", "pad", "both")
OUTCOMES = (
    ("lemma_success", "lemma, success"),
    ("lemma_fail", "lemma, failure"),
    ("tree_success", "tree, success"),
    ("tree_fail", "tree, failure"),
)
#: Under each bar of the per-model figure: H = high density, H+I = high density + irrelevant, L = low density.
BAR_LABEL = ("H", "H+I", "L")
#: Arm labels on the outcome figures: the paper's names, never the arm codes.
OUTCOME_ARM_LABEL = {"lem": "high density", "pad": "high density +\nirrelevant", "both": "low density"}


def outcome_shares(stats: dict[str, dict], arms: tuple[str, ...] = OUTCOME_ARMS) -> dict[str, dict[str, float]]:
    """Arm -> outcome -> % of attempts, averaged over models (each model weighs equally).

    "lemma route" = no non-lemma rule applied, which includes failures with no valid
    step at all (cap hit, no answer, invented first rule). Only ``both`` can show a tree
    rule; in ``lem`` and ``pad`` the two tree segments are 0 by construction.
    """
    out: dict[str, dict[str, float]] = {}
    for arm in arms:
        acc = {k: [] for k, _ in OUTCOMES}
        for s in stats.values():
            d = s["arms"][arm]
            if not d["n"]:
                continue
            ts, tf = d["n_non_lemma_success"], d["n_non_lemma_fail"]
            acc["tree_success"].append(100.0 * ts / d["n"])
            acc["tree_fail"].append(100.0 * tf / d["n"])
            acc["lemma_success"].append(100.0 * (d["n_success"] - ts) / d["n"])
            acc["lemma_fail"].append(100.0 * (d["n_fail"] - tf) / d["n"])
        out[arm] = {k: float(np.mean(v)) if v else 0.0 for k, v in acc.items()}
    return out


def figure_outcomes(stats: dict[str, dict], out: Path | None = None):
    """One stacked bar per arm: lemma route vs tree rule, succeeded vs failed."""
    import matplotlib.pyplot as plt

    shares = outcome_shares(stats)
    n_models = sum(1 for s in stats.values() if s["arms"]["both"]["n"])
    fig, ax = plt.subplots(figsize=(5, 4))
    xs = np.arange(len(OUTCOME_ARMS))
    bottom = np.zeros(len(OUTCOME_ARMS))
    style = {"lemma_success": ("C0", ""), "lemma_fail": ("C0", "//"), "tree_success": ("C1", ""), "tree_fail": ("C1", "//")}
    for key, label in OUTCOMES:
        vals = np.array([shares[a][key] for a in OUTCOME_ARMS])
        color, hatch = style[key]
        ax.bar(xs, vals, bottom=bottom, color=color, hatch=hatch, edgecolor="white", label=label,
               alpha=1.0 if not hatch else 0.55)
        for x, v, b in zip(xs, vals, bottom):
            if v >= 4:
                ax.text(x, b + v / 2, f"{v:.0f}", ha="center", va="center", fontsize=9)
        bottom += vals
    ax.set_xticks(xs)
    ax.set_xticklabels([OUTCOME_ARM_LABEL[a] for a in OUTCOME_ARMS], fontsize=9)
    ax.set_ylabel(f"% of attempts, mean over {n_models} models")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    fig.tight_layout()
    if out is not None:
        fig.savefig(out / "horn_route_outcomes.pdf", bbox_inches="tight")
        fig.savefig(out / "horn_route_outcomes.png", dpi=150, bbox_inches="tight")
    return fig


def decomposition_markdown(stats: dict[str, dict]) -> str:
    """Failure kinds per arm as % of attempts, pooled over all cells of all models."""
    heads = ["failure kind"] + list(ARMS)
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    n = {a: sum(s["arms"][a]["n"] for s in stats.values()) for a in ARMS}
    for key, label in FAIL_KINDS:
        cells = []
        for a in ARMS:
            k = sum(s["arms"][a]["fail_breakdown"][key] for s in stats.values())
            cells.append(f"{100.0 * k / n[a]:.1f}" if n[a] else "—")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    succ = [f"{100.0 * sum(s['arms'][a]['n_success'] for s in stats.values()) / n[a]:.1f}" if n[a] else "—" for a in ARMS]
    lines.append("| success | " + " | ".join(succ) + " |")
    lines.append("| n attempts | " + " | ".join(str(n[a]) for a in ARMS) + " |")
    return "\n".join(lines) + "\n"


OUTCOMES5 = (
    ("lemma_success", "lemma, success"),
    ("lemma_fail", "lemma, failure"),
    ("no_proof", "no proof"),
    ("tree_success", "tree, success"),
    ("tree_fail", "tree, failure"),
)


def outcome_shares5(stats: dict[str, dict], arms: tuple[str, ...] = OUTCOME_ARMS) -> dict[str, dict[str, float]]:
    """Like ``outcome_shares`` but failures with no route are their own segment."""
    out: dict[str, dict[str, float]] = {}
    for arm in arms:
        acc = {k: [] for k, _ in OUTCOMES5}
        for s in stats.values():
            d = s["arms"][arm]
            if not d["n"]:
                continue
            fb = d["fail_breakdown"]
            acc["tree_success"].append(100.0 * d["n_non_lemma_success"] / d["n"])
            acc["tree_fail"].append(100.0 * fb["tree"] / d["n"])
            acc["lemma_success"].append(100.0 * (d["n_success"] - d["n_non_lemma_success"]) / d["n"])
            acc["lemma_fail"].append(100.0 * fb["lemma"] / d["n"])
            acc["no_proof"].append(100.0 * (fb["cap"] + fb["no_route"] + fb["no_answer"]) / d["n"])
        out[arm] = {k: float(np.mean(v)) if v else 0.0 for k, v in acc.items()}
    return out


def figure_outcomes5(stats: dict[str, dict], out: Path | None = None):
    """Five segments per arm: the four of ``figure_outcomes`` with no-proof failures split out."""
    import matplotlib.pyplot as plt

    shares = outcome_shares5(stats)
    n_models = sum(1 for s in stats.values() if s["arms"]["both"]["n"])
    fig, ax = plt.subplots(figsize=(5, 4))
    xs = np.arange(len(OUTCOME_ARMS))
    bottom = np.zeros(len(OUTCOME_ARMS))
    style = {"lemma_success": ("C0", "", 1.0), "lemma_fail": ("C0", "//", 0.55), "no_proof": ("0.6", "", 1.0),
             "tree_success": ("C1", "", 1.0), "tree_fail": ("C1", "//", 0.55)}
    for key, label in OUTCOMES5:
        vals = np.array([shares[a][key] for a in OUTCOME_ARMS])
        color, hatch, alpha = style[key]
        ax.bar(xs, vals, bottom=bottom, color=color, hatch=hatch, edgecolor="white", label=label, alpha=alpha)
        for x, v, b in zip(xs, vals, bottom):
            if v >= 4:
                ax.text(x, b + v / 2, f"{v:.0f}", ha="center", va="center", fontsize=9)
        bottom += vals
    ax.set_xticks(xs)
    ax.set_xticklabels([OUTCOME_ARM_LABEL[a] for a in OUTCOME_ARMS], fontsize=9)
    ax.set_ylabel(f"% of attempts, mean over {n_models} models")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False)
    fig.tight_layout()
    if out is not None:
        fig.savefig(out / "horn_route_outcomes5.pdf", bbox_inches="tight")
        fig.savefig(out / "horn_route_outcomes5.png", dpi=150, bbox_inches="tight")
    return fig


def outcomes5_markdown(stats: dict[str, dict]) -> str:
    shares = outcome_shares5(stats)
    heads = ["arm"] + [label for _, label in OUTCOMES5]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for arm in OUTCOME_ARMS:
        lines.append(f"| {OUTCOME_ARM_LABEL[arm].replace(chr(10), ' ')} | " + " | ".join(f"{shares[arm][k]:.1f}" for k, _ in OUTCOMES5) + " |")
    return "\n".join(lines) + "\n"


def outcome_shares5_by_model(stats: dict[str, dict], arms: tuple[str, ...] = OUTCOME_ARMS) -> dict[str, dict[str, dict[str, float]]]:
    """Model -> arm -> outcome -> % of that model's attempts in that arm."""
    out: dict[str, dict[str, dict[str, float]]] = {}
    for model, s in stats.items():
        per_arm: dict[str, dict[str, float]] = {}
        for arm in arms:
            d = s["arms"][arm]
            if not d["n"]:
                continue
            fb = d["fail_breakdown"]
            n = d["n"]
            per_arm[arm] = {
                "lemma_success": 100.0 * (d["n_success"] - d["n_non_lemma_success"]) / n,
                "lemma_fail": 100.0 * fb["lemma"] / n,
                "no_proof": 100.0 * (fb["cap"] + fb["no_route"] + fb["no_answer"]) / n,
                "tree_success": 100.0 * d["n_non_lemma_success"] / n,
                "tree_fail": 100.0 * fb["tree"] / n,
            }
        if per_arm:
            out[model] = per_arm
    return out


def _summary_groups(by_model: dict[str, dict[str, dict[str, float]]], arms: tuple[str, ...]) -> dict[str, dict[str, dict[str, float]]]:
    """``mean``: arithmetic mean of each segment over models."""
    out: dict[str, dict[str, dict[str, float]]] = {"mean": {}}
    for arm in arms:
        rows = [d[arm] for d in by_model.values() if arm in d]
        if not rows:
            continue
        keys = [k for k, _ in OUTCOMES5]
        mat = np.array([[r[k] for k in keys] for r in rows])
        out["mean"][arm] = dict(zip(keys, mat.mean(axis=0)))
    return out


def figure_outcomes5_models(stats: dict[str, dict], out: Path | None = None):
    """Per model, three stacked bars (high density, high density + irrelevant, low density),
    five segments, H / H+I / L under each bar, plus a mean group at the right."""
    import matplotlib.pyplot as plt

    by_model = outcome_shares5_by_model(stats)
    groups = {hr.PAPER_NAME[m]: d for m, d in by_model.items()}
    groups.update(_summary_groups(by_model, OUTCOME_ARMS))
    names = list(groups)
    xs = np.arange(len(names))
    width = 0.27
    style = {"lemma_success": ("C0", "", 1.0), "lemma_fail": ("C0", "//", 0.55), "no_proof": ("0.6", "", 1.0),
             "tree_success": ("C1", "", 1.0), "tree_fail": ("C1", "//", 0.55)}
    fig, ax = plt.subplots(figsize=(12, 4))
    for k, arm in enumerate(OUTCOME_ARMS):
        pos = xs + (k - 1) * width
        bottom = np.zeros(len(names))
        for key, label in OUTCOMES5:
            vals = np.array([groups[n].get(arm, {}).get(key, 0.0) for n in names])
            color, hatch, alpha = style[key]
            ax.bar(pos, vals, bottom=bottom, width=width, color=color, hatch=hatch, edgecolor="white",
                   linewidth=0.5, alpha=alpha, label=label if k == 0 else None)
            bottom += vals
    ax.axvline(len(by_model) - 0.5, color="black", linewidth=0.8, linestyle=":")
    for k, short in enumerate(BAR_LABEL):
        for x in xs:
            ax.text(x + (k - 1) * width, -1.5, short, ha="center", va="top", fontsize=6)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.tick_params(axis="x", length=0, pad=10)
    ax.set_ylabel("% of attempts")
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.6, len(names) - 0.4)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=5, fontsize=8, frameon=False,
              title="H = high density, H+I = high density + irrelevant, L = low density", title_fontsize=8)
    fig.tight_layout()
    if out is not None:
        fig.savefig(out / "horn_route_outcomes5_models.pdf", bbox_inches="tight")
        fig.savefig(out / "horn_route_outcomes5_models.png", dpi=150, bbox_inches="tight")
    return fig


def outcomes5_models_markdown(stats: dict[str, dict]) -> str:
    by_model = outcome_shares5_by_model(stats)
    groups = {hr.PAPER_NAME[m]: d for m, d in by_model.items()}
    groups.update(_summary_groups(by_model, OUTCOME_ARMS))
    heads = ["Model", "arm"] + [label for _, label in OUTCOMES5]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for name, d in groups.items():
        for arm in OUTCOME_ARMS:
            if arm in d:
                lines.append(f"| {name} | {OUTCOME_ARM_LABEL[arm].replace(chr(10), ' ')} | "
                             + " | ".join(f"{d[arm][k]:.1f}" for k, _ in OUTCOMES5) + " |")
    return "\n".join(lines) + "\n"


def outcomes_markdown(stats: dict[str, dict]) -> str:
    shares = outcome_shares(stats)
    heads = ["arm"] + [label for _, label in OUTCOMES]
    lines = ["| " + " | ".join(heads) + " |", "|" + "|".join(["---"] * len(heads)) + "|"]
    for arm in OUTCOME_ARMS:
        lines.append(f"| {OUTCOME_ARM_LABEL[arm].replace(chr(10), ' ')} | " + " | ".join(f"{shares[arm][k]:.1f}" for k, _ in OUTCOMES) + " |")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- driver


def write_outputs(stats: dict[str, dict], out: Path = hr.OUT, figures: bool = True) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = [out / "horn_routes.md", out / "horn_routes.tex", out / "horn_routes.json"]
    written[0].write_text(markdown(stats), encoding="utf-8")
    written[1].write_text(latex(stats), encoding="utf-8")
    slim = {
        m: {"m": s["m"], "arms": {a: {k: v for k, v in d.items() if k != "steps_m"} for a, d in s["arms"].items()}}
        for m, s in stats.items()
    }
    written[2].write_text(json.dumps(slim, indent=1), encoding="utf-8")
    if figures:
        import matplotlib.pyplot as plt

        plt.close(figure(stats, out))
        plt.close(figure_outcomes(stats, out))
        plt.close(figure_outcomes5(stats, out))
        plt.close(figure_outcomes5_models(stats, out))
        written += [out / f"horn_{k}.{ext}" for k in ("routes", "route_outcomes", "route_outcomes5", "route_outcomes5_models") for ext in ("png", "pdf")]
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--data", type=Path, required=True, help="the released results folder")
    ap.add_argument("--scoring", choices=list(hr.SCORING_MODES), default=hr.DEFAULT_SCORING)
    ap.add_argument("--out", type=Path, default=hr.OUT, help="outputs go to <out>/<scoring>/")
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args(argv)
    if not a.no_figures:
        import matplotlib

        matplotlib.use("Agg")
    res = hr.run_pipeline(a.data, scoring=a.scoring)
    stats = route_stats(res)
    written = write_outputs(stats, a.out / a.scoring, not a.no_figures)
    print(markdown(stats))
    print("Wrote " + ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
