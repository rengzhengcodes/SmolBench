"""Babysit direct (supervisor-less) ``run_study.py`` shard fleets.

Some induction runs launch ``notebooks/induction/run_study.py`` DIRECTLY, one
process per ``INDUCTION_SHARD``, instead of the one-model-per-box lanes
``run_fleet.py`` supervises -- and such a process stays dead once it dies. This
script supervises ONE shard group:

- ADOPTS already-running shards (matched by `find_adoptable`) rather than
  double-launching them, so it is safe to start mid-run.
- Relaunches a dead shard on the hand-launch environment recipe, so it
  REATTACHES to a still-live box through its state file, or provisions a new one.
- RESTARTS or HALTS a dead shard on the SHARED restart policy,
  ``scripts/fleet/policy.py``, which ``run_fleet.py`` reads too -- so one spot
  reclaim gets one answer whichever supervisor is watching. ``classify_exit``
  decides reclaim-vs-crash from the log tail; a crash gets
  ``MAX_CRASH_RELAUNCHES`` immediate relaunches, a reclaim
  ``MAX_RECLAIM_RELAUNCHES`` relaunches on an exponential, capped backoff, then
  the shard HALTS either way. This script used to answer the same question with
  a private vocabulary, and both halves of it are gone:

  * the ``CAPACITY_MARKER`` substring (``"No spot capacity for any"``) is
    subsumed by the shared ``RECLAIM_PATTERNS``' ``spot capacity`` pattern --
    the producing line is ``providers/ec2.py``'s "No spot capacity for any
    (instance type, region) combination:" -- alongside seven other reclaim
    spellings this script never matched at all, and its flat 300s retry was
    UNBOUNDED, so a permanently dry pool was re-hunted for the whole run.
  * the consecutive-fast-crash detector (``FAST_CRASH_SECONDS`` /
    ``MAX_FAST_CRASHES``) has no counterpart in the shared policy, which
    counts relaunches rather than timing them. Its "consecutive" reset is
    precisely what let a SLOW crash loop run forever: one crash slower than
    the threshold zeroed the counter, so a shard that failed every 6 minutes
    never reached the halt.

- On a shard's clean exit, terminates its instance through its state file --
  direct runs do no teardown, so the box would otherwise idle ~30 minutes until
  the on-box watchdog fires.
- Exits once every shard is complete or halted, non-zero if any halted.

Tag namespace: ``--tag`` defaults to the committed study config's
``[fleet].standalone_tag``, read here as ``_config.STANDALONE_TAG`` -- the
same default ``notebooks/induction/run_study.py`` applies to a standalone
run, so the two cannot spell it differently. That config places it
deliberately OUTSIDE the fleet's tag prefix (see `refuse_fleet_prefix_tag`),
so `fleet_status.py`'s server-side tag filter never lists these shard boxes
and ``fleet_teardown.py --terminate`` can never reach them. A ``--tag`` that
would land inside that prefix once the driver's per-shard suffix is appended
is refused unless ``--allow-fleet-prefix`` is passed.

Launch it detached (``setsid nohup ... &``, redirecting to a log under
``notebooks/induction/results/fleet_logs/``) from a shell that has sourced
``notebooks/induction/keys.env`` and ``notebooks/ec2-operator.env``: children
inherit this process's environment, with only per-shard variables layered on
top.
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
from typing import Dict, Optional

_CONFIG_MODULE_NAME = "smolbench_fleet_config"


def _load_fleet_config():
    """Load ``scripts/fleet/_config.py`` by file path (see its docstring)."""
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        path = Path(__file__).resolve().parent / "_config.py"
        spec = importlib.util.spec_from_file_location(_CONFIG_MODULE_NAME, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[_CONFIG_MODULE_NAME] = module
        spec.loader.exec_module(module)
    return module


# By file path, not a bare `import _config`: `scripts/fleet` has no
# `__init__.py` (it is not a package), and every module in it is already
# loaded under a private module name by its own callers (see `_config.py`'s
# module docstring for the full list), so a bare import name is ambiguous or
# absent from `sys.path`.
_config = _load_fleet_config()

# Everything OTHER than `_config` itself now loads through the one loader
# `_config` provides, rather than through another copy of the bootstrap above:
# `_config` cannot load itself that way (the function does not exist until the
# module has run), but nothing else has that problem.
#
# `_policy` is the restart vocabulary `run_fleet.py` reads too -- and, because
# `load_fleet_module` caches on a shared `sys.modules` name, literally the same
# module object when both run in one process. That shared identity is the point:
# a cap or a pattern changed there changes for both supervisors at once.
_policy = _config.load_fleet_module("policy")
#: `shards.Shard` lives in its own module so it can be constructed -- and the
#: supervision loop driven -- without an argparse namespace. Bound as a module,
#: not as a bare `Shard` name, so this file has exactly one definition of that
#: class to point at and no local alias that could shadow a future change.
_shards = _config.load_fleet_module("shards")

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "notebooks" / "induction" / "run_study.py"
PYTHON = REPO / ".venv" / "bin" / "python"
LOG_DIR = REPO / "notebooks" / "induction" / "results" / "fleet_logs"

#: Seconds between supervision passes. Only the pass CADENCE lives here; every
#: relaunch delay comes from `_policy.reclaim_backoff_seconds`.
POLL_SECONDS = 30


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

    Why not the fleet scheme
    ------------------------
    This deliberately does NOT match `fleet_status`/`fleet_teardown`'s
    ``.ec2_state_scaling_<lane>.json`` naming. When a shard tag landed inside
    the fleet's blast radius (the bug `refuse_fleet_prefix_tag` now refuses),
    the fix is that refusal, not renaming these files INTO the fleet's
    scheme, for three reasons:

    1. `terminate_shard_box` already unlinks its own state file on the
       success path -- this script owns that file's whole lifecycle, so
       there is no handoff to `fleet_teardown.py` to align the name with.
       (Still true now that `terminate_shard_box` takes a `shards.Shard`
       rather than ``(args, index)``: the path it unlinks is the one THIS
       function produced, carried on the shard as ``state_file``.)
    2. `fleet_teardown.delete_state_files` only ever sees rows produced by
       `fleet_status.fleet_rows`, which filters server-side on the
       ``scaling-*`` tag prefix. With a ``--tag`` outside that prefix (the
       default, ``"induction-scaling"``), a shard box is never in those
       rows, so teardown never needs -- and must never be handed -- a state
       file matching its glob.
    3. Renaming shard state files INTO ``.ec2_state_scaling_*`` would put
       them in `fleet_teardown`'s deletion glob, risking a collision with
       (deletion of, or deletion alongside) a real fleet lane's file.

    Note that this function never reads `args.tag`: the ``induction-``
    prefix here is fixed regardless of what ``--tag`` is (default or
    otherwise), so it only coincidentally echoes the word in the new default
    tag ``"induction-scaling"`` -- the two are not derived from each other.
    """
    if args.no_shard:
        return REPO / args.state_file
    return REPO / f".ec2_state_induction-{args.model}-s{index}of{args.count}.json"


