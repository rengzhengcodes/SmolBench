"""List the family-ladder scaling study's live EC2 fleet, read-only.

This module is a companion to ``scripts/fleet/run_fleet.py`` (the supervisor
that launches and monitors the fleet) and ``scripts/fleet/fleet_teardown.py``
(which can terminate it). This module does exactly one thing: it lists
every EC2 instance tagged for this study, across every region the study
might use it. You can call it safely from anywhere: a notebook cell (an
analysis notebook also imports this module directly, to render a live
fleet table), a test, or this file's own ``__main__`` CLI. Tests reach
it through dependency injection; see `client_factory` below.

This module does not import boto3 at module scope. None of its callers --
the notebook, `run_fleet.py`'s monitor loop, or the offline test suite --
may need the AWS SDK installed just to import it.
`_default_client_factory` imports `boto3` lazily, only when it needs a
real (non-injected) client.

Run this script from the repo root, in the main venv::

    .venv/bin/python scripts/fleet/fleet_status.py
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Sequence

#: Every lane's EC2 experiment tag is ``f"{SCALING_TAG_PREFIX}{spec_key}"``
#: (see ``run_fleet.Lane.experiment_tag``). This is the ONE constant that
#: must agree between the two modules, or this file finds nothing.
SCALING_TAG_PREFIX = "scaling-"
#: Every region a lane might have provisioned in. This matches
#: ``run_fleet.DEFAULT_REGIONS``; tier D's override spans the same three
#: regions, so these cover every tier.
STATUS_REGIONS: tuple[str, ...] = ("us-east-1", "us-east-2", "us-west-2")


def _default_client_factory(region: str) -> Any:
    """Build a real boto3 EC2 client bound to `region`.

    This function imports boto3 here, not at module scope. See the module
    docstring for why.

    Parameters
    ----------
    region : str
        AWS region name to bind the client to.

    Returns
    -------
    Any
        A boto3 EC2 client for `region`.
    """
    import boto3

    return boto3.client("ec2", region_name=region)


def fleet_rows(
    regions: Sequence[str] = STATUS_REGIONS,
    tag_prefix: str = SCALING_TAG_PREFIX,
    client_factory: Optional[Callable[[str], Any]] = None,
) -> list[dict]:
    """List every running or pending EC2 instance tagged for this study.

    This function queries each region in `regions` in turn.

    Parameters
    ----------
    regions : Sequence[str], optional
        AWS regions to query. Defaults to `STATUS_REGIONS`.
    tag_prefix : str, optional
        This function returns only instances whose ``smolbench:experiment``
        tag starts with this prefix. Defaults to `SCALING_TAG_PREFIX`.
    client_factory : Callable[[str], Any] or None, optional
        Maps a region name to an object that exposes
        ``describe_instances(**kwargs)`` (the shape of a boto3 EC2 client).
        The default, ``None``, uses `_default_client_factory`, which
        builds a real boto3 client lazily. This injection seam makes this
        function testable with zero AWS SDK dependency; see
        ``tests/tooling/test_run_fleet.py``'s ``_FakeEc2Client``.

    Returns
    -------
    list[dict]
        One dict per matching instance, with exactly these keys: `region`,
        `experiment_tag`, `lane` (the `experiment_tag` with `tag_prefix`
        stripped), `instance_id`, `instance_type`, `availability_zone`,
        `state`, `launch_time` (the raw ``datetime``, or ``None`` if EC2
        reported none), and `age_hours` (float, computed against
        ``datetime.now(timezone.utc)`` at call time; ``0.0`` when
        `launch_time` is ``None``).

    Notes
    -----
    This function applies the tag filter SERVER-SIDE
    (``Filters=[{"Name": "tag:smolbench:experiment", "Values":
    [f"{tag_prefix}*"]}, ...]``). EC2 tag filters support a trailing ``*``
    wildcard, so this call never lists the whole account's instances, and
    never pays the latency or cost of listing them. This function also
    re-checks every returned instance's tag CLIENT-SIDE against
    `tag_prefix`, as a second guard against a future change to the
    server-side filter. This guard stops an instance tagged for a sibling
    experiment (for example ``"periodic-induction"``) from leaking into
    this listing, even if the server-side filter regresses.

    If a region raises an error (no credentials for it, the region is
    disabled for this account, a throttle), this function logs the error
    and skips the region. It does not treat the error as fatal, because
    one bad region must not hide the fleet state in the other two.

    This function queries only instances where ``instance-state-name`` is
    ``"running"`` or ``"pending"``. This matches what an operator cares
    about for a LIVE fleet: a terminated or terminating instance is not
    "in the fleet" for this listing's purpose. (``fleet_teardown.py``'s
    ``--terminate`` path reads this same listing to decide what to kill,
    and killing an already-dead instance a second time serves no purpose.)
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
        except Exception as exc:  # noqa: BLE001 -- one bad region must not hide others
            logging.warning(f"fleet_rows: {region} describe_instances failed, skipping: {exc}")
            continue

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                experiment_tag = tags.get("smolbench:experiment", "")
                if not experiment_tag.startswith(tag_prefix):
                    continue  # second guard re-check -- see docstring Notes
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
    """Render `rows` (as returned by `fleet_rows`) as a fixed-width text table.

    Parameters
    ----------
    rows : Sequence[dict]
        Rows from `fleet_rows` (or anything with the same keys).

    Returns
    -------
    str
        A fixed-width table with, for every row, its `lane`,
        `instance_id`, `instance_type`, `availability_zone`, `state`, and
        age (formatted from `age_hours`). This function always returns a
        non-empty string, even for an empty `rows`. An empty fleet and a
        broken query must read differently to the operator. An empty
        `rows` renders an explicit "no scaling-* instances found" line,
        not an empty string that could look like output that never
        printed.
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
    """Run the CLI entry point: print the live fleet table and return 0.

    Parameters
    ----------
    argv : list[str] or None, optional
        Arguments to parse. ``None`` parses ``sys.argv[1:]``. This script
        takes no flags: `fleet_rows`'s defaults already cover every region
        this study could have provisioned in.

    Returns
    -------
    int
        Always ``0``. `fleet_rows` logs and skips a region that fails to
        describe; it does not raise. So this function has no fatal path,
        short of an unrecognized argument.
    """
    parser = argparse.ArgumentParser(
        description="Read-only listing of the scaling study's live EC2 fleet."
    )
    parser.parse_args(argv)
    print(format_fleet_table(fleet_rows()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
