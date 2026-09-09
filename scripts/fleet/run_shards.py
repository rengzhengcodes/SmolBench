"""Supervise direct ``run_study.py`` shard fleets.

Adopt or relaunch shards with the shared policy; terminate clean-exit boxes
because direct runs have no teardown and would idle about 30 minutes for the watchdog.
Default tags stay outside fleet teardown's scope.
Launch detached (``setsid nohup ... &``) after sourcing ``notebooks/induction/keys.env``
and ``notebooks/ec2-operator.env`` because children inherit this environment and `shard_env` only layers onto it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Dict, Optional

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config() -> ModuleType:
    # `_config` must bootstrap its own path loader.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Share the cached policy module with run_fleet so restart rules cannot drift.
_policy = _config.load_fleet_module("policy")
#: Keep one Shard definition rather than a shadowing local alias.
_shards = _config.load_fleet_module("shards")

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "notebooks" / "induction" / "run_study.py"
PYTHON = REPO / ".venv" / "bin" / "python"
LOG_DIR = REPO / "notebooks" / "induction" / "results" / "fleet_logs"

#: Seconds between passes; policy controls relaunch delays.
POLL_SECONDS = 30


def shard_env(args: argparse.Namespace, index: int) -> Dict[str, str]:
    """Build the complete child environment for shard `index`.

    Preserve the base tag because the driver derives shard tags and state paths.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed shard-launch arguments.
    index : int
        Zero-based shard index.

    Returns
    -------
    Dict[str, str]
        Child-process environment.
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

    Match ``INDUCTION_MODELS`` and ``INDUCTION_SHARD`` in ``/proc/<pid>/environ``;
    first match wins because launch discipline permits at most one per pair.

    Parameters
    ----------
    model : str
        Model identifier.
    shard : Optional[str]
        Shard selector.

    Returns
    -------
    Optional[int]
        Matching PID, if any.
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

    Shards use ``.ec2_state_induction-<model>-s<i>of<n>.json``, mirroring the
    driver's ``_LANE`` suffix, so state stays separate from fleet tags.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed shard-launch arguments.
    index : int
        Zero-based shard index.

    Returns
    -------
    Path
        Repository-anchored shard state path.
    """
    if args.no_shard:
        return REPO / args.state_file
    return REPO / f".ec2_state_induction-{args.model}-s{index}of{args.count}.json"


def terminate_shard_box(shard: _shards.Shard) -> None:
    """Best-effort terminate of a completed `shard`'s instance, via its state file.

    Use the shard's carried file so termination provably targets what it launched,
    not arguments that may have moved on. Unlink it after success so reattach cannot
    latch onto an instance id that no longer exists.

    Parameters
    ----------
    shard : _shards.Shard
        Completed shard.
    """
    path = shard.state_file
    index = shard.index
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


def build_parser() -> argparse.ArgumentParser:
    """Build this script's CLI parser.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="Spec key, e.g. gemma-4-12b.")
    parser.add_argument("--count", type=int, required=True, help="Number of shards.")
    parser.add_argument("--force-rerun", default="", help="INDUCTION_FORCE_RERUN value ('1' or 'a-b'; empty = off).")
    parser.add_argument("--types", required=True, help="EC2_INSTANCE_TYPES for every shard.")
    parser.add_argument("--regions", required=True, help="EC2_REGIONS for every shard.")
    parser.add_argument("--request-timeout", type=int, default=0, help="EC2_REQUEST_TIMEOUT_SECONDS override.")
    parser.add_argument(
        # Use the study-config tag so driver and supervisor cannot drift.
        "--tag", default=_config.STANDALONE_TAG,
        help="Base EC2_EXPERIMENT_TAG (shard suffix is derived by the driver). "
             "Defaults to the committed study config's [fleet].standalone_tag, "
             "which sits deliberately outside the fleet's tag prefix -- see "
             "refuse_fleet_prefix_tag -- so fleet_teardown.py --terminate "
             "cannot reach these shard boxes.",
    )
    parser.add_argument("--no-shard", action="store_true", help="Single unsharded run (requires --state-file; --count must be 1).")
    parser.add_argument("--state-file", default="", help="INDUCTION_STATE_FILE for --no-shard runs.")
    parser.add_argument(
        "--allow-fleet-prefix", action="store_true",
        help="Allow --tag to fall inside the fleet's 'scaling-' tag prefix "
             "anyway. See refuse_fleet_prefix_tag for the blast-radius reason "
             "this is refused by default.",
    )
    # Skip empty shards so they do not consume vCPU quota before exiting;
    # --count still fixes seed-to-shard mapping, and this only skips their launch.
    parser.add_argument(
        "--only-shards", default="",
        help="Comma-separated shard indices to run (default: all). "
             "--count still defines the seed->shard mapping.",
    )
    return parser


