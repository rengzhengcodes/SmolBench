"""Reproduce the induction results of the ICLR 2027 submission.

    python -m smolbench.induction.repro models
    python -m smolbench.induction.repro fetch --out <results folder>
    python -m smolbench.induction.repro check-data <results folder>
    python -m smolbench.induction.repro report <results folder>

``iclr.json`` (next to this file) records the protocol: the public bucket, seeds, arms,
every model's pinned checkpoint, a SHA-256 digest of each seed's published runs, and the
published accuracies. ``fetch`` copies the released ``induction/`` results prefix into a
local folder with its key layout,
``<folder>/induction/<model>/seed=<seed>/<arm>--<run stamp>.yaml``. ``check-data`` checks
a folder against the recorded digests. ``report`` scores a folder and prints it next to
the published values.

A replicate's accuracy is the fraction of its marks with a truthy ``score``; a ``null``
score (an answer that could not be graded) counts as wrong. A replicate collected more
than once keeps its earliest surviving run. Files are read as plain YAML because the
released records predate later metadata fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Optional

from smolbench import public_release

PROTOCOL_PATH = Path(__file__).with_name("iclr.json")
#: Marker suffix identifying a superseded run.
SUPERSEDED_SUFFIX = ".superseded"
#: (a, b) -> delta "a-b", both relative to the low-density arm.
DELTAS = (("intens", "extens"), ("noise_intens", "extens"))
Cells = dict[tuple[str, str], dict[int, float]]


def load_protocol() -> dict:
    """Read the recorded protocol.

    Returns
    -------
    dict
        The contents of ``iclr.json``.
    """
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def parse_seeds(spec: str) -> list[int]:
    """Expand a seed list such as ``"0-29"`` or ``"0-2,7"``.

    Parameters
    ----------
    spec : str
        Comma-separated seeds and inclusive ``a-b`` ranges.

    Returns
    -------
    list[int]
        The seeds in the order given.
    """
    seeds: list[int] = []
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        seeds += range(int(lo), int(hi or lo) + 1)
    return seeds


def select_runs(data: Path, arms: tuple[str, ...]) -> dict[tuple[str, int, str], Path]:
    """Find the run that counts for every replicate in a results folder.

    Parameters
    ----------
    data : Path
        Results folder holding ``induction/<model>/seed=<seed>/``.
    arms : tuple[str, ...]
        Arms to select; others (such as ``zero``) are skipped.

    Returns
    -------
    dict[tuple[str, int, str], Path]
        ``(model, seed, arm)`` -> the earliest run without a ``.superseded`` marker.
    """
    root = data / load_protocol()["prefix"]
    runs: dict[tuple[str, int, str], list[str]] = {}
    for seed_dir in sorted(root.glob("*/seed=*")):
        names = {p.name for p in seed_dir.iterdir()}
        for name in names:
            arm, sep, stamp = name.removesuffix(".yaml").partition("--")
            if not name.endswith(".yaml") or not sep or arm not in arms:
                continue
            if name.removesuffix(".yaml") + SUPERSEDED_SUFFIX in names:
                continue
            seed = int(seed_dir.name.removeprefix("seed="))
            runs.setdefault((seed_dir.parent.name, seed, arm), []).append(stamp)
    return {
        (model, seed, arm): root / model / f"seed={seed}" / f"{arm}--{min(stamps)}.yaml"
        for (model, seed, arm), stamps in runs.items()
    }


def seed_digest(runs: dict[str, Path]) -> str:
    """SHA-256 over the name and bytes of one seed's runs, in arm order.

    Parameters
    ----------
    runs : dict[str, Path]
        Arm -> the run selected for it.

    Returns
    -------
    str
        Hex digest.
    """
    h = hashlib.sha256()
    for arm in load_protocol()["arms"]:
        h.update(f"{arm}/{runs[arm].name}".encode() + b"\0")
        h.update(runs[arm].read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def check_data(data: Path) -> list[str]:
    """Compare a results folder with the recorded digests.

    Parameters
    ----------
    data : Path
        Results folder to check.

    Returns
    -------
    list[str]
        Problems found; empty when every published replicate is identical.
    """
    proto = load_protocol()
    runs = select_runs(data, tuple(proto["arms"]))
    problems = []
    for model, digests in proto["seed_digests"].items():
        for seed, digest in digests.items():
            where = f"{model}/seed={seed}"
            found = {arm: runs.get((model, int(seed), arm)) for arm in proto["arms"]}
            missing = [arm for arm, path in found.items() if path is None]
            if missing:
                problems.append(f"{where}: missing {', '.join(missing)}")
            elif seed_digest(found) != digest:
                problems.append(f"{where}: digest differs from the published runs")
    return problems


def replicate_accuracy(path: Path) -> float:
    """Score one replicate: the fraction of its marks with a truthy ``score``.

    Parameters
    ----------
    path : Path
        A replicate's result file.

    Returns
    -------
    float
        Accuracy in ``[0, 1]``; a ``null`` score counts as wrong.

    Raises
    ------
    ValueError
        If the file does not hold the protocol's number of marks.
    """
    import yaml  # pylint: disable=import-outside-toplevel

    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    marks = yaml.load(path.read_text(encoding="utf-8"), Loader=loader)["marks"]
    expected = load_protocol()["marks_per_replicate"]
    if len(marks) != expected:
        raise ValueError(f"{path}: {len(marks)} marks, expected {expected}")
    return sum(bool(mark["score"]) for mark in marks) / len(marks)


def load_cells(data: Path) -> Cells:
    """Score every selected replicate in a results folder.

    Parameters
    ----------
    data : Path
        Results folder to score.

    Returns
    -------
    Cells
        ``(model, arm)`` -> ``{seed: accuracy}``.
    """
    cells: Cells = {}
    for (model, seed, arm), path in sorted(
        select_runs(data, tuple(load_protocol()["arms"])).items()
    ):
        cells.setdefault((model, arm), {})[seed] = replicate_accuracy(path)
    return cells


def cell_stats(per_seed: dict[int, float]) -> tuple[float, float]:
    """Mean and sample standard deviation (ddof = 1) over seeds.

    Parameters
    ----------
    per_seed : dict[int, float]
        Seed -> replicate accuracy.

    Returns
    -------
    tuple[float, float]
        ``(mean, sd)``; ``sd`` is 0 for a single seed.
    """
    values = list(per_seed.values())
    return statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0


def delta(mean_a: float, mean_b: float) -> float:
    """``a - b`` in points, from the means rounded to three decimals as printed.

    Parameters
    ----------
    mean_a : float
        Mean accuracy of arm ``a``.
    mean_b : float
        Mean accuracy of arm ``b``.

    Returns
    -------
    float
        ``100 * (round(mean_a, 3) - round(mean_b, 3))``.
    """
    return 100 * (round(mean_a, 3) - round(mean_b, 3))


def report(data: Path) -> str:
    """Accuracies and deltas per model, next to the published values.

    Parameters
    ----------
    data : Path
        Results folder to score.

    Returns
    -------
    str
        One block per model found in the folder.
    """
    proto = load_protocol()
    cells = load_cells(data)
    lines = []
    order = list(proto["models"])
    for model in sorted(
        {m for m, _ in cells},
        key=lambda m: (order.index(m) if m in order else len(order), m),
    ):
        ref = proto["models"].get(model, {}).get("results", {})
        stats = {
            arm: cell_stats(cells[model, arm])
            for arm in proto["arms"]
            if (model, arm) in cells
        }
        seeds = sorted({s for (m, _), v in cells.items() if m == model for s in v})
        lines.append(f"== {model}: {len(seeds)} seeds")
        lines.append(
            f"   {'':20s} {'mean':>6s} {'sd':>6s}"
            + (f" {'published':>16s}" if ref else "")
        )
        for arm, (mean, sd) in stats.items():
            row = f"   {arm:20s} {mean:6.3f} {sd:6.3f}"
            if arm in ref:
                row += f" {ref[arm]['mean']:9.3f} {ref[arm]['sd']:6.3f}"
            lines.append(row)
        for a, b in DELTAS:
            if a in stats and b in stats:
                name = f"{a}-{b}"
                row = f"   {name:20s} {delta(stats[a][0], stats[b][0]):+6.1f}"
                lines.append(
                    row + (f" {'':6s} {ref[name]:+9.1f}" if name in ref else "")
                )
    return "\n".join(lines)


def cmd_models(_: argparse.Namespace) -> int:
    """List the models, their checkpoints and published accuracies.

    Parameters
    ----------
    _ : argparse.Namespace
        Parsed ``models`` arguments (none).

    Returns
    -------
    int
        Exit status.
    """
    proto = load_protocol()
    print(f"{'model':28s} {'intens':>7s} {'noise':>7s} {'extens':>7s}  checkpoint")
    for key, e in proto["models"].items():
        r = e["results"]
        means = " ".join(f"{r[arm]['mean']:7.3f}" for arm in proto["arms"])
        print(f"{key:28s} {means}  {e['hf_model_id']}@{e['revision'][:12]}")
    return 0


def cmd_fetch(a: argparse.Namespace) -> int:
    """Download a results prefix into a local folder.

    Parameters
    ----------
    a : argparse.Namespace
        Parsed ``fetch`` arguments.

    Returns
    -------
    int
        Exit status.
    """
    proto = load_protocol()
    bucket, region, prefix = proto["bucket"], proto["region"], proto["prefix"]
    got, skipped = public_release.fetch(
        Path(a.out),
        bucket,
        f"{prefix}/",
        "",
        public_release.client(region),
    )
    print(
        f"fetched {got} files from s3://{bucket} to {a.out} ({skipped} already present)"
    )
    return 0


def cmd_check_data(a: argparse.Namespace) -> int:
    """Check a results folder against the recorded digests.

    Parameters
    ----------
    a : argparse.Namespace
        Parsed ``check-data`` arguments.

    Returns
    -------
    int
        Exit status: 1 when any replicate differs.
    """
    problems = check_data(Path(a.data))
    for p in problems[:20]:
        print(f"  {p}")
    print(
        f"FAIL: {len(problems)} problems"
        if problems
        else f"OK: {a.data} matches the published runs"
    )
    return 1 if problems else 0


def cmd_report(a: argparse.Namespace) -> int:
    """Score a results folder next to the published values.

    Parameters
    ----------
    a : argparse.Namespace
        Parsed ``report`` arguments.

    Returns
    -------
    int
        Exit status.
    """
    print(report(Path(a.data)))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point.

    Parameters
    ----------
    argv : Optional[list[str]]
        Arguments; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        Exit status.
    """
    p = argparse.ArgumentParser(
        prog="induction-repro", description=(__doc__ or "").split("\n\n", maxsplit=1)[0]
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models", help="list the models of the ICLR run").set_defaults(
        func=cmd_models
    )
    pf = sub.add_parser("fetch", help="download released results into a local folder")
    pf.add_argument("--out", required=True)
    pf.set_defaults(func=cmd_fetch)
    pd = sub.add_parser(
        "check-data", help="check a results folder against the published runs"
    )
    pd.add_argument("data")
    pd.set_defaults(func=cmd_check_data)
    prep = sub.add_parser(
        "report", help="score a results folder next to the published values"
    )
    prep.add_argument("data")
    prep.set_defaults(func=cmd_report)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
