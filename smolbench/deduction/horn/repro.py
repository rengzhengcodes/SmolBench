"""Reproduce the Horn analysis from the released results.

    python -m smolbench.deduction.horn.repro fetch --out <results folder>
    python -m smolbench.deduction.horn.repro check-data <results folder>
    python -m smolbench.deduction.horn.repro models
    python -m smolbench.deduction.horn.repro report <rows.jsonl>...

``iclr.json`` records the protocol, published values and calibration choices.
``fetch`` copies the released results into a local folder. ``check-data``
checks its manifest, and ``report`` summarizes result rows next to the
published numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from smolbench import public_release

from .render import ARMS
from .stats import arm_order, contrast, format_p, load_rows, pass_rate

PROTOCOL_PATH = Path(__file__).with_name("iclr.json")
#: Files of one theory that the digest covers, relative to ``<rung>/s<seed>/``.
ARM_FILES = ("prompt.md", "system.md", "meta.json")
DELTAS = (("lem", "both"), ("pad", "both"), ("disc", "both"))


def load_protocol() -> dict:
    """The recorded protocol (``iclr.json``)."""
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def seed_digest(seed_dir: Path, arms: tuple[str, ...] = ARMS) -> str:
    """SHA-256 over ``theory.json`` and every arm's prompt, system prompt and metadata."""
    h = hashlib.sha256()
    names = ["theory.json"] + [f"{arm}/{f}" for arm in arms for f in ARM_FILES]
    for name in names:
        h.update(name.encode() + b"\0")
        h.update((seed_dir / name).read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def check_data(data: Path) -> list[str]:
    """Problems found when checking a results folder against its ``MANIFEST.json``.

    Checks every listed file's SHA-256 and every prompt directory's ``seed_digest``.
    """
    manifest_path = data / "MANIFEST.json"
    if not manifest_path.exists():
        return [f"{manifest_path} not found"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for rel, info in manifest["files"].items():
        path = data / rel
        if not path.exists():
            problems.append(f"{rel}: missing")
            continue
        h = hashlib.sha256()
        with path.open("rb") as fh:
            while chunk := fh.read(1 << 20):
                h.update(chunk)
        if h.hexdigest() != info["sha256"]:
            problems.append(f"{rel}: checksum differs from the MANIFEST")
    for rung, info in manifest.get("prompts", {}).items():
        for seed, digest in info["digests"].items():
            rel = f"horn/prompts/{rung}/s{int(seed):04d}"
            try:
                got = seed_digest(data / rel, tuple(info["arms"]))
            except FileNotFoundError as err:
                problems.append(f"{rel}: {Path(err.filename).name} missing")
                continue
            if got != digest:
                problems.append(f"{rel}: digest differs from the MANIFEST")
    return problems


def report(paths: list[Path], rng_seed: int = 0) -> str:
    """Pass rates and deltas per model and rung, next to the published values."""
    cells, dropped = load_rows(paths)
    models = load_protocol()["models"]
    rng = random.Random(rng_seed)
    scorings = _scorings(paths)
    lines = []
    for (model, rung), arms in sorted(cells.items()):
        published = models.get(model, {}).get("results", {})
        ref = published.get(scorings[0]) if len(scorings) == 1 else None
        seeds = sorted({s for arm in arms.values() for s in arm})
        n = sum(len(v) for arm in arms.values() for v in arm.values())
        lines.append(
            f"== {model} {rung}: {n} cells, {len(seeds)} seeds, scoring {'/'.join(scorings)}"
        )
        head = f"   {'':10s} {'pass %':>8s}"
        lines.append(head + (f" {'published':>10s}" if ref else ""))
        for arm in sorted(arms, key=arm_order):
            row = f"   {arm:10s} {pass_rate(arms[arm]):8.1f}"
            if ref and arm in ref:
                row += f" {ref[arm]:10.1f}"
            lines.append(row)
        for x, y in DELTAS:
            if x in arms and y in arms:
                mean, lo, hi, p, k = contrast(arms[x], arms[y], rng)
                name = f"{x}-{y}"
                row = (
                    f"   {name:10s} {mean:+8.1f}  [{lo:+.1f}, {hi:+.1f}]  "
                    f"{format_p(p, k)}  ({k} seeds)"
                )
                if ref and name in ref:
                    row += f"  published {ref[name]:+.1f}"
                lines.append(row)
    if dropped:
        lines.append(f"dropped rows: {dropped}")
    return "\n".join(lines)


def _scorings(paths: list[Path]) -> list[str]:
    """The scoring modes found in the rows (rows without the field were scored ``iclr``)."""
    found: set[str] = set()
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    found.add(json.loads(line).get("scoring") or "iclr")
                except json.JSONDecodeError:
                    continue
    return sorted(found) or ["iclr"]


def cmd_models(_: argparse.Namespace) -> int:
    """List the models, their chain lengths, backends, and published results."""
    proto = load_protocol()
    print(
        f"{'model':28s} {'m':>3s}  {'backend':8s} "
        f"{'lem':>6s} {'pad':>6s} {'both':>6s}  notes"
    )
    for key, entry in proto["models"].items():
        results = entry["results"]["iclr"]
        print(
            f"{key:28s} {entry['m']:3d}  {entry['backend']:8s} "
            f"{results['lem']:6.1f} {results['pad']:6.1f} {results['both']:6.1f}  "
            f"{entry.get('notes', '')}"
        )
    return 0


def cmd_fetch(a: argparse.Namespace) -> int:
    """Download the released results into a local folder."""
    proto = load_protocol()
    bucket, region, prefix = proto["bucket"], proto["region"], proto["prefix"]
    out = Path(a.out)
    got, skipped = public_release.fetch(
        out, bucket, prefix, prefix, public_release.client(region)
    )
    print(
        f"fetched {got} files from s3://{bucket}/{prefix} to {out} "
        f"({skipped} already present)"
    )
    return 0


def cmd_check_data(a: argparse.Namespace) -> int:
    """Check a results folder against its MANIFEST checksums."""
    problems = check_data(Path(a.data))
    for problem in problems:
        print(f"  {problem}")
    print(
        f"FAIL: {len(problems)} problems"
        if problems
        else f"OK: {a.data} matches its MANIFEST"
    )
    return 1 if problems else 0


def cmd_report(a: argparse.Namespace) -> int:
    """Summarize result rows next to the published values."""
    print(report([Path(path) for path in a.rows]))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        prog="horn-repro", description=(__doc__ or "").split("\n\n", maxsplit=1)[0]
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    pf = sub.add_parser("fetch", help="download the public results")
    pf.add_argument("--out", required=True)
    pf.set_defaults(func=cmd_fetch)
    pd = sub.add_parser(
        "check-data", help="check a results folder against its MANIFEST"
    )
    pd.add_argument("data")
    pd.set_defaults(func=cmd_check_data)
    sub.add_parser("models", help="list the models of the ICLR run").set_defaults(
        func=cmd_models
    )
    prep = sub.add_parser("report", help="summarize rows next to the published values")
    prep.add_argument("rows", nargs="+")
    prep.set_defaults(func=cmd_report)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
