"""List the family-ladder scaling study's live EC2 fleet, read-only.

Companion to ``run_fleet.py`` (launches and monitors) and
``fleet_teardown.py`` (terminates); both import it, as do analysis
notebooks. Importing needs no AWS SDK: boto3 is imported lazily inside
`_default_client_factory`, never at module scope, and tests inject a fake
through `client_factory`.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional, Sequence

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


def _default_client_factory(region: str) -> Any:
    """Build a boto3 EC2 client for `region` (boto3 imported here, lazily)."""
    import boto3

    return boto3.client("ec2", region_name=region)


def fleet_rows(
    regions: Sequence[str] = _config.REGION_TUPLE,
    tag_prefix: str = _config.SCALING_TAG_PREFIX,
    client_factory: Optional[Callable[[str], Any]] = None,
) -> list[dict]:
    """List every running or pending EC2 instance tagged for this study.
    `tag_prefix` is applied server-side (EC2 tag filters accept a trailing
    ``*``) and re-checked client-side, so a regression in one can't leak a
    sibling experiment's instances in. A region that raises (no
    credentials, disabled, throttled) is logged and skipped.

    Parameters
    ----------
    client_factory : Optional[Callable[[str], Any]], optional
        `None` uses `_default_client_factory`, the seam tests use to stub in a
        fake with no AWS SDK. Returns one dict per instance with exactly
        region/experiment_tag/lane/instance_id/instance_type/availability_zone/
        state/launch_time/age_hours -- `format_fleet_table` relies on this exact
        set.
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
        return f"fleet_status: no {_config.SCALING_TAG_PREFIX}* instances found in any region.\n"

    columns = ("lane", "instance_id", "instance_type", "availability_zone", "state", "age", "region")
    # No `.get` defaults: fleet_rows is the only producer and guarantees these keys.
    formatted_rows = [
        {c: f"{row['age_hours']:.1f}h" if c == "age" else str(row[c]) for c in columns}
        for row in rows
    ]

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
    """Print the live fleet table; always returns ``0``. No flags."""
    parser = argparse.ArgumentParser(
        description="Read-only listing of the scaling study's live EC2 fleet."
    )
    parser.parse_args(argv)
    print(format_fleet_table(fleet_rows()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
