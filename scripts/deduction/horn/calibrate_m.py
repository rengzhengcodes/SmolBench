"""Find, per model, the chain length m at which the lem arm passes about 70%.

Walks a ladder of lem-only calibration rungs (``<calib_root>/calib_m<m>``, seeds
200-229). Starts at ``--start``; while the pass rate is above ``--hi`` it moves to the
next longer chain, while below ``--lo`` to the next shorter one; stops when the rate is
inside [lo, hi] or the ladder ends, and reports the level whose rate is closest to
``--target``. Every level run is kept (``<out_dir>/<model>_m<m>.jsonl``), and a level is
never run twice. Exception rows are retried by rerunning the same command.

usage::

    python scripts/deduction/horn/calibrate_m.py --calib-root <root> --out-dir <dir> \\
        --model zai.glm-4.7-flash --spec-key glm-4.7-flash [--extra-fields '{...}']
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pass_rate(path: Path, model: str) -> tuple[float, int, int, int] | None:
    """(pass rate, n scored, n length, n exceptions) of the model's rows, or None."""
    if not path.exists():
        return None
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("model") == model]
    scored = [r for r in rows if r["verdict"] != "exception"]
    if not scored:
        return None
    ok = sum(r["verdict"] == "success" for r in scored)
    length = sum(r.get("finish_reason") == "length" for r in scored)
    return ok / len(scored), len(scored), length, len(rows) - len(scored)


def run_level(a: argparse.Namespace, m: int) -> tuple[float, int, int, int]:
    """Run (or resume) the lem arm at level ``m`` and return its pass rate tuple."""
    out = Path(a.out_dir) / f"{a.spec_key}_m{m}.jsonl"
    cmd = [
        sys.executable, str(HERE / "bedrock_sweep.py"),
        "--model", a.model, "--spec-key", a.spec_key, "--region", a.region,
        "--rung-dir", str(Path(a.calib_root) / f"calib_m{m}"), "--arms", "lem",
        "--replicates", str(a.replicates), "--max-tokens", str(a.max_tokens),
        "--temperature", str(a.temperature), "--concurrency", str(a.concurrency),
        "--timeout", str(a.timeout), "--out", str(out),
    ]
    if a.extra_fields:
        cmd += ["--extra-fields", a.extra_fields]
    if a.seeds:
        cmd += ["--seeds", a.seeds]
    for _ in range(3):  # rerun picks up exception rows
        subprocess.run(cmd, check=False)
        pr = pass_rate(out, a.model)
        if pr and pr[3] == 0:
            break
    pr = pass_rate(out, a.model)
    if pr is None:
        raise SystemExit(f"{a.spec_key} m={m}: no scored rows")
    return pr


def main(argv: list[str] | None = None) -> int:
    """Walk the ladder and print the chosen level."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--calib-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--spec-key", required=True)
    ap.add_argument("--region", default="us-east-2")
    ap.add_argument("--ladder", default="3,6,12,24,48,96")
    ap.add_argument("--start", type=int, default=12)
    ap.add_argument("--target", type=float, default=0.70)
    ap.add_argument("--lo", type=float, default=0.60)
    ap.add_argument("--hi", type=float, default=0.80)
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--seeds", default=None)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--extra-fields", default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args(argv)
    ladder = [int(x) for x in a.ladder.split(",")]
    i = ladder.index(a.start)
    seen: dict[int, tuple[float, int, int, int]] = {}
    while True:
        m = ladder[i]
        if m not in seen:
            seen[m] = run_level(a, m)
        rate = seen[m][0]
        print(f"[calibrate] {a.spec_key} m={m}: lem {100*rate:.1f}% (n={seen[m][1]}, length {seen[m][2]}, exc {seen[m][3]})", flush=True)
        if rate > a.hi and i + 1 < len(ladder) and ladder[i + 1] not in seen:
            i += 1
        elif rate < a.lo and i > 0 and ladder[i - 1] not in seen:
            i -= 1
        else:
            break
    best = min(seen, key=lambda m: (abs(seen[m][0] - a.target), -m))
    status = "ok"
    if seen[best][0] < a.lo:
        status = "below floor" if best == ladder[0] else "between levels"
    elif seen[best][0] > a.hi:
        status = "near ceiling" if best == ladder[-1] else "between levels"
    result = {
        "spec_key": a.spec_key, "model": a.model, "chosen_m": best, "status": status,
        "levels": {str(m): {"pass": round(seen[m][0], 3), "n": seen[m][1], "length": seen[m][2]} for m in sorted(seen)},
        "extra_fields": json.loads(a.extra_fields) if a.extra_fields else None,
    }
    Path(a.out_dir, f"{a.spec_key}_calibration.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8"
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
