"""21-lane EC2 fleet supervisor for the family-ladder scaling study.

Running this script launches ``notebooks/induction/run_study.py`` once per
checkpoint with ``INDUCTION_MODELS`` pinned to one spec key and
``INDUCTION_STATE_FILE`` to a lane-private EC2 state file. Between them, the
modules listed under Layout below own the roster (tiers A-D fix a lane's
instance types, regions and budget), the per-lane environment, the subprocess
lifecycle, the optional deduction phase on the SAME reused box, and the final
S3 spool sync plus shutdown -- this file itself owns none of them.

- Launch order: tier D first (scarcest capacity), then tier A, staggered. The
  FAMILY GATE (``--no-gate`` skips it) holds tiers B/C until all three
  ``supervisor.GATE_MODELS`` tier-A lanes -- one per reasoning-toggle style --
  log a healthy serve, turning a 21-way bet on the digest-pinned
  ``lane_env.FLEET_IMAGE`` into a 3-way bet.
- Restart policy: the VOCABULARY lives in ``scripts/fleet/policy.py``, SHARED
  with ``scripts/fleet/run_shards.py`` so one spot reclaim gets one answer
  whichever supervisor is watching; ``supervisor._apply_restart_policy``
  applies it here. ``policy.classify_exit`` gives a reclaim
  ``policy.MAX_RECLAIM_RELAUNCHES`` BACKED-OFF relaunches and a crash
  ``policy.MAX_CRASH_RELAUNCHES`` immediate ones, then HALTS that lane either
  way; the fleet continues.
- CoT-ON: ``supervisor.reasoning_fraction`` HALTS any lane whose first landed
  replicate falls below ``supervisor.COT_MIN_FRACTION``; non-thinking data is
  indistinguishable later.
- Phases: ``--phase induction`` (default) never shuts a box down; ``deduction``
  may reattach to the SAME instance (same tag and state file) and, on success,
  spools to S3 and shuts down; ``both`` chains them. Only
  ``scripts/fleet/fleet_teardown.py --terminate`` reclaims the boxes an
  induction-only run leaves up.
- COST: an ungated launch provisions up to 21 DISTINCT spot instances at once,
  ``g6e.4xlarge`` up to 8xB200 ``p6-b200.48xlarge``, each billing while up.

Layout
------
This file is the ENTRY POINT only -- argument parsing, the lane selection and
the ``--dry-run`` plan. The work lives in its siblings, each loaded by file
path through ``_config.load_fleet_module`` (see below), so that the tables,
the loop and the command line each have exactly one home:

- ``scripts/fleet/lane_env.py`` -- the roster tables (``LANES``, the per-tier
  instance-type/region/budget/GPU-pin tables) and one lane's environment and
  argv (``lane_env``, ``lane_command``). Bound here as `_lane_env`.
- ``scripts/fleet/supervisor.py`` -- the live loop: pre-flight, staggered
  launch, family gate, monitor ticks, restart policy, CoT-ON check, phase
  advance, S3 spool and shutdown. Bound here as `_supervisor`.
- ``scripts/fleet/policy.py`` -- the reclaim-vs-crash vocabulary, shared with
  ``run_shards.py``; reached through ``supervisor._policy``.
- ``scripts/fleet/_config.py`` -- the study's tag prefix, region list and
  roster, read from the committed ``smolbench/evals/study_config.toml``.

Nothing moved is re-exported here. Use ``_lane_env.LANES``,
``_supervisor.preflight``, and so on: a convenience alias in this file is
exactly the second spelling the split exists to remove.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

# NOTE: no `logging.basicConfig` here. It moved to `lane_env.py`, which must
# call it BEFORE its by-path load of the induction driver (that module logs at
# its own import time, and the first handler installed wins) -- and `lane_env`
# is loaded below, so the root logger is already configured by the time
# `main()` logs anything.

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
# loaded under a private module name by its own callers (this file itself is
# loaded under a private name by `tests/tooling/test_run_fleet.py`), so a
# bare import name would be ambiguous at best and simply absent from
# `sys.path` at worst -- see `_config.py`'s own module docstring for the
# fuller argument. Bootstrapped BY HAND, unlike the two bindings below,
# because `load_fleet_module` is a function ON this module and so cannot load
# it; cached under the shared `_CONFIG_MODULE_NAME` key, so there is one
# `_config` object per process however many fleet modules ask for it.
_config = _load_fleet_config()

# The roster/lane-environment module, then the supervision loop -- in that
# order because `lane_env.py` is the module that runs `load_dotenv` (through
# its by-path load of the induction driver) BEFORE
# `smolbench.evals.providers.ec2` freezes its `EC2_*` constants against the
# environment, and loading it first makes that sequence visible here rather
# than leaving it a side effect of loading `supervisor.py`, which reaches
# `lane_env` at its own module scope anyway. Either way there is ONE module
# object: both lines go through the same cached `load_fleet_module`, so the
# roster and its import-time `_drift_guard` exist once per process, not once
# per consumer.
#
# Bound under these exact private names, and NOT unpacked into module-level
# aliases: every use site below spells `_lane_env.X` / `_supervisor.Y` so that
# a moved symbol has exactly one home. `tests/tooling/test_run_fleet.py`
# reaches both modules through these two attributes, rather than loading its
# own copies, for the same reason.
_lane_env = _config.load_fleet_module("lane_env")
_supervisor = _config.load_fleet_module("supervisor")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="21-lane EC2 fleet supervisor for the family-ladder scaling study."
    )
    parser.add_argument(
        "--phase", choices=("induction", "deduction", "both"), default="induction",
        help="Which subprocess phase(s) each lane runs this invocation (default: induction).",
    )
    parser.add_argument(
        "--lanes", default="",
        help="Comma-separated spec keys to run (default: all 21 lanes in lane_env.LANES).",
    )
    parser.add_argument(
        "--no-gate", action="store_true",
        help="Skip the family gate: launch tiers B/C immediately after tiers D/A.",
    )
    parser.add_argument(
        "--log-dir", default=None,
        help=f"Directory for per-lane log files (default: {_supervisor.LOG_DIR}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the launch plan (tier, command, full environment per lane) "
        "and exit. Launches no subprocess and makes no AWS call. Does NOT run "
        "preflight (tokenizer warm-up + completion-budget derivation) or check "
        "that FLEET_IMAGE resolves -- those steps only run on a live launch. "
        "This proves the wiring is correct, not that the lanes will actually "
        "start.",
    )
    return parser


def _selected_lanes(raw: str) -> dict[str, _lane_env.Lane]:
    """Resolve ``--lanes`` into a ``{key: Lane}`` map, in ``lane_env.LANES`` declaration order.

    Raises ``SystemExit`` if `raw` names a key that is not in ``lane_env.LANES``.
    """
    lanes = _lane_env.LANES
    if not raw.strip():
        return dict(lanes)
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    unknown = [k for k in keys if k not in lanes]
    if unknown:
        raise SystemExit(f"run_fleet: unknown --lanes key(s) {unknown}; choose from {sorted(lanes)}")
    chosen = set(keys)
    return {k: lanes[k] for k in lanes if k in chosen}


#: Printed verbatim under the DRY RUN header, worded for the OPERATOR: one who
#: reads a clean `--dry-run` as "the launch will work" would otherwise meet a
#: tokenizer-fetch failure or a budget-floor `SystemExit` only on the live run,
#: which is what `supervisor.preflight()` exists to surface EARLIER.
_DRY_RUN_NOTICE = (
    "NOTE: this is a WIRING preview only. It did NOT run preflight (per-lane\n"
    "HuggingFace tokenizer warm-up + completion-budget derivation) and did NOT\n"
    "check that the digest-pinned FLEET_IMAGE resolves -- both do real\n"
    "network I/O (HuggingFace, Docker Hub) and only run on the live path\n"
    "(drop --dry-run). A clean plan below means the commands and per-lane\n"
    "environment are correct; it does NOT mean the lanes will actually start --\n"
    "a tokenizer fetch failure or a too-small completion budget can still\n"
    "surface for the first time on the live launch.\n"
)


def _print_dry_run_plan(lanes: dict[str, _lane_env.Lane], phase_name: str) -> None:
    """Print, per lane, its tier, every scheduled phase's command, and full env.

    Prints `_DRY_RUN_NOTICE` under the header: this preview never calls
    ``supervisor.preflight``/``supervisor.fleet_image_digest`` (both do real
    network I/O).
    """
    phases = _supervisor._phase_sequence(phase_name)
    print(f"run_fleet DRY RUN -- phase={phase_name!r}, {len(lanes)} lane(s) selected\n")
    print(_DRY_RUN_NOTICE)
    for key, lane in lanes.items():
        print(f"=== {key} (tier {lane.tier}, budget {lane.budget_hours}h) ===")
        for phase in phases:
            print(f"  [{phase}] command: {' '.join(_lane_env.lane_command(lane, phase))}")
            print(f"  [{phase}] env:")
            for env_key, env_val in sorted(_lane_env.lane_env(lane, phase).items()):
                print(f"        {env_key}={env_val}")
        if "deduction" in phases:
            print(
                f"  [shutdown] command (after a successful deduction exit): "
                f"{' '.join(_lane_env.lane_command(lane, 'shutdown'))}"
            )
        print()


def main(argv: Optional[list[str]] = None) -> int:
    """Parse args, then print the dry-run plan or launch the fleet live.

    Returns
    -------
    int
        ``0`` after a dry run, or once the live fleet is all-terminal --
        individual lanes may still be halted; see the printed summary.
    """
    args = _build_arg_parser().parse_args(argv)
    lanes = _selected_lanes(args.lanes)

    if args.dry_run:
        _print_dry_run_plan(lanes, args.phase)
        return 0

    log_dir = Path(args.log_dir).resolve() if args.log_dir else _supervisor.LOG_DIR

    _supervisor.preflight(list(lanes.values()))
    digest = _supervisor.fleet_image_digest()
    logging.info(
        f"run_fleet: launching against {_lane_env.FLEET_IMAGE} (digest={digest or 'unknown'})."
    )

    _supervisor._run_fleet(
        lanes,
        _supervisor._phase_sequence(args.phase),
        gate=not args.no_gate,
        log_dir=log_dir,
        phase_name=args.phase,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