def terminate_shard_box(shard: _shards.Shard) -> None:
    """Best-effort terminate of a completed `shard`'s instance, via its state file.

    Direct runs do no teardown, so this reclaims the box at once instead of
    waiting ~30 minutes for the on-box idle watchdog, which stays the backstop:
    any failure here is logged and swallowed.

    Parameters
    ----------
    shard : shards.Shard
        The finished shard. Reads ``shard.state_file`` -- the path
        `state_file_for` produced when `main` built it -- and ``shard.index``,
        for the log line. Taking the shard rather than ``(args, index)`` is
        what lets `supervise` run without an argparse namespace; it also means
        the file terminated is provably the one this shard was launched
        against, not one re-derived from arguments that may have moved on.

    Notes
    -----
    Unlinks ``shard.state_file`` after a successful terminate, so a later
    reattach cannot latch onto an instance id that no longer exists.
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

    Extracted out of `main` (which now just calls this and `parse_args`) so
    `refuse_fleet_prefix_tag` and tests can exercise argument parsing --
    including the fleet-prefix refusal -- without running the supervisor
    loop.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="Spec key, e.g. gemma-4-12b.")
    parser.add_argument("--count", type=int, required=True, help="Number of shards.")
    parser.add_argument("--force-rerun", default="", help="INDUCTION_FORCE_RERUN value ('1' or 'a-b'; empty = off).")
    parser.add_argument("--types", required=True, help="EC2_INSTANCE_TYPES for every shard.")
    parser.add_argument("--regions", required=True, help="EC2_REGIONS for every shard.")
    parser.add_argument("--request-timeout", type=int, default=0, help="EC2_REQUEST_TIMEOUT_SECONDS override.")
    parser.add_argument(
        # Sourced from the committed study config rather than re-typed: the
        # driver already defaults a standalone run's EC2_EXPERIMENT_TAG to the
        # same key, so a literal here could drift and put a shard box under a
        # tag no other tool expects.
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
    return parser


def refuse_fleet_prefix_tag(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse a ``--tag`` whose DERIVED per-shard tag falls in the fleet's blast radius.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Used only to call `parser.error`, argparse's own gate: it prints a
        usage message to stderr and raises ``SystemExit(2)``. A raise, not an
        ``assert`` -- an ``assert`` is stripped entirely under ``python -O``.
    args : argparse.Namespace
        Parsed arguments; reads ``args.tag`` and ``args.allow_fleet_prefix``.

    Raises
    ------
    SystemExit
        Via `parser.error`, when ``args.tag`` would land inside
        `_config.SCALING_TAG_PREFIX` once the driver's per-shard suffix is
        appended, and ``args.allow_fleet_prefix`` is ``False``.

    Notes
    -----
    `shard_env` passes ``args.tag`` straight through as
    ``EC2_EXPERIMENT_TAG``, and ``notebooks/induction/run_study.py`` appends
    ``-<model>-s<i>of<n>`` to it per shard (its ``_LANE`` derivation) -- so
    the string that actually lands on the instance's ``smolbench:experiment``
    tag is the SUFFIXED form, never the bare ``args.tag``. That is why this
    checks ``f"{args.tag}-"`` rather than ``args.tag`` itself: a bare tag of
    exactly ``"scaling"`` (the OLD default) does not literally start with
    ``"scaling-"`` -- it is one character short -- yet its derived per-shard
    tag, ``"scaling-<model>-s0of<n>"``, does. Appending one more ``"-"``
    before the prefix check catches that exact-match case too, without
    over-matching an unrelated tag like ``"scalingful"`` (whose derived form,
    ``"scalingful-<model>-s0of<n>"``, never starts with ``"scaling-"``
    either).

    A tag inside `_config.SCALING_TAG_PREFIX` sits inside
    `fleet_status.fleet_rows`'s server-side tag filter, and therefore inside
    `fleet_teardown.py --terminate`'s only safety re-check -- so a routine
    fleet teardown would terminate these hand-launched shard boxes as though
    they were fleet lane instances. ``"induction-scaling"``, the new
    default, is spelled outside that prefix on purpose (see this module's
    docstring).
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

    Parameters
    ----------
    shard_list : list of shards.Shard
        The shards to watch, already launched or adopted by the caller. Their
        `status`, counters and `proc` are mutated in place. Takes a plain list
        of shards and no argparse namespace, so a caller can hand-build shards
        and drive this loop directly -- which is what makes the restart
        behaviour testable at all.

    Returns
    -------
    int
        ``1`` if any shard halted, else ``0`` -- this process's exit code.

    Raises
    ------
    ValueError
        Propagated from `_policy.decide_relaunch` if the verdict is neither
        ``"reclaim"`` nor ``"crash"``, which would mean the classifier and this
        caller had drifted apart.

    Notes
    -----
    SLEEP-driven, unlike ``run_fleet._apply_restart_policy``, which records a
    deadline and re-checks it on a later tick. Both take their delay from
    `_policy`, so only the SCHEDULING differs: a shard group is one model's
    work and this loop has nothing else to get on with while a shard backs
    off, whereas the fleet's single loop is shared by 21 lanes and must never
    block in one of them.

    The closing summary names no model: this function is handed shards, not
    ``args``. `main` logs the model once, before calling it, so the model is
    still in the log stream that precedes this line.
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
            # `instance_present=True`, unconditionally and on purpose. That
            # argument exists for `run_fleet`, which runs a periodic
            # `describe_instances` sweep and can say "the box is gone, so this
            # was a reclaim". A shard supervisor runs no such sweep and has no
            # cheap way to: it would need EC2 credentials and a call per shard
            # per pass. So the verdict must come from the log tail alone, and
            # asserting presence is what makes the tail the only evidence.
            # Passing ``False`` would short-circuit `classify_exit` to
            # "reclaim" for EVERY exit -- including a genuine crash, which
            # would then get `MAX_RECLAIM_RELAUNCHES` backed-off relaunches
            # instead of `MAX_CRASH_RELAUNCHES` immediate ones, and would never
            # be reported as the crash it is.
            verdict = _policy.classify_exit(tail, True)

            # Increment first, then ask: the policy's `attempt` is defined as
            # the POST-increment count, so the first relaunch is attempt 1 and
            # the cap is exceeded at MAX + 1.
            if verdict == "reclaim":
                shard.reclaim_relaunches += 1
                attempt = shard.reclaim_relaunches
            else:
                shard.crash_relaunches += 1
                attempt = shard.crash_relaunches
            decision = _policy.decide_relaunch(verdict, attempt=attempt, rc=rc)

            if decision.action == "halt":
                shard.status = "halted"
                logging.error(
                    f"shard {shard.index}: HALTED -- {decision.reason}; "
                    f"see {shard.log}"
                )
                continue

            logging.warning(f"shard {shard.index}: {decision.reason}")
            if decision.delay_seconds:
                # Skipped entirely on a crash, whose delay is 0.0: sleeping
                # zero seconds would still hand the interpreter a scheduling
                # round-trip for no reason, and reads as though a delay were
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

    Returns
    -------
    int
        `supervise`'s exit code: ``1`` if any shard halted, else ``0``.

    Raises
    ------
    SystemExit
        Via `argparse.ArgumentParser.error`, for an invalid ``--no-shard``
        combination, an out-of-range ``--only-shards`` index, or a ``--tag``
        inside the fleet's blast radius (`refuse_fleet_prefix_tag`).

    Notes
    -----
    Deliberately thin: argument parsing, the derivations that turn ``args``
    into `shards.Shard` constructor arguments, the adoption pass, and one call
    into `supervise`. Everything it used to hold inline -- the `shards.Shard`
    class and the whole supervision loop -- now lives where it can be built and
    driven without a command line.
    """
    parser = build_parser()
    args = parser.parse_args()
    if args.no_shard and (args.count != 1 or not args.state_file):
        parser.error("--no-shard requires --count 1 and --state-file")
    # Nothing may be launched -- not even logging is configured yet -- until
    # the tag is confirmed outside the fleet's blast radius.
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

    # The derivations that used to live inside the nested Shard class, done
    # ONCE here instead of on every launch. `shard_env` in particular snapshots
    # this process's own environment, which is exactly the hand-launch recipe
    # the shards must reproduce and which cannot change under a supervisor that
    # never edits `os.environ`; building it per relaunch only re-derived the
    # same dict.
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

    # Logged here, not in `supervise`, which is handed shards and never sees
    # `args`: it keeps the model in the log stream ahead of the per-shard lines
    # and the closing summary.
    logging.info(f"run_shards[{args.model}]: supervising {len(shard_list)} shard(s)")

    for shard in shard_list:
        pid = find_adoptable(args.model, shard.selector)
        if pid is not None:
            shard.adopted_pid = pid
            shard.launched_at = time.time()  # true start unknown; use now, conservative
            shard.status = "running"
            logging.info(f"shard {shard.index}: adopted live pid {pid}")
        else:
            shard.launch()
            time.sleep(5)  # stagger cold launches gently

    return supervise(shard_list)


if __name__ == "__main__":
    sys.exit(main())
