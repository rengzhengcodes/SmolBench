"""List, and optionally terminate, the family-ladder scaling study's EC2 fleet.

Read-only by default; nothing is terminated without an explicit
``--terminate``. Deletes no local file: ``ec2.py`` recovers a box from its
``smolbench:experiment`` tag when the state file is missing, so unlinking it
never reclaimed anything -- terminating the instance is what stops billing.
`terminate_fleet` re-checks the ``scaling-`` tag prefix per row rather than
trusting the caller, since that tag is an AWS value this script does not
control.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional


def _fleet_status():
    """Load the sibling ``fleet_status.py`` lazily, through `_config`'s loader.

    `_config` is bootstrapped by hand here, same as every fleet module: it
    can't load itself through its own function.
    """
    name = "smolbench_fleet_config"
    config = sys.modules.get(name)
    if config is None:
        spec = importlib.util.spec_from_file_location(
            name, Path(__file__).resolve().parent / "_config.py")
        sys.modules[name] = config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
    return config.load_fleet_module("fleet_status")


def terminate_fleet(rows: list[dict], *, client_factory: Optional[Any] = None) -> list[dict]:
    """Terminate every instance in `rows`, region by region; returns the rows actually terminated.

    rows: skips any row whose `experiment_tag` lacks the study's `scaling-`
    prefix, the safety re-check against terminating another experiment's box.
    client_factory: `None` builds a boto3 client lazily per region, keeping
    boto3 out of the import chain.
    """
    fleet_status = _fleet_status()
    factory = client_factory or fleet_status._default_client_factory
    terminated: list[dict] = []
    for row in rows:
        tag = row.get("experiment_tag", "")
        if not tag.startswith(fleet_status._config.SCALING_TAG_PREFIX):
            continue  # defensive: fleet_rows filters this server- and client-side
        client = factory(row["region"])
        client.terminate_instances(InstanceIds=[row["instance_id"]])
        terminated.append(row)
    return terminated


def main(argv: Optional[list[str]] = None) -> int:
    """Run the CLI: print the fleet listing, and with ``--terminate`` kill it.

    Returns ``1`` only if the ``--terminate`` confirmation is declined.
    """
    parser = argparse.ArgumentParser(
        description="Enumerate (and, with --terminate, kill) the scaling study's EC2 fleet."
    )
    parser.add_argument(
        "--terminate", action="store_true",
        help="Terminate every enumerated instance. No local file is deleted.",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip the interactive confirmation prompt for --terminate.",
    )
    args = parser.parse_args(argv)

    fleet_status = _fleet_status()
    rows = fleet_status.fleet_rows()
    print(fleet_status.format_fleet_table(rows))

    if not args.terminate:
        print("(read-only listing -- pass --terminate to actually terminate these instances)")
        return 0

    if not rows:
        print("Nothing to terminate.")
        return 0

    lanes = sorted(row.get("lane", "?") for row in rows)
    if not args.yes:
        answer = input(f"Terminate {len(rows)} instance(s) ({', '.join(lanes)})? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted; nothing terminated.")
            return 1

    terminated = terminate_fleet(rows)
    print(f"Terminated {len(terminated)} instance(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
