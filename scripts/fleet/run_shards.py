"""Babysit direct (supervisor-less) ``run_study.py`` shard fleets.

Some induction runs launch ``run_study.py`` directly, one process per
``INDUCTION_SHARD``, instead of the one-model-per-box lanes ``run_fleet.py``
supervises -- and such a process stays dead once it dies. This script
supervises one shard group: adopts already-running shards (`find_adoptable`)
rather than double-launching them, so it's safe to start mid-run; relaunches
a dead one on the hand-launch recipe, reattaching to a still-live box via its
state file or provisioning a new one; and applies the restart policy shared
with ``run_fleet.py`` (``policy.py``), so one spot reclaim gets one answer
whichever supervisor is watching. On a clean exit it terminates the shard's
instance through its state file, since direct runs do no teardown and the box
would otherwise idle ~30 minutes for the on-box watchdog. Exits non-zero if
any shard halted.

``--tag`` defaults to ``_config.STANDALONE_TAG``, deliberately outside the
fleet's tag prefix (see `refuse_fleet_prefix_tag`) so `fleet_status.py` never
lists, and ``fleet_teardown.py --terminate`` never reaches, these shard
boxes.

Launch detached (``setsid nohup ... &``, log under
``notebooks/induction/results/fleet_logs/``) from a shell that has sourced
``notebooks/induction/keys.env`` and ``notebooks/ec2-operator.env``: children
inherit this process's environment, and `shard_env` only layers per-shard
variables on top of it.
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
    # Bootstrapped by hand: load_module_by_path lives on _config itself,
    # and scripts/fleet isn't a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()

# Everything but `_config` itself loads through the loader `_config`
# provides; `_config` can't load itself that way since the function doesn't
# exist until the module has run.
#
# `_policy` is the same module object `run_fleet.py` reads (load_fleet_module
# caches on a shared sys.modules name): a cap or pattern changed there
# changes for both supervisors at once.
_policy = _config.load_fleet_module("policy")
#: Bound as a module, not a bare `Shard` name, so this file has exactly one
#: definition to point at and no local alias that could shadow a change.
_shards = _config.load_fleet_module("shards")

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "notebooks" / "induction" / "run_study.py"
PYTHON = REPO / ".venv" / "bin" / "python"
LOG_DIR = REPO / "notebooks" / "induction" / "results" / "fleet_logs"

#: Seconds between supervision passes; every relaunch delay itself comes from
#: `_policy.reclaim_backoff_seconds`.
POLL_SECONDS = 30


def shard_env(args: argparse.Namespace, index: int) -> Dict[str, str]:
    """Build the complete child environment for shard `index`.

    Mirrors the hand-launch recipe: inherited base environment plus per-shard
    variables. Passing the same base ``EC2_EXPERIMENT_TAG`` reproduces the
    hand launches' tags -- the driver derives the per-shard tag and
    state-file suffix from ``INDUCTION_SHARD`` -- which is what makes
    adoption and reattach work.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed shard-launch arguments.
    index : int
        Zero-based shard index.

    Returns
    -------
    Dict[str, str]
        Complete child-process environment.
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

    Matches ``INDUCTION_MODELS``/``INDUCTION_SHARD`` in ``/proc/<pid>/environ``.
    First match wins; the launch discipline guarantees at most one per
    (model, shard).

    Parameters
    ----------
    model : str
        Model identifier to match.
    shard : Optional[str]
        Shard selector to match.

    Returns
    -------
    Optional[int]
        PID of the matching live process, or None.
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
    ``--state-file`` verbatim. Deliberately distinct from the fleet's
    ``.ec2_state_scaling_<lane>.json`` and never derived from `args.tag`.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed shard-launch arguments.
    index : int
        Zero-based shard index.

    Returns
    -------
    Path
        Shard EC2 state-file path anchored at the repository root.
    """
    if args.no_shard:
        return REPO / args.state_file
    return REPO / f".ec2_state_induction-{args.model}-s{index}of{args.count}.json"


def terminate_shard_box(shard: _shards.Shard) -> None:
    """Best-effort terminate of a completed `shard`'s instance, via its state file.

    Direct runs do no teardown, so this reclaims the box at once instead of
    waiting ~30 minutes for the on-box idle watchdog, which stays the
    backstop: any failure here is logged and swallowed. Takes the shard
    rather than ``(args, index)`` so `supervise` can run without an argparse
    namespace, and so the file terminated is provably the one this shard was
    launched against, not one re-derived from arguments that may have moved
    on. Unlinks `shard.state_file` after a successful terminate, so a later
    reattach can't latch onto an instance id that no longer exists.

    Parameters
    ----------
    shard : _shards.Shard
        Completed shard whose instance is terminated via its state file.
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

    Separate from `main` so `refuse_fleet_prefix_tag` and tests can exercise
    argument parsing, including the fleet-prefix refusal, without running
    the supervisor loop.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="Spec key, e.g. gemma-4-12b.")
    parser.add_argument("--count", type=int, required=True, help="Number of shards.")
    parser.add_argument("--force-rerun", default="", help="INDUCTION_FORCE_RERUN value ('1' or 'a-b'; empty = off).")
    parser.add_argument("--types", required=True, help="EC2_INSTANCE_TYPES for every shard.")
    parser.add_argument("--regions", required=True, help="EC2_REGIONS for every shard.")
    parser.add_argument("--request-timeout", type=int, default=0, help="EC2_REQUEST_TIMEOUT_SECONDS override.")
    parser.add_argument(
        # Sourced from the study config, not re-typed: the driver already
        # defaults a standalone run's EC2_EXPERIMENT_TAG to the same key, so
        # a literal here could drift and tag a shard box unexpectedly.
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
    # The driver provisions before it checks has_outstanding(), so a shard
    # whose seeds are already collected still bids for a box, holds it
    # through boot, and exits -- starving shards with real work against the
    # account's vCPU quota. --count still defines the seed->shard mapping;
    # this only skips launching the empty shards.
    parser.add_argument(
        "--only-shards", default="",
        help="Comma-separated shard indices to run (default: all). "
             "--count still defines the seed->shard mapping.",
    )
    return parser


def refuse_fleet_prefix_tag(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse a ``--tag`` whose derived per-shard tag falls in the fleet's blast radius.

    `shard_env` passes ``args.tag`` straight through as
    ``EC2_EXPERIMENT_TAG``, and the driver appends ``-<model>-s<i>of<n>`` to
    it per shard, so the string that actually lands on the instance's tag is
    the suffixed form, never the bare ``args.tag``. Checking
    ``f"{args.tag}-"`` rather than ``args.tag`` itself catches a bare tag of
    exactly ``"scaling"`` (the old default: one character short of
    ``"scaling-"``, but its derived tag ``"scaling-<model>-s0of<n>"`` does
    match) without over-matching an unrelated tag like ``"scalingful"``.

    A tag inside `_config.SCALING_TAG_PREFIX` sits inside
    `fleet_status.fleet_rows`'s server-side tag filter and therefore inside
    `fleet_teardown.py --terminate`'s only safety re-check, so a routine
    fleet teardown would terminate these hand-launched shard boxes as though
    they were fleet lane instances.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser that reports an unsafe tag.
    args : argparse.Namespace
        Parsed arguments containing the base tag and override flag.

    Raises
    ------
    SystemExit
        Via `parser.error` (not an ``assert``, which ``python -O`` strips) when that would
        happen and ``args.allow_fleet_prefix`` is false.
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

    One pass per `POLL_SECONDS`: every shard that was ``"running"`` and is no
    longer `alive` is either recorded complete (and its box terminated),
    relaunched, or halted, on `_policy`'s verdict.

    `shard_list` takes a plain list of shards and no argparse namespace
    (their `status`, counters and `proc` are mutated in place), so a caller
    can hand-build shards and drive this loop directly -- what makes the
    restart behaviour testable at all.

    Sleep-driven, unlike ``run_fleet``'s tick-and-deadline supervision: a
    shard group has nothing else to get on with while one shard backs off,
    whereas the fleet's single loop is shared by 21 lanes and must never
    block in one of them. Both take their delay from `_policy`, so only the
    scheduling differs.

    Parameters
    ----------
    shard_list : list
        Shards whose status, counters, and processes are supervised.

    Returns
    -------
    int
        ``1`` if any shard halted, else ``0``.
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
            # instance_present=True unconditionally: that argument exists for
            # run_fleet's periodic describe_instances sweep, which this
            # supervisor has no cheap way to run (EC2 credentials, a call per
            # shard per pass), so the verdict must come from the log tail
            # alone. Passing False would short-circuit classify_exit to
            # "reclaim" for every exit, including a genuine crash.
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
                # Skipped on a crash (delay 0.0): a sleep(0) would still cost
                # a scheduling round-trip and read as though a delay were
                # intended.
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

    Returns `supervise`'s exit code. Raises `SystemExit` (via
    `argparse.ArgumentParser.error`) for an invalid ``--no-shard``
    combination, an out-of-range ``--only-shards`` index, or a ``--tag``
    inside the fleet's blast radius (`refuse_fleet_prefix_tag`).
    """
    parser = build_parser()
    args = parser.parse_args()
    if args.no_shard and (args.count != 1 or not args.state_file):
        parser.error("--no-shard requires --count 1 and --state-file")
    # Nothing may launch -- logging isn't even configured yet -- until the
    # tag is confirmed outside the fleet's blast radius.
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

    # Built once here rather than per relaunch: `shard_env` snapshots this
    # process's own environment (the hand-launch recipe), which can't change
    # under a supervisor that never edits `os.environ`.
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

    # Logged here, not in `supervise` (which never sees `args`), to keep the
    # model in the log stream ahead of the per-shard lines.
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
