"""Enumerates, and optionally terminates, the family-ladder scaling study's fleet.

Companion to ``scripts/run_fleet.py`` (launches and monitors the fleet) and
``scripts/fleet_status.py`` (the read-only listing this script is built on
top of, imported rather than re-implemented). This is the "reclaim the
boxes" half of the lifecycle that ``run_fleet.py --phase induction`` alone
deliberately never performs (see that module's docstring): it prints a
reminder pointing here for exactly that reason.

Default behaviour is READ-ONLY: with no flags, this script enumerates the
fleet (via ``fleet_status.fleet_rows``) and prints the table plus a
reminder that ``--terminate`` is required to actually kill anything. Nothing
is ever terminated, and no state file is ever deleted, unless ``--terminate``
is passed explicitly.

Safety invariants -- documented here, and ENFORCED IN CODE, not just by
convention
----------------------------------------------------------------------------
- This script NEVER touches an instance whose ``smolbench:experiment`` tag
  does not start with ``"scaling-"``. ``fleet_status.fleet_rows`` already
  filters on this both server-side (an EC2 tag-value wildcard filter) and
  client-side (a belt-and-braces re-check); `terminate_fleet` below adds a
  THIRD check of the same fact immediately before calling
  ``terminate_instances``, so a caller that ever hands this function a
  hand-built row list (bypassing `fleet_status.fleet_rows` entirely) still
  cannot terminate an instance outside this prefix.
- This script NEVER deletes a file that is not shaped exactly
  ``REPO_ROOT/.ec2_state_scaling_<lane>.json``. `delete_state_files` derives
  the path from a row's `lane` field, RESOLVES it (normalising away any
  ``..`` traversal), and verifies the resolved path's parent is `REPO_ROOT`
  and its basename matches the ``.ec2_state_scaling_*.json`` glob BEFORE
  unlinking -- so even a maliciously tag-crafted `lane` value (an AWS
  principal with tag-write access naming an instance
  ``scaling-../../secrets``) cannot walk this outside the repo root or
  delete an unrelated state file.

Run (repo root, main venv)::

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
    """Lazily loads ``scripts/fleet_status.py`` by file path, cached after the first call.

    Loaded by path (not ``sys.path`` + a bare ``import fleet_status``) for
    the same reason as ``run_fleet.py``'s identical helper: it avoids any
    risk of colliding with how ``tests/test_run_fleet.py`` loads these
    files under private module names, and it keeps this module's own
    import-time footprint to nothing but name/constant definitions --
    `fleet_status.py` is only ever loaded once this script's `main` (or a
    direct call to `terminate_fleet`/`delete_state_files`) actually needs
    it.
    """
    path = Path(__file__).resolve().parent / "fleet_status.py"
    spec = importlib.util.spec_from_file_location("fleet_teardown_fleet_status_dep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_file_path(lane: str) -> Path:
    """Returns the (unresolved) EC2 state-file path for `lane`.

    Parameters
    ----------
    lane : str
        A lane key, e.g. from a `fleet_status.fleet_rows` row's `"lane"`
        field.

    Returns
    -------
    Path
        ``REPO_ROOT / f".ec2_state_scaling_{lane}.json"``. NOT
        independently verified to be safe here -- callers that actually
        delete a file built from this MUST re-verify it via
        ``.resolve()`` first (see `delete_state_files`), since `lane`
        ultimately originates from an AWS tag value this script does not
        control.
    """
    return REPO_ROOT / f".ec2_state_scaling_{lane}.json"


def terminate_fleet(rows: list[dict], *, client_factory: Optional[Any] = None) -> list[dict]:
    """Terminates every instance in `rows`, region by region.

    Parameters
    ----------
    rows : list[dict]
        Rows shaped like `fleet_status.fleet_rows`'s output (must carry
        `region`, `instance_id`, `experiment_tag`).
    client_factory : Callable[[str], Any] or None, optional
        Maps a region to an EC2-client-shaped object (``terminate_
        instances(InstanceIds=...)``). ``None`` builds a real boto3 client
        lazily per region. Injectable for testing.

    Returns
    -------
    list[dict]
        The subset of `rows` actually terminated -- i.e. every row whose
        `experiment_tag` starts with `fleet_status.SCALING_TAG_PREFIX`.

    Notes
    -----
    Re-checks `experiment_tag`'s prefix immediately before calling
    ``terminate_instances`` -- see the module docstring's safety-invariants
    section for why this holds even though `rows` normally already passed
    through that same filter inside `fleet_status.fleet_rows`.

    boto3 is imported lazily (inside the default client factory), matching
    this repo's house convention (see ``smolbench.evals.ec2``) that nothing
    reachable at import time requires the AWS SDK.
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
            continue  # should be unreachable via fleet_rows -- see docstring
        client = factory(row["region"])
        client.terminate_instances(InstanceIds=[row["instance_id"]])
        terminated.append(row)
    return terminated


def delete_state_files(rows: list[dict]) -> list[Path]:
    """Deletes the local EC2 state file for each row in `rows`, if present.

    Parameters
    ----------
    rows : list[dict]
        Rows shaped like `fleet_status.fleet_rows`'s output (must carry
        `lane`).

    Returns
    -------
    list[Path]
        Every state-file path actually deleted.

    Notes
    -----
    For each row, `state_file_path(row["lane"])` is RESOLVED
    (``Path.resolve()``, which normalises away any ``..`` components) and
    only deleted when the resolved path's parent is `REPO_ROOT` (also
    resolved) AND its basename matches `STATE_FILE_GLOB`. Both checks
    should be unreachable given `state_file_path`'s own construction (a
    plain f-string with no directory separators expected in `lane`), but
    `lane` traces back to an AWS tag value this script does not control --
    see the module docstring's safety-invariants section.
    """
    deleted: list[Path] = []
    repo_root_resolved = REPO_ROOT.resolve()
    for row in rows:
        lane = row.get("lane", "")
        resolved = state_file_path(lane).resolve()
        if resolved.parent != repo_root_resolved or not fnmatch.fnmatch(resolved.name, STATE_FILE_GLOB):
            continue  # should be unreachable -- see docstring
        if resolved.exists():
            resolved.unlink()
            deleted.append(resolved)
    return deleted


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Parameters
    ----------
    argv : list[str] or None, optional
        Arguments to parse; ``None`` parses ``sys.argv[1:]``.

    Returns
    -------
    int
        ``0`` on a successful read-only listing, or after a confirmed/forced
        termination. ``1`` if ``--terminate`` was requested but the
        interactive confirmation was declined.

    Notes
    -----
    Without ``--terminate``, this is a thin, read-only wrapper around
    `fleet_status.fleet_rows` / `format_fleet_table`. With ``--terminate``
    and no ``--yes``, prompts interactively with the instance count and lane
    list before calling `terminate_fleet` and `delete_state_files`.
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
