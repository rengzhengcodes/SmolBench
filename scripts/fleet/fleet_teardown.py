"""List or explicitly terminate the scaling study's EC2 fleet.

Deleting state cannot stop billing because ec2.py recovers boxes from their
``smolbench:experiment`` tags; only termination reclaims them. Re-check each AWS
tag before termination because callers do not control those values.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Optional


def _fleet_status() -> ModuleType:
    """Load the sibling ``fleet_status.py`` lazily, through `_config`'s loader.

    Bootstrap ``_config`` because it cannot load itself.
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
    """Terminate eligible instances and return the terminated rows.

    Parameters
    ----------
    rows : list[dict]
        Rows; tags outside the study prefix are skipped for safety.
    client_factory : Optional[Any], optional
        Client factory, or a lazy boto3 client.

    Returns
    -------
    list[dict]
        Terminated rows.
    """
    fleet_status = _fleet_status()
    factory = client_factory or fleet_status._default_client_factory
    terminated: list[dict] = []
    for row in rows:
        tag = row.get("experiment_tag", "")
        if not tag.startswith(fleet_status._config.SCALING_TAG_PREFIX):
            continue  # Never terminate a row outside the study prefix.
        client = factory(row["region"])
        client.terminate_instances(InstanceIds=[row["instance_id"]])
        terminated.append(row)
    return terminated


def main(argv: Optional[list[str]] = None) -> int:
    """Print the fleet; terminate only with ``--terminate``.

    Parameters
    ----------
    argv : Optional[list[str]], optional
        Command-line arguments.

    Returns
    -------
    int
        One when confirmation is declined; otherwise zero.
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
