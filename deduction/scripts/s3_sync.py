"""Continuous S3-sync daemon for SmolBench deductive runs.

Designed to run alongside `deduction.src.runner` / `deduction.src.baseline_min` on a spot instance. Every
`--interval` seconds it `aws s3 sync`'s the run directory to the bucket so
that nothing is lost when AWS reclaims the box.

What gets synced:
  - The runner's per-cell JSONL + `<out>.meta.jsonl` (the primary results).
  - vLLM and kimina server stdout/stderr logs.
  - GPU/system metrics (sampled by this daemon itself: see `_sample_metrics`).
  - Anything else under the same parent directory (so the operator can drop
    extra log files there and they'll be picked up).

Key design properties:
  - Idempotent: aws s3 sync is fine to interrupt. The daemon can crash and
    restart with no harm.
  - Cheap: only changed files are uploaded thanks to S3 sync's mtime+size
    comparison. A 100MB JSONL that grew by 10K only re-uploads 10K (well,
    actually the whole file — S3 sync is whole-object — but the cost is
    bounded and uploads are fast).
  - Final-flush: SIGTERM triggers one last sync before exit, so the spot
    handler can `kill -TERM` us and trust the result.

Usage:
    python -m deduction.scripts.s3_sync \\
      --src /opt/dlami/nvme/sb/runs/run_box1 \\
      --dst s3://smolbench-deductive/runs/box1/run_2026-04-28/ \\
      --interval 60
"""
from __future__ import annotations

import argparse
import datetime
import json
import signal
import subprocess
import sys
import time
from pathlib import Path


_stop = False


def _handle_stop(signum, frame):
    global _stop
    _stop = True
    print(f"[s3_sync] received signal {signum}; will flush and exit",
          flush=True)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sync_once(src: Path, dst: str, *, exclude_patterns: list[str]) -> int:
    """One pass: aws s3 sync src/ dst/. Returns rc."""
    cmd = ["aws", "s3", "sync", str(src) + "/", dst]
    for p in exclude_patterns:
        cmd += ["--exclude", p]
    cmd += ["--no-progress", "--only-show-errors"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[s3_sync] FAIL rc={r.returncode}: {r.stderr.strip()[:500]}",
              file=sys.stderr, flush=True)
    return r.returncode


def _sample_metrics(out_dir: Path) -> None:
    """Append one nvidia-smi snapshot + free + uptime line to metrics.jsonl.

    Cheap (~50ms) and bounded — gives us a time-series for post-mortem.
    """
    rec: dict = {"ts": _now_iso()}
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        rec["gpus"] = [
            [x.strip() for x in line.split(",")]
            for line in r.stdout.splitlines() if line.strip()
        ]
    except Exception as e:
        rec["gpu_error"] = str(e)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith(("MemTotal:", "MemAvailable:")):
                    k, v = line.split(":")
                    rec[k.strip()] = v.strip()
    except Exception:
        pass
    try:
        with open("/proc/loadavg") as f:
            rec["loadavg"] = f.read().strip().split()[:3]
    except Exception:
        pass
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "metrics.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path,
                    help="Local run directory to sync (will be created if absent).")
    ap.add_argument("--dst", required=True,
                    help="S3 destination prefix, e.g. s3://bucket/runs/box1/run_X/")
    ap.add_argument("--interval", type=int, default=60,
                    help="Seconds between sync passes.")
    ap.add_argument("--metrics-interval", type=int, default=30,
                    help="Seconds between GPU/system metric snapshots. "
                         "0 disables.")
    ap.add_argument("--exclude", action="append", default=[],
                    help="aws s3 sync --exclude pattern. May be repeated.")
    args = ap.parse_args()

    if not args.dst.startswith("s3://"):
        print(f"--dst must start with s3://: {args.dst}", file=sys.stderr)
        sys.exit(2)
    args.src.mkdir(parents=True, exist_ok=True)

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    print(f"[s3_sync] src={args.src} dst={args.dst} "
          f"interval={args.interval}s metrics_interval={args.metrics_interval}s",
          flush=True)

    last_sync = 0.0
    last_metrics = 0.0
    n_sync = 0
    while not _stop:
        now = time.time()
        if args.metrics_interval > 0 and now - last_metrics >= args.metrics_interval:
            _sample_metrics(args.src)
            last_metrics = now
        if now - last_sync >= args.interval:
            rc = _sync_once(args.src, args.dst, exclude_patterns=args.exclude)
            n_sync += 1
            print(f"[s3_sync] pass #{n_sync} rc={rc} at {_now_iso()}",
                  flush=True)
            last_sync = now
        time.sleep(1)

    # Final flush on SIGTERM/SIGINT
    print(f"[s3_sync] final flush ...", flush=True)
    rc = _sync_once(args.src, args.dst, exclude_patterns=args.exclude)
    print(f"[s3_sync] final flush rc={rc}; exiting", flush=True)


if __name__ == "__main__":
    main()
