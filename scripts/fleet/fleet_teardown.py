"""List, and optionally terminate, the family-ladder scaling study's EC2 fleet.

The teardown half of the fleet lifecycle: ``run_fleet.py --phase induction``
never terminates anything, on purpose, and prints a reminder pointing here. The
listing itself is `fleet_status.py`, imported rather than reimplemented. The
default is READ-ONLY: nothing is terminated without an explicit
``--terminate``.

This script DELETES NO LOCAL FILE; it terminates instances, and that is all it
does. The per-lane EC2 state file belongs to
``smolbench/evals/providers/ec2.py``'s own provisioning mechanism, which
recovers a box from its ``smolbench:experiment`` tag when that file is
missing. Unlinking it therefore never reclaimed anything and could not have --
terminating the instance is what stops the billing.

That leaves ONE safety invariant re-checked in code at the point of action:
`terminate_fleet` skips any row whose ``experiment_tag`` does not start with
`fleet_status.SCALING_TAG_PREFIX`. It is re-checked rather than trusted
because that tag is an AWS tag value this script does not control.
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
from pathlib import Path
from typing import Any, Optional


@functools.lru_cache(maxsize=1)
def _fleet_status():
    """Load ``scripts/fleet/fleet_status.py`` by file path, lazily; cached.

    By path rather than a bare import: avoids colliding with the private module
    names ``tests/tooling/test_run_fleet.py`` loads these files under.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("fleet_teardown_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def terminate_fleet(rows: list[dict], *, client_factory: Optional[Any] = None) -> list[dict]:
    """Terminate every instance in `rows`, region by region.

    Parameters
    ----------
    rows : list[dict]
        `fleet_status.fleet_rows`-shaped; needs `region`, `instance_id` and
        `experiment_tag`. A row whose `experiment_tag` lacks the
        `fleet_status.SCALING_TAG_PREFIX` prefix is SKIPPED -- the safety
        re-check that stops this terminating another experiment's instance.
    client_factory : Any, optional
        Region -> object with ``terminate_instances(InstanceIds=...)``; ``None``
        builds a boto3 client lazily per region (no AWS SDK at import time).

    Returns
    -------
    list[dict]
        The rows actually terminated.
    """
    fleet_status = _fleet_status()

    def _default_factory(region: str) -> Any:
        import boto3

        return boto3.client("ec2", region_name=region)

    factory = client_factory or _default_factory
    terminated: list[dict] = []
    for row in rows:
        tag = row.get("experiment_tag", "")
        if not tag.startswith(fleet_status.SCALING_TAG_PREFIX):
            continue  # should be unreachable through fleet_rows -- see docstring
        client = factory(row["region"])
        client.terminate_instances(InstanceIds=[row["instance_id"]])
        terminated.append(row)
    return terminated


def main(argv: Optional[list[str]] = None) -> int:
    """Run the CLI: print the fleet listing, and with ``--terminate`` kill it.

    Returns
    -------
    int
        ``0`` for a read-only listing, or after a confirmed (or ``--yes``)
        `terminate_fleet` call; ``1`` if the ``--terminate`` confirmation was
        declined.
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
