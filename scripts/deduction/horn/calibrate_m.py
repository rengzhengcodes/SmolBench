"""Find, per model, the chain length m at which the lem arm fails 2-3 theories in 10.

A smart search over a ladder of lem-only calibration rungs (``<calib_root>/calib_m<m>``):
start at ``--start`` (a prior taken from the closest calibrated relative), run that level
on ``--seeds`` (default 10 theories, 200-209); while the pass rate is above ``--hi`` move
to the next longer chain, while below ``--lo`` to the next shorter one; stop when the
rate is inside [lo, hi] (7 or 8 passes out of 10 by default), when the target is
bracketed by two adjacent levels, or when the ladder ends. The pick is the level nearest
the target crossing of a logistic fit over the levels run (``calibration_pick``). Every level run is kept
(``<out_dir>/<spec_key>_m<m>.jsonl``); a level is never run twice; exception rows are
re-sent by rerunning. Backends: ``bedrock`` (``bedrock_sweep.py``) or ``openai`` (a
served vLLM endpoint through ``sweep.py``).

usage::

    python scripts/deduction/horn/calibrate_m.py --calib-root <root> --out-dir <dir> \\
        --model zai.glm-4.7-flash --spec-key glm-4.7-flash --start 12 [--extra-fields '{...}']
    python scripts/deduction/horn/calibrate_m.py --backend openai --endpoint http://127.0.0.1:8100/v1 \\
        --api-key <key> --calib-root <root> --out-dir <dir> --model qwen3.5-122b-a10b \\
        --spec-key qwen3.5-122b-a10b --start 64
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from calibration_pick import pick as pick_level  # noqa: E402  pylint: disable=wrong-import-position


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
    rung = str(Path(a.calib_root) / f"calib_m{m}")
    if a.backend == "bedrock":
        cmd = [
            sys.executable, str(HERE / "bedrock_sweep.py"),
            "--model", a.model, "--spec-key", a.spec_key, "--region", a.region,
            "--rung-dir", rung, "--arms", "lem", "--replicates", str(a.replicates),
            "--max-tokens", str(a.max_tokens), "--context-length", str(a.context_length),
            "--temperature", str(a.temperature), "--concurrency", str(a.concurrency),
            "--timeout", str(a.timeout), "--out", str(out),
        ]
        if a.extra_fields:
            cmd += ["--extra-fields", a.extra_fields]
    else:
        cmd = [
            sys.executable, str(HERE / "sweep.py"),
            "--endpoint", a.endpoint, "--api-key", a.api_key, "--model", a.model,
            "--spec-key", a.spec_key, "--rung-dir", rung, "--arms", "lem",
            "--replicates", str(a.replicates), "--max-tokens", str(a.max_tokens),
            "--context-length", str(a.context_length), "--temperature", str(a.temperature),
            "--concurrency", str(a.concurrency), "--timeout", str(a.timeout), "--out", str(out),
        ]
        if a.thinking:
            cmd += ["--thinking", a.thinking]
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


def next_level(ladder: list[int], seen: dict[int, float], m: int, lo: float, hi: float) -> int | None:
    """The next level to run after ``m`` (rate ``seen[m]``), or None when the search is done:
    inside [lo, hi], bracketed by an adjacent level on the other side of the band, or at
    the end of the ladder."""
    i = ladder.index(m)
    rate = seen[m]
    if lo <= rate <= hi:
        return None
    if rate > hi:
        if i + 1 >= len(ladder):
            return None
        nxt = ladder[i + 1]
        return None if nxt in seen else nxt  # already run: bracketed
    if i == 0:
        return None
    prv = ladder[i - 1]
    return None if prv in seen else prv


def main(argv: list[str] | None = None) -> int:
    """Walk the ladder and print the chosen level."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--backend", choices=["bedrock", "openai"], default="bedrock")
    ap.add_argument("--endpoint", default=None, help="openai backend: served base URL")
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--thinking", default=None, help="openai backend: auto|on|off")
    ap.add_argument("--calib-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--spec-key", required=True)
    ap.add_argument("--region", default="us-east-2")
    ap.add_argument("--ladder", default="1,2,3,4,6,8,10,12,16,20,24,32,48,64,96,192")
    ap.add_argument("--start", type=int, default=12, help="prior: the closest relative's pick")
    ap.add_argument("--target", type=float, default=0.75, help="7-8 passes in 10: 2-3 failures")
    ap.add_argument("--lo", type=float, default=0.65)
    ap.add_argument("--hi", type=float, default=0.85)
    ap.add_argument("--replicates", type=int, default=1)
    ap.add_argument("--seeds", default="200-209", help="theories per level (10 by default)")
    ap.add_argument("--max-tokens", type=int, default=131072)
    ap.add_argument("--context-length", type=int, default=131072)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--extra-fields", default=None)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument(
        "--fan-out",
        action="store_true",
        help="run the prior and its two neighbours in parallel in the first round",
    )
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args(argv)
    if a.backend == "openai" and not a.endpoint:
        raise SystemExit("--backend openai needs --endpoint")
    ladder = [int(x) for x in a.ladder.split(",")]
    if a.start not in ladder:
        raise SystemExit(f"--start {a.start} is not on the ladder {ladder}")
    seen: dict[int, tuple[float, int, int, int]] = {}
    if a.fan_out:
        # First round: the prior and its two neighbours at once (a served model with
        # several replicas has the capacity; this usually ends the search in one round).
        i = ladder.index(a.start)
        first = [ladder[j] for j in (i - 1, i, i + 1) if 0 <= j < len(ladder)]
        with ThreadPoolExecutor(len(first)) as pool:
            for lvl, res in zip(first, pool.map(lambda lv: run_level(a, lv), first)):
                seen[lvl] = res
                print(f"[calibrate] {a.spec_key} m={lvl}: lem {100*res[0]:.1f}% (n={res[1]}, length {res[2]}, exc {res[3]})", flush=True)
    m: int | None = a.start
    while m is not None:
        if m not in seen:
            seen[m] = run_level(a, m)
        rate = seen[m][0]
        print(f"[calibrate] {a.spec_key} m={m}: lem {100*rate:.1f}% (n={seen[m][1]}, length {seen[m][2]}, exc {seen[m][3]})", flush=True)
        m = next_level(ladder, {k: v[0] for k, v in seen.items()}, m, a.lo, a.hi)
    levels = {k: (round(v[0] * v[1]), v[1], v[2]) for k, v in seen.items()}
    res = pick_level(levels, a.target, min_cells=min(v[1] for v in seen.values()))
    result = {
        "spec_key": a.spec_key, "model": a.model, "chosen_m": res.get("chosen_m"),
        "fitted_m70": res.get("fitted_m70"), "status": res["status"],
        "levels": {str(k): {"pass": round(v[0], 3), "n": v[1], "length": v[2]} for k, v in sorted(seen.items())},
        "start": a.start, "seeds": a.seeds,
        "extra_fields": json.loads(a.extra_fields) if a.extra_fields else None,
    }
    Path(a.out_dir, f"{a.spec_key}_calibration.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8"
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
