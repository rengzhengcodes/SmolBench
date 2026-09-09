"""List the scaling study's live EC2 fleet without changing it.

Importing needs no AWS SDK because boto3 is loaded only when a client is made.
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
    # Bootstrap by path because scripts/fleet is not a package.
    module = sys.modules.get(_CONFIG_MODULE_NAME)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            _CONFIG_MODULE_NAME, Path(__file__).resolve().parent / "_config.py")
        sys.modules[_CONFIG_MODULE_NAME] = module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


_config = _load_fleet_config()


def _default_client_factory(region: str) -> Any:
    """Build an EC2 client lazily for `region`."""
    import boto3

    return boto3.client("ec2", region_name=region)


def fleet_rows(
    regions: Sequence[str] = _config.REGION_TUPLE,
    tag_prefix: str = _config.SCALING_TAG_PREFIX,
    client_factory: Optional[Callable[[str], Any]] = None,
) -> list[dict]:
    """List every running or pending EC2 instance tagged for this study.

    Apply and re-check the tag prefix so another experiment cannot leak in.
    Failed regions are logged and skipped.

    Parameters
    ----------
    regions : Sequence[str], optional
        Regions to query.
    tag_prefix : str, optional
        Required experiment-tag prefix.
    client_factory : Optional[Callable[[str], Any]], optional
        Client factory, or the lazy default.

    Returns
    -------
    list[dict]
        Rows with exactly region/experiment_tag/lane/instance_id/instance_type/availability_zone/state/launch_time/age_hours, as ``format_fleet_table`` requires.
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
                    continue  # Guard against a mismatched server-side filter.
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

    Empty rows render an explicit message so operators can distinguish them
    from a broken query.

    Parameters
    ----------
    rows : Sequence[dict]
        Rows from ``fleet_rows``.

    Returns
    -------
    str
        Fixed-width table.
    """
    if not rows:
        return f"fleet_status: no {_config.SCALING_TAG_PREFIX}* instances found in any region.\n"

    columns = ("lane", "instance_id", "instance_type", "availability_zone", "state", "age", "region")
    # ``fleet_rows`` guarantees every required key.
    formatted_rows = [
        {c: f"{row['age_hours']:.1f}h" if c == "age" else str(row[c]) for c in columns}
        for row in rows
    ]

    widths = {c: max([len(c), *(len(row[c]) for row in formatted_rows)]) for c in columns}
    return "\n".join([
        "  ".join(c.upper().ljust(widths[c]) for c in columns),
        "  ".join("-" * widths[c] for c in columns),
        *("  ".join(formatted[c].ljust(widths[c]) for c in columns)
          for formatted in formatted_rows),
    ]) + "\n"


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
