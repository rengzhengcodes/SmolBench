"""Babysit direct (supervisor-less) ``run_study.py`` shard fleets.

Some induction runs launch ``notebooks/induction/run_study.py`` DIRECTLY, one
process per ``INDUCTION_SHARD``, instead of the one-model-per-box lanes
``run_fleet.py`` supervises -- and such a process stays dead once it dies. This
script supervises ONE shard group:

- ADOPTS already-running shards (matched by `find_adoptable`) rather than
  double-launching them, so it is safe to start mid-run.
- Relaunches a dead shard on the hand-launch environment recipe, so it
  REATTACHES to a still-live box through its state file, or provisions a new one.
- HALTS a shard that dies within ``FAST_CRASH_SECONDS`` of launch
  ``MAX_FAST_CRASHES`` times in a row; capacity-exhausted hunts
  (``CAPACITY_MARKER``) are exempt and retry indefinitely on a longer backoff.
- On a shard's clean exit, terminates its instance through its state file --
  direct runs do no teardown, so the box would otherwise idle ~30 minutes until
  the on-box watchdog fires.
- Exits once every shard is complete or halted, non-zero if any halted.

Launch it detached (``setsid nohup ... &``, redirecting to a log under
``notebooks/induction/results/fleet_logs/``) from a shell that has sourced
``notebooks/induction/keys.env`` and ``notebooks/ec2-operator.env``: children
inherit this process's environment, with only per-shard variables layered on
top.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "notebooks" / "induction" / "run_study.py"
PYTHON = REPO / ".venv" / "bin" / "python"
LOG_DIR = REPO / "notebooks" / "induction" / "results" / "fleet_logs"

POLL_SECONDS = 30
RELAUNCH_BACKOFF_SECONDS = 60
#: A shard that dies faster than this after launch counts toward the crash loop.
FAST_CRASH_SECONDS = 300
MAX_FAST_CRASHES = 3
#: A capacity-exhausted hunt prints this marker and exits within about 2-3
#: minutes. That LOOKS like a fast crash, but must be retried indefinitely:
#: capacity and quota free up on their own (run_fleet classifies the analogous
#: lane exit as RECLAIM, with unlimited retries). Checked against the LOG TAIL
#: of the attempt that just died, and retried on a longer backoff so it does
#: not hammer a dry pool.
CAPACITY_MARKER = "No spot capacity for any"
CAPACITY_BACKOFF_SECONDS = 300


def shard_env(args: argparse.Namespace, index: int) -> Dict[str, str]:
    """Build the complete child environment for shard `index`.

    Mirrors the hand-launch recipe: the inherited base environment (keys.env
    plus operator credentials) plus per-shard variables. Passing the same base
    ``EC2_EXPERIMENT_TAG`` reproduces the hand launches' tags -- the driver
    derives the per-shard tag and state-file suffix from ``INDUCTION_SHARD`` --
    which is what makes adoption and reattach work.
    """
    env = dict(os.environ)
    env["INDUCTION_MODELS"] = args.model
    env["EC2_EXPERIMENT_TAG"] = args.tag
    env["EC2_INSTANCE_TYPES"] = args.types
    env["EC2_REGIONS"] = args.regions
    if args.request_timeout:
        env["EC2_REQUEST_TIMEOUT_SECONDS"] = str(args.request_timeout)
    if args.force_rerun:
        env["INDUCTION_FORCE_RERUN"] = args.force_rerun
    if args.no_shard:
        if args.state_file:
            env["INDUCTION_STATE_FILE"] = args.state_file
    else:
        env["INDUCTION_SHARD"] = f"{index}/{args.count}"
    return env


def find_adoptable(model: str, shard: Optional[str]) -> Optional[int]:
    """Return the PID of a live ``run_study.py`` process for (`model`, `shard`), or None.

    Matches on ``INDUCTION_MODELS`` and ``INDUCTION_SHARD`` (``"i/n"``, or
    ``None`` for an unsharded run) in ``/proc/<pid>/environ``. First match wins;
    the launch discipline guarantees at most one per (model, shard).
    """
    try:
        pids = subprocess.run(
            ["pgrep", "-f", "notebooks/induction/run_study.py"],
            capture_output=True, text=True, check=False,
        ).stdout.split()
    except OSError:
        return None
    for pid in pids:
        try:
            environ = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
        except OSError:
            continue
        kv = dict(e.decode(errors="replace").split("=", 1) for e in environ if b"=" in e)
        if kv.get("INDUCTION_MODELS") != model:
            continue
        if kv.get("INDUCTION_SHARD") != shard:
            continue
        return int(pid)
    return None


def state_file_for(args: argparse.Namespace, index: int) -> Path:
    """Return shard `index`'s EC2 state file path, anchored at the repo root.

    Sharded runs derive ``.ec2_state_induction-<model>-s<i>of<n>.json``
    (mirroring ``run_study``'s ``_LANE`` suffix); unsharded runs use
    ``--state-file`` verbatim.
    """
    if args.no_shard:
        return REPO / args.state_file
    return REPO / f".ec2_state_induction-{args.model}-s{index}of{args.count}.json"


def terminate_shard_box(args: argparse.Namespace, index: int) -> None:
    """Best-effort terminate of completed shard `index`'s instance, via its state file.

    Direct runs do no teardown, so this reclaims the box at once instead of
    waiting ~30 minutes for the on-box idle watchdog, which stays the backstop:
    any failure here is logged and swallowed.
    """
    path = state_file_for(args, index)
    try:
        state = json.loads(path.read_text())
        import boto3  # deferred: needed only on the success path

        boto3.client("ec2", region_name=state["region"]).terminate_instances(
            InstanceIds=[state["instance_id"]]
        )
        logging.info(
            f"shard {index}: terminated {state['instance_id']} ({state['region']})"
        )
        path.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001 -- watchdog is the backstop
        logging.warning(f"shard {index}: box termination skipped ({exc})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="Spec key, e.g. gemma-4-12b.")
    parser.add_argument("--count", type=int, required=True, help="Number of shards.")
    parser.add_argument("--force-rerun", default="", help="INDUCTION_FORCE_RERUN value ('1' or 'a-b'; empty = off).")
    parser.add_argument("--types", required=True, help="EC2_INSTANCE_TYPES for every shard.")
    parser.add_argument("--regions", required=True, help="EC2_REGIONS for every shard.")
    parser.add_argument("--request-timeout", type=int, default=0, help="EC2_REQUEST_TIMEOUT_SECONDS override.")
    parser.add_argument("--tag", default="scaling", help="Base EC2_EXPERIMENT_TAG (shard suffix is derived by the driver).")
    parser.add_argument("--no-shard", action="store_true", help="Single unsharded run (requires --state-file; --count must be 1).")
    parser.add_argument("--state-file", default="", help="INDUCTION_STATE_FILE for --no-shard runs.")
    # WHY: the driver provisions BEFORE it checks has_outstanding(), so a shard
    # whose seeds are already collected still bids for a box, holds it through
    # boot, finds nothing to do, and exits -- starving the shards with real work
    # against the account's vCPU quota. --count still defines the seed->shard
    # mapping; this only skips launching the empty shards.
    parser.add_argument(
        "--only-shards", default="",
        help="Comma-separated shard indices to run (default: all). "
             "--count still defines the seed->shard mapping.",
    )
    args = parser.parse_args()
    if args.no_shard and (args.count != 1 or not args.state_file):
        parser.error("--no-shard requires --count 1 and --state-file")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    class Shard:
        def __init__(self, index: int):
            self.index = index
            self.selector = None if args.no_shard else f"{index}/{args.count}"
            self.proc: Optional[subprocess.Popen] = None
            self.adopted_pid: Optional[int] = None
            self.launched_at = 0.0
            self.fast_crashes = 0
            self.status = "pending"  # pending|running|done|halted
            stem = (args.model if args.no_shard
                    else f"{args.model}-s{index}of{args.count}")
            self.log = LOG_DIR / f"{stem}.log"

        def alive(self) -> bool:
            if self.proc is not None:
                return self.proc.poll() is None
            if self.adopted_pid is not None:
                return Path(f"/proc/{self.adopted_pid}").exists()
            return False

        def returncode(self) -> Optional[int]:
            if self.proc is not None:
                return self.proc.poll()
            # Adopted processes leave no waitable handle. Infer success
            # from the driver's unconditional completion line instead.
            try:
                tail = self.log.read_text(errors="replace")[-4000:]
            except OSError:
                tail = ""
            return 0 if "INDUCTION STUDY RUN COMPLETE" in tail else 1

        def launch(self):
            self.log.parent.mkdir(parents=True, exist_ok=True)
            with self.log.open("ab") as sink:
                self.proc = subprocess.Popen(
                    [str(PYTHON), "-u", str(DRIVER)],
                    stdout=sink, stderr=subprocess.STDOUT,
                    env=shard_env(args, self.index),
                    cwd=str(REPO), start_new_session=True,
                )
            self.adopted_pid = None
            self.launched_at = time.time()
            self.status = "running"
            logging.info(f"shard {self.index}: launched pid {self.proc.pid}")

    selected = (
        sorted({int(i) for i in args.only_shards.split(",") if i.strip() != ""})
        if args.only_shards else list(range(args.count))
    )
    out_of_range = [i for i in selected if not 0 <= i < args.count]
    if out_of_range:
        parser.error(f"--only-shards {out_of_range} outside 0..{args.count - 1}")
    if args.only_shards:
        logging.info(
            "running %d of %d shard(s): %s (the rest are not launched, so they "
            "cannot provision no-op boxes)", len(selected), args.count, selected,
        )
    shards: List[Shard] = [Shard(i) for i in selected]
    for shard in shards:
        pid = find_adoptable(args.model, shard.selector)
        if pid is not None:
            shard.adopted_pid = pid
            shard.launched_at = time.time()  # true start unknown; use now, conservative
            shard.status = "running"
            logging.info(f"shard {shard.index}: adopted live pid {pid}")
        else:
            shard.launch()
            time.sleep(5)  # stagger cold launches gently

    while True:
        for shard in shards:
            if shard.status != "running" or shard.alive():
                continue
            rc = shard.returncode()
            age = time.time() - shard.launched_at
            if rc == 0:
                shard.status = "done"
                logging.info(f"shard {shard.index}: COMPLETE")
                terminate_shard_box(args, shard.index)
                continue
            try:
                tail = shard.log.read_text(errors="replace")[-2000:]
            except OSError:
                tail = ""
            if CAPACITY_MARKER in tail:
                # Not a crash: the hunt found no capacity. Retry patiently,
                # and never count this toward the crash loop.
                shard.fast_crashes = 0
                logging.info(
                    f"shard {shard.index}: capacity-exhausted hunt; "
                    f"re-hunting in {CAPACITY_BACKOFF_SECONDS}s"
                )
                time.sleep(CAPACITY_BACKOFF_SECONDS)
                shard.launch()
                continue
            if age < FAST_CRASH_SECONDS:
                shard.fast_crashes += 1
            else:
                shard.fast_crashes = 0
            if shard.fast_crashes >= MAX_FAST_CRASHES:
                shard.status = "halted"
                logging.error(
                    f"shard {shard.index}: HALTED -- {shard.fast_crashes} "
                    f"consecutive fast crashes (rc={rc}); see {shard.log}"
                )
                continue
            logging.warning(
                f"shard {shard.index}: exited rc={rc} after {age:.0f}s; "
                f"relaunching in {RELAUNCH_BACKOFF_SECONDS}s"
            )
            time.sleep(RELAUNCH_BACKOFF_SECONDS)
            shard.launch()
        if all(s.status in ("done", "halted") for s in shards):
            break
        time.sleep(POLL_SECONDS)

    halted = [s.index for s in shards if s.status == "halted"]
    logging.info(
        f"run_shards[{args.model}]: all shards finished "
        f"({len(shards) - len(halted)} done, halted={halted or 'none'})"
    )
    return 1 if halted else 0


if __name__ == "__main__":
    sys.exit(main())
