"""Spot-interruption watchdog for SmolBench deductive runs.

AWS publishes a 2-minute warning before reclaiming a spot instance via the
instance metadata service:
    http://169.254.169.254/latest/meta-data/spot/instance-action

This daemon polls IMDS every `--poll-interval` seconds. On detection of an
interruption notice, it:
  1. Logs the event (timestamp, action, reclaim time) to a JSONL.
  2. Sends SIGTERM to the runner pidfile (graceful drain).
  3. Sends SIGTERM to the s3-sync pidfile (forces final flush).
  4. Waits up to `--drain-timeout` seconds for them to exit.
  5. Runs one extra `aws s3 sync` itself as belt-and-suspenders.

It does NOT try to keep working past the warning — the goal is to leave a
clean, fully-uploaded run directory when the instance is reclaimed.

Usage:
    python -m deduction.scripts.spot_handler \\
      --runner-pidfile /tmp/runner.pid \\
      --sync-pidfile /tmp/s3_sync.pid \\
      --src /opt/dlami/nvme/sb/runs/run_box1 \\
      --dst s3://smolbench-deductive/runs/box1/run_X/ \\
      --event-log /opt/dlami/nvme/sb/runs/run_box1/spot_events.jsonl
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


IMDS_TOKEN_URL = "http://169.254.169.254/latest/api/token"
IMDS_BASE = "http://169.254.169.254/latest/meta-data"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _imds_token() -> Optional[str]:
    try:
        req = urllib.request.Request(
            IMDS_TOKEN_URL,
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "300"},
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.read().decode()
    except Exception:
        return None


def _imds_get(path: str, token: Optional[str]) -> tuple[Optional[int], Optional[str]]:
    """Return (status_code, body). Body is None on transport error."""
    try:
        headers = {"X-aws-ec2-metadata-token": token} if token else {}
        req = urllib.request.Request(f"{IMDS_BASE}/{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return None, None


def _read_pid(pidfile: Path) -> Optional[int]:
    try:
        return int(pidfile.read_text().strip())
    except Exception:
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _term(pidfile: Path, label: str, log) -> None:
    pid = _read_pid(pidfile)
    if pid is None:
        log(f"[spot] no pid in {pidfile} ({label}); skipping signal")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        log(f"[spot] sent SIGTERM to {label} pid={pid}")
    except ProcessLookupError:
        log(f"[spot] {label} pid={pid} already gone")
    except Exception as e:
        log(f"[spot] failed to signal {label} pid={pid}: {e}")


def _wait(pids: list[int], timeout: float, log) -> None:
    """Wait until all pids exit or timeout. Polls every 0.5s."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        alive = [p for p in pids if _alive(p)]
        if not alive:
            log(f"[spot] all child pids exited cleanly")
            return
        time.sleep(0.5)
    still = [p for p in pids if _alive(p)]
    if still:
        log(f"[spot] timeout: pids still alive after {timeout:.0f}s: {still}")


def _final_sync(src: Path, dst: str, log) -> int:
    cmd = ["aws", "s3", "sync", str(src) + "/", dst,
           "--no-progress", "--only-show-errors"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log(f"[spot] final aws s3 sync rc={r.returncode}; stderr={r.stderr.strip()[:300]}")
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner-pidfile", type=Path, required=True)
    ap.add_argument("--sync-pidfile", type=Path, required=True)
    ap.add_argument("--src", type=Path, required=True,
                    help="Run directory (for the belt-and-suspenders sync).")
    ap.add_argument("--dst", required=True,
                    help="S3 destination, e.g. s3://bucket/runs/box1/run_X/")
    ap.add_argument("--event-log", type=Path, required=True,
                    help="JSONL file to append spot events to.")
    ap.add_argument("--poll-interval", type=float, default=5.0)
    ap.add_argument("--drain-timeout", type=float, default=90.0,
                    help="Max seconds to wait for runner+sync to exit after "
                         "SIGTERM. AWS gives 120s total — leave 30s headroom.")
    args = ap.parse_args()

    args.event_log.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str, **extra) -> None:
        print(msg, flush=True)
        rec = {"ts": _now_iso(), "msg": msg, **extra}
        with args.event_log.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    log(f"[spot] watchdog starting; poll={args.poll_interval}s "
        f"drain_timeout={args.drain_timeout}s")
    log(f"[spot] runner_pidfile={args.runner_pidfile} "
        f"sync_pidfile={args.sync_pidfile}")

    fired = False
    while not fired:
        token = _imds_token()
        # spot/instance-action returns 200 with JSON body when an action is
        # scheduled; 404 otherwise.
        status, body = _imds_get("spot/instance-action", token)
        if status == 200 and body:
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"raw": body}
            log(f"[spot] INSTANCE ACTION DETECTED",
                imds_status=status, payload=payload)
            fired = True
            break
        # Backwards-compat fallback for the older termination-time endpoint:
        status2, body2 = _imds_get("spot/termination-time", token)
        if status2 == 200 and body2:
            log(f"[spot] termination-time present",
                imds_status=status2, body=body2)
            fired = True
            break
        time.sleep(args.poll_interval)

    runner_pid = _read_pid(args.runner_pidfile)
    sync_pid = _read_pid(args.sync_pidfile)

    _term(args.runner_pidfile, "runner", log)
    _term(args.sync_pidfile, "s3_sync", log)

    pids_to_watch = [p for p in (runner_pid, sync_pid) if p is not None]
    _wait(pids_to_watch, timeout=args.drain_timeout, log=log)

    rc = _final_sync(args.src, args.dst, log)
    log(f"[spot] watchdog exiting rc={rc}")
    sys.exit(0)


if __name__ == "__main__":
    main()
