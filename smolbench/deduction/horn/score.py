"""Score ``answer.s<i>.md`` files under a rendered tree and summarize per arm.

    python -m smolbench.deduction.horn.score <root> [--json out.jsonl]

Prints pass@1 (mean over samples), the verdict mix and, for ``both``, the
route split among successes.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from .checker import verify
from .render import Rendered
from .theory import Theory

_ANS_RE = re.compile(r"^answer\.s(\d+)\.md$")


def score_tree(root: Path) -> list[dict]:
    """One row per answer file."""
    rows: list[dict] = []
    for sd in sorted(root.glob("s[0-9]*")):
        tj = sd / "theory.json"
        if not tj.exists():
            continue
        theory = Theory.from_json(tj.read_text(encoding="utf-8"))
        for ad in sorted(p for p in sd.iterdir() if p.is_dir()):
            mj = ad / "meta.json"
            if not mj.exists():
                continue
            r = Rendered.from_meta(json.loads(mj.read_text(encoding="utf-8")))
            for af in sorted(ad.iterdir()):
                mt = _ANS_RE.match(af.name)
                if not mt:
                    continue
                v = verify(theory, r, af.read_text(encoding="utf-8"))
                rows.append(
                    {
                        "seed": theory.seed,
                        "arm": r.arm,
                        "sample": int(mt.group(1)),
                        "n_tokens": r.n_tokens,
                        **asdict(v),
                    }
                )
    return rows


def summarize(rows: list[dict]) -> str:
    """Per-arm table."""
    by = collections.defaultdict(list)
    for r in rows:
        by[r["arm"]].append(r)
    out = [f"{'arm':8s} {'n':>4s} {'pass':>6s}  verdicts / routes"]
    for arm, rs in sorted(by.items()):
        n = len(rs)
        ok = sum(r["verdict"] == "success" for r in rs)
        vc = collections.Counter(r["verdict"] for r in rs)
        routes = collections.Counter(
            r["route"] for r in rs if r["verdict"] == "success"
        )
        extra = f"  routes {dict(routes)}" if arm == "both" else ""
        out.append(f"{arm:8s} {n:4d} {100*ok/n:5.1f}%  {dict(vc)}{extra}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    p = argparse.ArgumentParser(prog="horn-score")
    p.add_argument("root")
    p.add_argument("--json", default=None, help="write one row per answer as JSONL")
    a = p.parse_args(argv)
    rows = score_tree(Path(a.root))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(summarize(rows))
    fails = [r for r in rows if r["verdict"] != "success"]
    for r in fails[:20]:
        print(
            f"  s{r['seed']:04d} {r['arm']:7s} {r['verdict']:13s} {r['reason'][:100]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
