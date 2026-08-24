"""List, and optionally terminate, the family-ladder scaling study's fleet.

This script is a companion to ``scripts/run_fleet.py`` (launches and
monitors the fleet) and ``scripts/fleet_status.py`` (the read-only listing
this script builds on, by import, not by reimplementation). This script is
the "reclaim the boxes" half of the lifecycle. ``run_fleet.py --phase
induction`` never performs that half on its own, on purpose (see that
module's docstring); it prints a reminder that points here.

The default behavior is READ-ONLY. With no flags, this script enumerates
the fleet (through ``fleet_status.fleet_rows``), prints the table, and
prints a reminder that you must pass ``--terminate`` to kill anything.
This script never terminates an instance, and never deletes a state file,
unless you pass ``--terminate`` explicitly.

Safety invariants -- documented here, and ENFORCED IN CODE, not just by
convention
----------------------------------------------------------------------------
- This script NEVER touches an instance whose ``smolbench:experiment`` tag
  does not start with ``"scaling-"``. ``fleet_status.fleet_rows`` already
  filters on this, both server-side (an EC2 tag-value wildcard filter) and
  client-side (a second re-check). `terminate_fleet` below adds a THIRD
  check of the same fact, immediately before it calls
  ``terminate_instances``. So even a caller that hands this function a
  hand-built row list, bypassing `fleet_status.fleet_rows` entirely, still
  cannot terminate an instance outside this prefix.
- This script NEVER deletes a file unless its path is exactly
  ``REPO_ROOT/.ec2_state_scaling_<lane>.json``. `delete_state_files`
  derives the path from a row's `lane` field and RESOLVES it (this
  removes any ``..`` traversal). Before it unlinks the file, it also
  verifies that the resolved path's parent is `REPO_ROOT` and its
  basename matches the ``.ec2_state_scaling_*.json`` glob. So even a
  maliciously tag-crafted `lane` value (an AWS principal with tag-write
  access, naming an instance ``scaling-../../secrets``) cannot walk
  this path outside the repo root, or delete an unrelated state file.

Run this script from the repo root, in the main venv::

    .venv/bin/python scripts/fleet_teardown.py                 # read-only listing
    .venv/bin/python scripts/fleet_teardown.py --terminate      # prompts, then kills
    .venv/bin/python scripts/fleet_teardown.py --terminate --yes  # no prompt
"""

from __future__ import annotations

import argparse
import fnmatch
import functools
import importlib.util
from pathlib import Path
from typing import Any, Optional

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
STATE_FILE_GLOB = ".ec2_state_scaling_*.json"


@functools.lru_cache(maxsize=1)
def _fleet_status():
    """Load ``scripts/fleet_status.py`` by file path, lazily, and cache the result.

    This function loads the module by path, not by ``sys.path`` plus a
    bare ``import fleet_status``, for the same reason as
    ``run_fleet.py``'s identical helper. This avoids any risk of colliding
    with how ``tests/test_run_fleet.py`` loads these files under private
    module names. It also keeps this module's own import-time footprint
    to nothing but name and constant definitions: `fleet_status.py` loads
    only once this script's `main` (or a direct call to
    `terminate_fleet` or `delete_state_files`) actually needs it.

    Returns
    -------
    module
        The loaded ``fleet_status`` module.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("fleet_teardown_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_file_path(lane: str) -> Path:
    """Return the unresolved EC2 state-file path for `lane`.

    Parameters
    ----------
    lane : str
        A lane key, for example from a `fleet_status.fleet_rows` row's
        `"lane"` field.

    Returns
    -------
    Path
        ``REPO_ROOT / f".ec2_state_scaling_{lane}.json"``. This function
        does not verify that the path is safe. A caller that deletes a
        file built from this path MUST re-verify it with ``.resolve()``
        first (see `delete_state_files`), because `lane` ultimately
        comes from an AWS tag value this script does not control.
    """
    return REPO_ROOT / f".ec2_state_scaling_{lane}.json"


def terminate_fleet(rows: list[dict], *, client_factory: Optional[Any] = None) -> list[dict]:
    """Terminate every instance in `rows`, region by region.

    Parameters
    ----------
    rows : list[dict]
        Rows shaped like `fleet_status.fleet_rows`'s output. Each row must
        carry `region`, `instance_id`, and `experiment_tag`.
    client_factory : Callable[[str], Any] or None, optional
        Maps a region to an EC2-client-shaped object (with a
        ``terminate_instances(InstanceIds=...)`` method). The default,
        ``None``, builds a real boto3 client lazily per region. You can
        inject this for testing.

    Returns
    -------
    list[dict]
        The subset of `rows` this function actually terminated: every row
        whose `experiment_tag` starts with `fleet_status.SCALING_TAG_PREFIX`.

    Notes
    -----
    This function re-checks `experiment_tag`'s prefix immediately before
    it calls ``terminate_instances``. See the module docstring's
    safety-invariants section for why this check matters, even though
    `rows` has normally already passed the same filter inside
    `fleet_status.fleet_rows`.

    This function imports boto3 lazily, inside the default client
    factory. This matches this repo's house convention (see
    ``smolbench.evals.ec2``): nothing reachable at import time requires
    the AWS SDK.
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
    """Delete the local EC2 state file for each row in `rows`, if present.

    Parameters
    ----------
    rows : list[dict]
        Rows shaped like `fleet_status.fleet_rows`'s output. Each row must
        carry `lane`.

    Returns
    -------
    list[Path]
        Every state-file path this function actually deleted.

    Notes
    -----
    For each row, this function RESOLVES `state_file_path(row["lane"])`
    (``Path.resolve()``, which removes any ``..`` components). It deletes
    the file only when the resolved path's parent is `REPO_ROOT` (also
    resolved) AND its basename matches `STATE_FILE_GLOB`. Both checks
    should be unreachable given how `state_file_path` builds the path (a
    plain f-string, with no directory separators expected in `lane`). But
    `lane` traces back to an AWS tag value this script does not control;
    see the module docstring's safety-invariants section.
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
    """Run the CLI entry point.

    Parameters
    ----------
    argv : list[str] or None, optional
        Arguments to parse. ``None`` parses ``sys.argv[1:]``.

    Returns
    -------
    int
        ``0`` on a successful read-only listing, or after a confirmed or
        forced termination. ``1`` if the caller requested ``--terminate``
        but declined the interactive confirmation.

    Notes
    -----
    Without ``--terminate``, this function is a thin, read-only wrapper
    around `fleet_status.fleet_rows` and `format_fleet_table`. With
    ``--terminate`` and no ``--yes``, this function prompts interactively
    with the instance count and lane list, before it calls
    `terminate_fleet` and `delete_state_files`.
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
