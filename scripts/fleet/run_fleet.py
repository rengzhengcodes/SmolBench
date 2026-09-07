"""21-lane EC2 fleet supervisor for the family-ladder scaling study.

Launches ``notebooks/induction/run_study.py`` once per checkpoint, pinning
``INDUCTION_MODELS`` and a lane-private EC2 state file. This file is the
entry point only -- argument parsing, lane selection, ``--dry-run``; the
roster, per-lane environment, live loop, restart policy and S3 spool/shutdown
live in ``lane_env.py``/``supervisor.py``/``policy.py``/``_config.py``,
loaded by path below, so each has exactly one home.

Launch order is tier D (scarcest capacity) then tier A, staggered. The
family gate (``--no-gate`` skips it) holds tiers B/C until the tier-A
``supervisor.GATE_MODELS`` lanes log a healthy serve, turning a 21-way bet on
the digest-pinned ``lane_env.FLEET_IMAGE`` into a 3-way one. ``--phase
induction`` (default) never shuts a box down; only
``fleet_teardown.py --terminate`` reclaims what it leaves up.

COST: an ungated launch can provision up to 21 distinct spot instances at
once, each billing while up.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

# No `logging.basicConfig` here: it lives in `lane_env.py`, which must call
# it before its by-path load of the induction driver (that module logs at
# import time, and the first handler installed wins). `lane_env` is loaded
# below, so the root logger is already configured by the time `main` logs.

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

# lane_env before supervisor: lane_env.py runs load_dotenv (via its by-path
# load of the induction driver) before smolbench.evals.providers.ec2 freezes
# its EC2_* constants against the environment. Reordering these two lines
# changes that sequence silently -- supervisor.py reaches lane_env at its own
# module scope too, but only as a side effect.
#
# Bound under these exact private names, never unpacked into module-level
# aliases, so every use site spells `_lane_env.X`/`_supervisor.Y` and a moved
# symbol keeps one home; tests reach both modules the same way.
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
    """Resolve ``--lanes`` into a ``{key: Lane}`` map, in ``lane_env.LANES`` order.

    Parameters
    ----------
    raw : str
        Comma-separated lane keys from ``--lanes``.

    Returns
    -------
    dict[str, _lane_env.Lane]
        Selected lanes in ``lane_env.LANES`` order.

    Raises
    ------
    SystemExit
        For a key not in ``lane_env.LANES``.
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


_DRY_RUN_NOTICE = (
    "NOTE: WIRING preview only -- preflight and the image-digest check run on "
    "the live path.\n"
)


def _print_dry_run_plan(lanes: dict[str, _lane_env.Lane], phase_name: str) -> None:
    """Print, per lane, its tier, every scheduled phase's command, and full env.

    Never calls ``supervisor.preflight``/``fleet_image_digest`` (real network
    I/O); `_DRY_RUN_NOTICE` says so under the header.

    Parameters
    ----------
    lanes : dict[str, _lane_env.Lane]
        Lanes to include in the plan.
    phase_name : str
        Requested phase selection.
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

    Parameters
    ----------
    argv : Optional[list[str]], optional
        Command-line arguments to parse.

    Returns
    -------
    int
        ``0`` once the live fleet is all-terminal; individual lanes may still be
        halted (see the printed summary).
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
