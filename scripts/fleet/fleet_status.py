"""List the family-ladder scaling study's live EC2 fleet, read-only.

Companion to ``scripts/fleet/run_fleet.py`` (launches and monitors) and
``scripts/fleet/fleet_teardown.py`` (terminates); both import it, as do
analysis notebooks. Importing needs no AWS SDK -- boto3 is imported lazily
inside `_default_client_factory`, never at module scope -- and tests inject a
fake through `client_factory`.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Sequence

#: Every lane's EC2 experiment tag is ``f"{SCALING_TAG_PREFIX}{spec_key}"``
#: (see ``run_fleet.Lane.experiment_tag``) -- the ONE constant that must agree
#: between the two modules, or this file finds nothing.
SCALING_TAG_PREFIX = "scaling-"
#: Every region a lane might have provisioned in: matches
#: ``run_fleet.DEFAULT_REGIONS``, and tier D's override spans the same three.
STATUS_REGIONS: tuple[str, ...] = ("us-east-1", "us-east-2", "us-west-2")


def _default_client_factory(region: str) -> Any:
    """Build a boto3 EC2 client for `region` (boto3 imported here, lazily)."""
    import boto3

    return boto3.client("ec2", region_name=region)


def fleet_rows(
    regions: Sequence[str] = STATUS_REGIONS,
    tag_prefix: str = SCALING_TAG_PREFIX,
    client_factory: Optional[Callable[[str], Any]] = None,
) -> list[dict]:
    """List every running or pending EC2 instance tagged for this study.

    Parameters
    ----------
    client_factory : Callable[[str], Any] or None, optional
        Region name -> object exposing ``describe_instances(**kwargs)``; ``None``
        uses `_default_client_factory`. The seam that makes this testable with no
        AWS SDK (``tests/tooling/test_run_fleet.py``'s ``_FakeEc2Client``).

    Returns
    -------
    list[dict]
        One dict per instance, with exactly these keys: `region`,
        `experiment_tag`, `lane` (the tag minus `tag_prefix`), `instance_id`,
        `instance_type`, `availability_zone`, `state`, `launch_time` (raw
        ``datetime``, or ``None`` if EC2 reported none) and `age_hours` (float,
        against ``datetime.now(timezone.utc)`` at call time; ``0.0`` when
        `launch_time` is ``None``).

    Notes
    -----
    Only ``running``/``pending`` are queried -- the LIVE fleet, and what
    ``fleet_teardown.py --terminate`` reads to decide what to kill. The
    `tag_prefix` filter is applied SERVER-SIDE (EC2 tag filters accept a
    trailing ``*``), so this never lists the whole account, and re-checked
    CLIENT-SIDE so a regression there still cannot let a sibling experiment's
    instances leak in. A region that raises (no credentials, disabled region,
    throttle) is logged and skipped, so one bad region cannot hide the rest.
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

    Never empty: empty `rows` render an explicit "no scaling-* instances found"
    line, so an empty fleet and a broken query read differently to the operator.
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
    """Print the live fleet table; always returns ``0``.

    No flags: `fleet_rows`'s defaults cover every region this study could have
    provisioned in, and it logs and skips a region that fails to describe.
    """
    parser = argparse.ArgumentParser(
        description="Read-only listing of the scaling study's live EC2 fleet."
    )
    parser.parse_args(argv)
    print(format_fleet_table(fleet_rows()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
