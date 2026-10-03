"""Accuracy table for the induction study, from a results folder.

    python notebooks/induction/analysis/induction_results.py --data <results folder> --out <dir>

Reads ``<data>/induction/<model>/seed=<seed>/<arm>--<run stamp>.yaml``: the released
results, or a ``run_study.py`` run, as ``python -m smolbench.induction.repro fetch``
downloads them. Checks the folder against the published runs (``--skip-check`` for your
own run), then writes:

* ``induction_table.tex``: the paper table (``tab:induction-results``). One row per model,
  ladder order, the accuracy of the high-density (``intens``), high-density + irrelevant
  (``noise_intens``) and low-density (``extens``) arms, and the two deltas against low
  density.
* ``induction_table.md``: the same table in markdown, with the number of seeds per model.
* ``induction_summary.json``: every number in the tables.

Statistics (``smolbench.induction.repro``). A replicate's accuracy is the fraction of its 9
marks scored correct; a ``null`` score is wrong. A cell is the mean over seeds; its ``±``
is the sample standard deviation over seeds (``--spread sd``, as published), twice that
(``2sd``), or the half-width of the 95% t confidence interval for the mean (``ci``). Bold
marks the row's highest mean, ties included. A delta is ``100 x (a - b)`` in points from
the means rounded to three decimals, as printed.

usage: induction_results.py --data DIR --out DIR [--spread sd|2sd|ci] [--skip-check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# pylint: disable=wrong-import-position
from smolbench.induction.repro import (  # noqa: E402
    DELTAS,
    cell_stats,
    check_data,
    delta,
    load_cells,
    load_protocol,
)

#: Family -> models, small to large, in the paper's family order.
FAMILIES = (
    ("Gemma 4", ("gemma-4-e2b", "gemma-4-12b", "gemma-4-31b")),
    ("Nemotron 3", ("nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b")),
    ("Qwen3.5", ("qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b")),
    ("DeepSeek", ("deepseek-v4-flash", "deepseek-v3.1")),
    ("GLM", ("glm-4.7-flash", "glm-4.7")),
    ("Ministral 3", ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b")),
)
ARMS = ("intens", "noise_intens", "extens")
#: Two-sided 95% t quantile with ``df`` degrees of freedom, to three decimals.
T_975 = {9: 2.262, 19: 2.093, 29: 2.045}
#: ``--spread`` -> (what ± means in the caption, table label).
SPREADS = {
    "sd": (r"$\pm$ one sample standard deviation across seeds", "tab:induction-results"),
    "2sd": (r"$\pm$ two sample standard deviations across seeds", "tab:induction-results-2sd"),
    "ci": (r"$\pm$ the half-width of the $95\%$ $t$ confidence interval for the mean", "tab:induction-results-ci95"),
}
HEADER = r"""\begin{table}[t]
    \centering
    \footnotesize
    LLM Induction Accuracy
    \begin{tabular}{lcccrr}
        \toprule
        Model
            & \makecell{high density}
            & \makecell{high density \\ $+$ irrelevant}
            & \makecell{low density}
            & \makecell{$\Delta$ (high \\ $-$ low)}
            & \makecell{$\Delta$ (irrelevant \\ $-$ low)} \\
        \hline"""
CAPTION = (
    "For induction, LLMs with high density information generally outperform low "
    "density information, even when context length is accounted for by appending "
    "irrelevant information to high density information. Each cell is the mean "
    "accuracy over {n} seeds {spread}."
)


def summarise(cells: dict[tuple[str, str], dict[int, float]]) -> dict[str, dict]:
    """Per-model cell statistics and deltas, in ladder order.

    Models outside the roster follow the roster, in name order.

    Parameters
    ----------
    cells : dict[tuple[str, str], dict[int, float]]
        ``(model, arm)`` -> ``{seed: accuracy}``, from ``repro.load_cells``.

    Returns
    -------
    dict[str, dict]
        Model -> ``{"name", "family", "n", "arms": {arm: {"mean", "sd"}}, "deltas"}``.
    """
    names = {key: e["name"] for key, e in load_protocol()["models"].items()}
    family = {m: f for f, ms in FAMILIES for m in ms}
    found = {m for m, _ in cells}
    order = [m for _, ms in FAMILIES for m in ms if m in found] + sorted(found - set(family))
    summary = {}
    for model in order:
        stats = {arm: cell_stats(cells[model, arm]) for arm in ARMS if (model, arm) in cells}
        summary[model] = {
            "name": names.get(model, model),
            "family": family.get(model, "other"),
            "n": min(len(cells[model, arm]) for arm in stats),
            "arms": {arm: {"mean": m, "sd": sd} for arm, (m, sd) in stats.items()},
            "deltas": {f"{a}-{b}": delta(stats[a][0], stats[b][0]) for a, b in DELTAS if a in stats and b in stats},
        }
    return summary


def spread_of(sd: float, n: int, spread: str) -> float:
    """The ``±`` of one cell.

    Parameters
    ----------
    sd : float
        Sample standard deviation over seeds.
    n : int
        Number of seeds.
    spread : str
        A ``SPREADS`` key.

    Returns
    -------
    float
        ``sd``, ``2 * sd`` or the 95% t half-width ``t * sd / sqrt(n)``.

    Raises
    ------
    ValueError
        For ``ci`` with a seed count ``T_975`` has no quantile for.
    """
    if spread == "sd":
        return sd
    if spread == "2sd":
        return 2 * sd
    if n - 1 not in T_975:
        raise ValueError(f"no 95% t quantile recorded for {n} seeds; known: {sorted(d + 1 for d in T_975)}")
    return T_975[n - 1] * sd / n**0.5


def fmt_delta(points: float) -> str:
    """One-decimal delta, with a negative wrapped in math mode for the minus sign.

    Parameters
    ----------
    points : float
        Delta in points.

    Returns
    -------
    str
        LaTeX for the cell.
    """
    return f"{points:.1f}" if points >= 0 else f"$-{abs(points):.1f}$"


def latex_table(summary: dict[str, dict], spread: str = "sd") -> str:
    """LaTeX for the paper table.

    Parameters
    ----------
    summary : dict[str, dict]
        Output of ``summarise``; every model needs all three arms.
    spread : str
        A ``SPREADS`` key.

    Returns
    -------
    str
        The ``table`` environment.
    """
    rows = []
    previous = None
    for s in summary.values():
        best = max(a["mean"] for a in s["arms"].values())
        cells = [s["name"]]
        for arm in ARMS:
            a = s["arms"][arm]
            body = f"{a['mean']:.3f} \\pm {spread_of(a['sd'], s['n'], spread):.3f}"
            cells.append(f"$\\mathbf{{{body}}}$" if a["mean"] == best else f"${body}$")
        cells += [fmt_delta(s["deltas"][f"{a}-{b}"]) for a, b in DELTAS]
        rows.append((r"\addlinespace" if previous not in (None, s["family"]) else None, cells))
        previous = s["family"]
    widths = [max(len(cells[i]) for _, cells in rows) for i in range(6)]
    lines = [HEADER]
    for rule, cells in rows:
        if rule:
            lines.append(f"        {rule}")
        padded = [cells[0].ljust(widths[0])] + [c.rjust(w) for c, w in zip(cells[1:], widths[1:])]
        lines.append("        " + " & ".join(padded) + r" \\")
    seeds = sorted({s["n"] for s in summary.values()})
    text, label = SPREADS[spread]
    lines += [
        r"        \bottomrule",
        r"    \end{tabular}",
        f"    \\caption{{{CAPTION.format(n='/'.join(map(str, seeds)), spread=text)}}}",
        f"    \\label{{{label}}}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def markdown_table(summary: dict[str, dict], spread: str = "sd") -> str:
    """The paper table in markdown, with the seeds per model.

    Parameters
    ----------
    summary : dict[str, dict]
        Output of ``summarise``.
    spread : str
        A ``SPREADS`` key.

    Returns
    -------
    str
        A markdown table.
    """
    head = "| Model | n | high density | high density + irrelevant | low density | Δ (high − low) | Δ (irrelevant − low) |"
    lines = [head, "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summary.values():
        cells = [s["name"], str(s["n"])]
        for arm in ARMS:
            a = s["arms"].get(arm)
            cells.append(f"{a['mean']:.3f} ± {spread_of(a['sd'], s['n'], spread):.3f}" if a else "")
        cells += [f"{s['deltas'][f'{a}-{b}']:+.1f}" if f"{a}-{b}" in s["deltas"] else "" for a, b in DELTAS]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def published_mismatches(summary: dict[str, dict]) -> tuple[int, list[str]]:
    """Compare the printed cells (mean, sd, deltas) with the published table.

    Parameters
    ----------
    summary : dict[str, dict]
        Output of ``summarise``.

    Returns
    -------
    tuple[int, list[str]]
        ``(cells compared, one line per cell that differs)``.
    """
    compared, diffs = 0, []
    for model, e in load_protocol()["models"].items():
        if model not in summary:
            continue
        got, ref = summary[model], e["results"]
        for arm in ARMS:
            for field in ("mean", "sd"):
                compared += 1
                want, have = f"{ref[arm][field]:.3f}", f"{got['arms'][arm][field]:.3f}"
                if want != have:
                    diffs.append(f"{model} {arm} {field}: {have}, published {want}")
        for name, have in got["deltas"].items():
            compared += 1
            if f"{have:.1f}" != f"{ref[name]:.1f}":
                diffs.append(f"{model} {name}: {have:.1f}, published {ref[name]:.1f}")
    return compared, diffs


def write_outputs(summary: dict[str, dict], out: Path, spread: str = "sd") -> list[Path]:
    """Write the tables and the JSON summary under ``out``.

    Parameters
    ----------
    summary : dict[str, dict]
        Output of ``summarise``.
    out : Path
        Output directory, created if missing.
    spread : str
        A ``SPREADS`` key.

    Returns
    -------
    list[Path]
        The files written.
    """
    out.mkdir(parents=True, exist_ok=True)
    written = [out / "induction_table.tex", out / "induction_table.md", out / "induction_summary.json"]
    written[0].write_text(latex_table(summary, spread), encoding="utf-8")
    written[1].write_text(markdown_table(summary, spread), encoding="utf-8")
    written[2].write_text(json.dumps({"spread": spread, "models": summary}, indent=1) + "\n", encoding="utf-8")
    return written


def main(argv: list[str] | None = None) -> int:
    """Check the data, then write and print the tables.

    Parameters
    ----------
    argv : list[str] | None
        Arguments; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        Exit status: 1 when the data check fails.
    """
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--data", type=Path, required=True, help="the results folder")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--spread", choices=list(SPREADS), default="sd", help="what ± means in the arm columns")
    ap.add_argument("--skip-check", action="store_true", help="do not check the data against the published runs")
    a = ap.parse_args(argv)
    if not a.skip_check:
        problems = check_data(a.data)
        if problems:
            for p in problems[:20]:
                print(f"data: {p}")
            print(f"data: {len(problems)} problems; pass --skip-check for your own run")
            return 1
        print(f"data: {a.data} matches the published runs")
    summary = summarise(load_cells(a.data))
    written = write_outputs(summary, a.out, a.spread)
    print(markdown_table(summary, a.spread))
    compared, diffs = published_mismatches(summary)
    for line in diffs:
        print(f"- {line}")
    print(f"{compared - len(diffs)} of {compared} cells match the published table")
    print("Wrote " + ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
