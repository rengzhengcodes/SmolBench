"""List, and optionally terminate, the family-ladder scaling study's EC2 fleet.

The teardown half of the fleet lifecycle: ``run_fleet.py --phase induction``
never terminates anything, on purpose, and prints a reminder pointing here. The
listing itself is `fleet_status.py`, imported rather than reimplemented. The
default is READ-ONLY: nothing is terminated and no state file deleted without
an explicit ``--terminate``.

Safety invariants, enforced in code rather than by convention:

- Only instances whose ``smolbench:experiment`` tag starts with ``"scaling-"``
  are terminated. `terminate_fleet` re-checks the prefix immediately before
  ``terminate_instances``, so even a hand-built row list cannot escape it.
- Only ``REPO_ROOT/.ec2_state_scaling_<lane>.json`` is ever unlinked;
  `delete_state_files` ``.resolve()``s first, because `lane` comes from an AWS
  tag value this script does not control.

Run from the repo root::

    .venv/bin/python scripts/fleet/fleet_teardown.py                    # listing
    .venv/bin/python scripts/fleet/fleet_teardown.py --terminate [--yes]
"""

from __future__ import annotations

import argparse
import fnmatch
import functools
import importlib.util
from pathlib import Path
from typing import Any, Optional

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
STATE_FILE_GLOB = ".ec2_state_scaling_*.json"


@functools.lru_cache(maxsize=1)
def _fleet_status():
    """Load ``scripts/fleet/fleet_status.py`` by file path, lazily; cached.

    By path rather than a bare import, to avoid colliding with the private module
    names ``tests/tooling/test_run_fleet.py`` loads these files under.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("fleet_teardown_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_file_path(lane: str) -> Path:
    """Return the UNRESOLVED ``REPO_ROOT/.ec2_state_scaling_{lane}.json`` path.

    Nothing is checked here. `lane` ultimately comes from an AWS tag value this
    script does not control, so a caller that deletes a file built from this
    path MUST re-verify it with ``.resolve()`` first (see `delete_state_files`).
    """
    return REPO_ROOT / f".ec2_state_scaling_{lane}.json"


def terminate_fleet(rows: list[dict], *, client_factory: Optional[Any] = None) -> list[dict]:
    """Terminate every instance in `rows`, region by region.

    Parameters
    ----------
    rows : list[dict]
        Shaped like `fleet_status.fleet_rows`'s output; must carry `region`,
        `instance_id` and `experiment_tag`. A row whose `experiment_tag` lacks
        the `fleet_status.SCALING_TAG_PREFIX` prefix is SKIPPED -- the last-line
        safety re-check described in the module docstring.
    client_factory : Any, optional
        Maps a region to an object with ``terminate_instances(InstanceIds=...)``;
        ``None`` builds a real boto3 client lazily per region, per this repo's
        convention that nothing reachable at import time requires the AWS SDK.

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


def delete_state_files(rows: list[dict]) -> list[Path]:
    """Delete each row's local EC2 state file if present.

    Parameters
    ----------
    rows : list[dict]
        Must carry `lane`.

    Returns
    -------
    list[Path]
        The resolved paths actually unlinked.

    Notes
    -----
    `state_file_path(row["lane"])` is ``.resolve()``d and unlinked only when its
    parent is `REPO_ROOT` (also resolved) AND its basename matches
    `STATE_FILE_GLOB`: `lane` traces back to an AWS tag value, so a crafted
    ``scaling-../../secrets`` tag must not walk outside the repo.
    """
    deleted: list[Path] = []
    repo_root_resolved = REPO_ROOT.resolve()
    for row in rows:
        lane = row.get("lane", "")
        resolved = state_file_path(lane).resolve()
        if resolved.parent != repo_root_resolved or not fnmatch.fnmatch(resolved.name, STATE_FILE_GLOB):
            continue  # should be unreachable -- see docstring Notes
        if resolved.exists():
            resolved.unlink()
            deleted.append(resolved)
    return deleted


def main(argv: Optional[list[str]] = None) -> int:
    """Run the CLI: print the fleet listing, and with ``--terminate`` kill it.

    Returns
    -------
    int
        ``0`` for a read-only listing, or after a confirmed or ``--yes``-forced
        termination (`terminate_fleet`, then `delete_state_files`); ``1`` if
        ``--terminate`` was requested and the confirmation declined.
    """
    parser = argparse.ArgumentParser(
        description="Enumerate (and, with --terminate, kill) the scaling study's EC2 fleet."
    )
    parser.add_argument(
        "--terminate", action="store_true",
        help="Terminate every enumerated instance and delete its local state file.",
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
    deleted = delete_state_files(terminated)
    print(f"Terminated {len(terminated)} instance(s); deleted {len(deleted)} state file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