def refuse_fleet_prefix_tag(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse a ``--tag`` whose derived per-shard tag falls in the fleet's blast radius.

    Check the derived tag so fleet teardown cannot reach shard boxes. The
    ``f"{args.tag}-"`` form catches ``"scaling"``, one character short of the prefix
    although its derived tag matches, without over-matching ``"scalingful"``.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser for unsafe tags.
    args : argparse.Namespace
        Parsed tag and override flag.

    Raises
    ------
    SystemExit
        Unsafe derived tag without the override.
    """
    if args.allow_fleet_prefix:
        return
    if f"{args.tag}-".startswith(_config.SCALING_TAG_PREFIX):
        parser.error(
            f"--tag {args.tag!r}: shard tags become "
            f"'{args.tag}-<model>-s<i>of<n>', which starts with the fleet's "
            f"{_config.SCALING_TAG_PREFIX!r} prefix -- these shard boxes would "
            "sit inside fleet_teardown.py --terminate's blast radius, so a "
            "routine fleet teardown would terminate them. Pass a --tag outside "
            "that prefix (the default, 'induction-scaling', already is), or "
            "pass --allow-fleet-prefix to launch anyway."
        )


def supervise(shard_list: list) -> int:
    """Supervise `shard_list` until every shard is done or halted; return the exit code.

    Sleep during shard backoff because this supervisor has no other lanes to tick.

    Parameters
    ----------
    shard_list : list
        Shards to supervise.

    Returns
    -------
    int
        ``1`` for halted shards, else ``0``.
    """
    while True:
        for shard in shard_list:
            if shard.status != "running" or shard.alive():
                continue
            rc = shard.returncode()
            if rc == 0:
                shard.status = "done"
                logging.info(f"shard {shard.index}: COMPLETE")
                terminate_shard_box(shard)
                continue

            try:
                tail = shard.log.read_text(errors="replace")[-2000:]
            except OSError:
                tail = ""
            # No instance sweep here; false would classify every exit as reclaim.
            decision = _policy.count_and_decide(shard, tail, True, rc)

            if decision.action == "halt":
                shard.status = "halted"
                logging.error(
                    f"shard {shard.index}: HALTED -- {decision.reason}; "
                    f"see {shard.log}"
                )
                continue

            logging.warning(f"shard {shard.index}: {decision.reason}")
            if decision.delay_seconds:
                # Skip sleep(0): it still costs a scheduling round-trip and reads
                # as though a delay were intended.
                time.sleep(decision.delay_seconds)
            shard.launch()

        if all(s.status in ("done", "halted") for s in shard_list):
            break
        time.sleep(POLL_SECONDS)

    halted = [s.index for s in shard_list if s.status == "halted"]
    logging.info(
        f"run_shards: all shards finished "
        f"({len(shard_list) - len(halted)} done, halted={halted or 'none'})"
    )
    return 1 if halted else 0


def main() -> int:
    """Parse the command line, build and start the shards, then `supervise` them.

    Return ``supervise``'s exit code. Raise ``SystemExit`` for an invalid ``--no-shard``
    combination, an out-of-range ``--only-shards`` index, or a tag inside the fleet's blast radius.
    """
    parser = build_parser()
    args = parser.parse_args()
    if args.no_shard and (args.count != 1 or not args.state_file):
        parser.error("--no-shard requires --count 1 and --state-file")
    # Validate tags before any launch.
    refuse_fleet_prefix_tag(parser, args)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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

    # Snapshot the inherited launch environment once.
    shard_list = []
    for index in selected:
        stem = (args.model if args.no_shard
                else f"{args.model}-s{index}of{args.count}")
        shard_list.append(_shards.Shard(
            index=index,
            selector=None if args.no_shard else f"{index}/{args.count}",
            log=LOG_DIR / f"{stem}.log",
            env=shard_env(args, index),
            state_file=state_file_for(args, index),
            python=PYTHON,
            driver=DRIVER,
            cwd=REPO,
        ))

    # Log here, not in supervise, which never sees args, so the model precedes shard lines.
    logging.info(f"run_shards[{args.model}]: supervising {len(shard_list)} shard(s)")

    for shard in shard_list:
        pid = find_adoptable(args.model, shard.selector)
        if pid is not None:
            shard.adopted_pid = pid
            shard.status = "running"
            logging.info(f"shard {shard.index}: adopted live pid {pid}")
        else:
            shard.launch()
            time.sleep(5)  # stagger cold launches gently

    return supervise(shard_list)


if __name__ == "__main__":
    sys.exit(main())
