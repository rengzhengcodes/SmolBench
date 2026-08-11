"""Read-only enumeration of the family-ladder scaling study's live EC2 fleet.

Companion to ``scripts/run_fleet.py`` (the supervisor that launches and
monitors the fleet) and ``scripts/fleet_teardown.py`` (which can terminate
it). This module does exactly one thing -- list every EC2 instance tagged
for this study, across every region it might have landed in -- and does it
in a way that is safe to call from ANYWHERE: a notebook cell (this module is
also imported directly by an analysis notebook to render a live fleet
table), a test (via dependency injection -- see `client_factory` below), or
this file's own ``__main__`` CLI.

No boto3 import at module scope. Importing this module -- for the notebook,
for `run_fleet.py`'s monitor loop, or for the offline test suite -- must
never require the AWS SDK to be installed; `boto3` is imported lazily,
inside `_default_client_factory`, only when a real (non-injected) client is
actually needed.

Run (repo root, main venv)::

    .venv/bin/python scripts/fleet_status.py
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Sequence

#: Every lane's EC2 experiment tag is ``f"{SCALING_TAG_PREFIX}{spec_key}"``
#: (see ``run_fleet.Lane.experiment_tag``) -- this is the ONE constant that
#: has to agree between the two modules for this file to find anything.
SCALING_TAG_PREFIX = "scaling-"
#: Every region a lane might have provisioned in -- the union of
#: ``run_fleet.DEFAULT_REGIONS`` and its tier-D override
#: (``us-east-2,us-west-2``, already a subset of these three).
STATUS_REGIONS: tuple[str, ...] = ("us-east-1", "us-east-2", "us-west-2")


def _default_client_factory(region: str) -> Any:
    """Builds a real boto3 EC2 client bound to `region`.

    boto3 is imported HERE, not at module scope -- see the module
    docstring's "No boto3 import at module scope" section.
    """
    import boto3

    return boto3.client("ec2", region_name=region)


def fleet_rows(
    regions: Sequence[str] = STATUS_REGIONS,
    tag_prefix: str = SCALING_TAG_PREFIX,
    client_factory: Optional[Callable[[str], Any]] = None,
) -> list[dict]:
    """Lists every running/pending EC2 instance tagged for this study, across `regions`.

    Parameters
    ----------
    regions : Sequence[str], optional
        AWS regions to query. Defaults to `STATUS_REGIONS`.
    tag_prefix : str, optional
        Only instances whose ``smolbench:experiment`` tag starts with this
        prefix are returned. Defaults to `SCALING_TAG_PREFIX`.
    client_factory : Callable[[str], Any] or None, optional
        Maps a region name to an object exposing ``describe_instances(
        **kwargs)`` (the shape of a boto3 EC2 client). ``None`` (the
        default) uses `_default_client_factory`, which builds a real boto3
        client lazily. This injection seam is what makes this function
        testable with zero AWS SDK dependency -- see
        ``tests/test_run_fleet.py``'s ``_FakeEc2Client``.

    Returns
    -------
    list[dict]
        One dict per matching instance, with EXACTLY these keys: `region`,
        `experiment_tag`, `lane` (the `experiment_tag` with `tag_prefix`
        stripped), `instance_id`, `instance_type`, `availability_zone`,
        `state`, `launch_time` (the raw ``datetime``, or ``None`` if EC2
        reported none), `age_hours` (float, computed against
        ``datetime.now(timezone.utc)`` at call time; ``0.0`` when
        `launch_time` is ``None``).

    Notes
    -----
    The tag filter is applied SERVER-SIDE
    (``Filters=[{"Name": "tag:smolbench:experiment", "Values":
    [f"{tag_prefix}*"]}, ...]``) -- EC2 tag filters support a trailing
    ``*`` wildcard, so this call never lists (or pays the latency/cost of
    listing) the whole account's instances. On top of that, every returned
    instance's tag is re-checked CLIENT-SIDE against `tag_prefix` -- belt
    and braces against a future change to the server-side filter, so an
    instance tagged e.g. ``"periodic-induction"`` (a sibling experiment's
    tag) can never leak into this listing even if the filter itself
    regresses.

    A region that raises (no credentials for it, the region is disabled for
    this account, a throttle) is LOGGED and SKIPPED, not fatal -- one bad
    region must not blind the operator to the fleet state in the other two.

    Only ``instance-state-name`` in ``{"running", "pending"}`` is queried,
    matching what an operator cares about for a LIVE fleet -- a terminated
    or terminating instance is not "in the fleet" for this listing's
    purpose (``fleet_teardown.py``'s ``--terminate`` path reads this same
    listing to decide what to kill, and killing an already-dead instance a
    second time is pointless).
    """
    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    factory = client_factory or _default_client_factory

    for region in regions:
        try:
            client = factory(region)
            response = client.describe_instances(
                Filters=[
                    {"Name": "tag:smolbench:experiment", "Values": [f"{tag_prefix}*"]},
                    {"Name": "instance-state-name", "Values": ["running", "pending"]},
                ]
            )
        except Exception as exc:  # noqa: BLE001 -- one bad region must not blind the operator
            logging.warning(f"fleet_rows: {region} describe_instances failed, skipping: {exc}")
            continue

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                experiment_tag = tags.get("smolbench:experiment", "")
                if not experiment_tag.startswith(tag_prefix):
                    continue  # belt-and-braces re-check -- see docstring
                launch_time = instance.get("LaunchTime")
                age_hours = (
                    (now - launch_time).total_seconds() / 3600 if launch_time is not None else 0.0
                )
                rows.append(
                    {
                        "region": region,
                        "experiment_tag": experiment_tag,
                        "lane": experiment_tag[len(tag_prefix):],
                        "instance_id": instance.get("InstanceId", "?"),
                        "instance_type": instance.get("InstanceType", "?"),
                        "availability_zone": instance.get("Placement", {}).get(
                            "AvailabilityZone", "?"
                        ),
                        "state": instance.get("State", {}).get("Name", "?"),
                        "launch_time": launch_time,
                        "age_hours": age_hours,
                    }
                )
    return rows


def format_fleet_table(rows: Sequence[dict]) -> str:
    """Renders `rows` (as returned by `fleet_rows`) as a fixed-width text table.

    Parameters
    ----------
    rows : Sequence[dict]
        Rows from `fleet_rows` (or anything with the same keys).

    Returns
    -------
    str
        A fixed-width table containing, for every row, its `lane`,
        `instance_id`, `instance_type`, `availability_zone`, `state`, and
        age (formatted from `age_hours`). ALWAYS non-empty, even for an
        empty `rows` -- an empty fleet and a broken query must read
        differently to the operator, so an empty `rows` renders an explicit
        "no scaling-* instances found" line rather than an empty string
        that could be mistaken for output that never printed.
    """
    if not rows:
        return f"fleet_status: no {SCALING_TAG_PREFIX}* instances found in any region.\n"

    columns = ("lane", "instance_id", "instance_type", "availability_zone", "state", "age", "region")
    formatted_rows = []
    for row in rows:
        formatted_rows.append(
            {
                "lane": str(row.get("lane", "?")),
                "instance_id": str(row.get("instance_id", "?")),
                "instance_type": str(row.get("instance_type", "?")),
                "availability_zone": str(row.get("availability_zone", "?")),
                "state": str(row.get("state", "?")),
                "age": f"{row.get('age_hours', 0.0):.1f}h",
                "region": str(row.get("region", "?")),
            }
        )

    widths = {c: len(c) for c in columns}
    for formatted in formatted_rows:
        for c in columns:
            widths[c] = max(widths[c], len(formatted[c]))

    lines = ["  ".join(c.upper().ljust(widths[c]) for c in columns)]
    lines.append("  ".join("-" * widths[c] for c in columns))
    for formatted in formatted_rows:
        lines.append("  ".join(formatted[c].ljust(widths[c]) for c in columns))
    return "\n".join(lines) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point: prints the live fleet table and returns 0.

    Parameters
    ----------
    argv : list[str] or None, optional
        Arguments to parse; ``None`` parses ``sys.argv[1:]``. This script
        takes no flags -- `fleet_rows`'s defaults cover every region this
        study could have provisioned in.

    Returns
    -------
    int
        Always ``0`` -- a region that fails to describe is logged and
        skipped by `fleet_rows`, not raised, so there is no fatal path here
        short of an unrecognised argument.
    """
    parser = argparse.ArgumentParser(
        description="Read-only listing of the scaling study's live EC2 fleet."
    )
    parser.parse_args(argv)
    print(format_fleet_table(fleet_rows()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
