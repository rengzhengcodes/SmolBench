"""Babysit direct (supervisor-less) ``run_study.py`` shard fleets.

``scripts/run_fleet.py`` supervises one-model-per-box lanes. But the
homogeneity re-runs of 2026-08-13 launch
``notebooks/induction/run_study.py`` DIRECTLY, one process per
``INDUCTION_SHARD``. A direct process that dies (spot reclaim, a
capacity-exhausted hunt, a crash) stays dead. This script closes that gap
for ONE shard group:

* This script **adopts** already-running shard processes, matched by
  ``INDUCTION_MODELS`` and ``INDUCTION_SHARD`` in ``/proc/<pid>/environ``,
  instead of double-launching them. You can safely start this script while
  a hand-launched fleet is mid-run.
* This script relaunches a dead shard with a 60 s backoff. It reuses the
  exact environment recipe of the hand launches, so a relaunch REATTACHES
  to a still-live box through the state file, or provisions a fresh box
  if the old box is gone.
* This script classifies a shard as HALTED if it dies within
  ``FAST_CRASH_SECONDS`` of launch three times in a row. This is a crash
  loop no relaunch will fix (for example, a SystemExit from a bad
  environment). This script then stops relaunching that shard, and
  reports the halt loudly.
* On a shard's clean completion (exit 0), this script terminates that
  shard's instance through its state file. Direct runs deliberately do no
  teardown of their own (the "fleet-owned" lifecycle contract), so
  without this step, every finished box would idle for about 30 minutes
  until the on-box watchdog fires.
* This script exits once every shard is complete or halted. It returns a
  non-zero exit code if any shard halted.

Credentials and config: this script inherits its environment. Launch it
from a shell that has sourced ``notebooks/induction/keys.env`` and
``notebooks/ec2-operator.env``, exactly like the hand launches. This
script adds per-shard variables to each child process on top of that.

Usage (one invocation per shard group, detached)::

    setsid nohup .venv/bin/python -u scripts/run_shards.py \\
        --model gemma-4-12b --count 3 --force-rerun 1 \\
        --types g7.12xlarge --regions us-east-2,us-west-2,us-east-1 \\
        --request-timeout 10800 \\
        >> notebooks/induction/results/fleet_logs/shards_gemma-4-12b.log 2>&1 &

Pass ``--count 1 --no-shard`` to supervise a single unsharded run (for
example, the deepseek-v4-flash seeds 0-11 re-collection). In that case,
you must pass ``--tag`` and ``--state-file`` explicitly, because there is
no shard suffix to derive them from.
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

REPO = Path(__file__).resolve().parent.parent
DRIVER = REPO / "notebooks" / "induction" / "run_study.py"
PYTHON = REPO / ".venv" / "bin" / "python"
LOG_DIR = REPO / "notebooks" / "induction" / "results" / "fleet_logs"

POLL_SECONDS = 30
RELAUNCH_BACKOFF_SECONDS = 60
#: A shard that dies faster than this after launch counts toward the crash loop.
FAST_CRASH_SECONDS = 300
MAX_FAST_CRASHES = 3
#: A capacity-exhausted hunt prints this marker and exits within about 2-3
#: minutes. This LOOKS like a fast crash, but this script must retry it
#: indefinitely: capacity and quota free up on their own (run_fleet
#: classifies the analogous lane exit as RECLAIM, with unlimited retries).
#: This script checks the marker against the LOG TAIL of the attempt that
#: just died, and retries on a longer backoff, so it does not hammer a dry
#: pool.
CAPACITY_MARKER = "No spot capacity for any"
CAPACITY_BACKOFF_SECONDS = 300


def shard_env(args: argparse.Namespace, index: int) -> Dict[str, str]:
    """Build the complete child environment for shard `index`.

    This function mirrors the hand-launch recipe byte-for-byte: it starts
    from the inherited base environment (keys.env plus operator
    credentials, sourced by the launching shell), and layers per-shard
    variables on top. For sharded groups, the driver itself derives the
    per-shard tag and state-file suffix from ``INDUCTION_SHARD``. So
    passing the same base ``EC2_EXPERIMENT_TAG`` yields the same tags as
    the hand launches. This is what makes adoption and reattach seamless.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI options.
    index : int
        Shard index in ``0..count-1``.

    Returns
    -------
    Dict[str, str]
        Environment for the child process.
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
    """Find the PID of a live ``run_study.py`` process for (`model`, `shard`).

    This function matches through ``/proc/<pid>/environ``, exactly like
    the operating session's manual checks: ``INDUCTION_MODELS`` must equal
    `model`, and ``INDUCTION_SHARD`` must equal `shard` (or be absent when
    `shard` is ``None``). The first match wins. The launch discipline
    guarantees at most one process per (model, shard).

    Parameters
    ----------
    model : str
        Spec key (e.g. ``"gemma-4-12b"``).
    shard : Optional[str]
        ``"i/n"`` selector, or ``None`` for an unsharded run.

    Returns
    -------
    Optional[int]
        A live PID, or ``None``.
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
    """Return the shard's EC2 state file path, anchored at the repo root.

    Sharded runs derive ``.ec2_state_induction-<model>-s<i>of<n>.json``
    (this mirrors ``run_study``'s ``_LANE`` suffix). Unsharded runs use
    ``--state-file`` verbatim.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI options.
    index : int
        Shard index in ``0..count-1``.

    Returns
    -------
    Path
        The state file path.
    """
    if args.no_shard:
        return REPO / args.state_file
    return REPO / f".ec2_state_induction-{args.model}-s{index}of{args.count}.json"


def terminate_shard_box(args: argparse.Namespace, index: int) -> None:
    """Make a best-effort attempt to terminate a completed shard's instance.

    Direct runs do no teardown, by contract. This function reclaims the
    box the moment its shard finishes, instead of waiting about 30
    minutes for the on-box idle watchdog. This function logs and
    swallows any failure; the watchdog is the backstop.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI options.
    index : int
        Shard index in ``0..count-1``.
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
    # WHY: the driver provisions BEFORE it checks has_outstanding(). So a
    # shard whose seeds are already collected still bids for a box, holds
    # it through boot, finds nothing to do, and exits. During the
    # 2026-08-14 ministral reshard, those no-op shards held 4 x 96 vCPU
    # against a 768 vCPU quota, and starved the one shard that had real
    # work for 47 minutes. The --only-shards filter keeps the
    # seed->shard mapping intact (--count still defines it), while it
    # skips launching the empty shards.
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
