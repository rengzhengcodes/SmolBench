"""Load the committed study configuration.

Consumers resolve environment overrides at different times.
"""

from __future__ import annotations

import functools
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional

#: Resolved relative to this module's own file, not the caller's cwd.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("study_config.toml")


@dataclass(frozen=True)
class ResultsConfig:
    """Results bucket configuration; its region applies only to that bucket."""

    bucket: str
    region: str
    base_prefix: str


@dataclass(frozen=True)
class FleetConfig:
    """EC2 fleet configuration; standalone tags protect standalone boxes."""

    regions: "tuple[str, ...]"
    tag_prefix: str
    standalone_tag: str


@dataclass(frozen=True)
class RosterConfig:
    """Read-only roster and tags to protect cached configuration."""

    families: "Mapping[str, tuple[str, ...]]"
    tags: "Mapping[str, str]"


@dataclass(frozen=True)
class StudyConfig:
    """The whole committed study config: results bucket, fleet, roster."""

    results: ResultsConfig
    fleet: FleetConfig
    roster: RosterConfig


def _require(mapping: dict, name: str, within: str = "") -> Any:
    """Return a required mapping value.

    Parameters
    ----------
    mapping : dict
    name : str
    within : str, optional
    Returns
    -------
    Any
    """
    key = name.strip("[]")
    if key not in mapping:
        label = name if name.startswith("[") else repr(name)
        raise ValueError(f"study_config.toml{within} is missing the required {label}")
    return mapping[key]


def _parse_study_config(data: dict) -> StudyConfig:
    """Build and validate a TOML study configuration.

    Tags must cover family members, name only members, and remain unique.

    Parameters
    ----------
    data : dict
    Returns
    -------
    StudyConfig
    """
    # Report missing keys at the configuration boundary.
    results_raw = _require(data, "[results]")
    results = ResultsConfig(
        bucket=_require(results_raw, "bucket", " [results]"),
        region=_require(results_raw, "region", " [results]"),
        base_prefix=_require(results_raw, "base_prefix", " [results]"),
    )

    fleet_raw = _require(data, "[fleet]")
    fleet = FleetConfig(
        regions=tuple(_require(fleet_raw, "regions", " [fleet]")),
        tag_prefix=_require(fleet_raw, "tag_prefix", " [fleet]"),
        standalone_tag=_require(fleet_raw, "standalone_tag", " [fleet]"),
    )

    roster_raw = _require(data, "[roster]")
    families_raw = _require(roster_raw, "families", " [roster]")
    tags_raw = _require(roster_raw, "tags", " [roster]")

    # TOML declaration order is ladder order.
    families = {name: tuple(rungs) for name, rungs in families_raw.items()}
    tags = dict(tags_raw)

    all_members = [key for rungs in families.values() for key in rungs]

    for key in all_members:
        if key not in tags:
            raise ValueError(
                f"study_config.toml [roster.tags] is missing an entry for "
                f"{key!r}, which [roster.families] lists as a family member"
            )

    member_set = set(all_members)
    for key in tags:
        if key not in member_set:
            raise ValueError(
                f"study_config.toml [roster.tags] names {key!r}, which no "
                f"family in [roster.families] lists as a member"
            )

    # Unique tags prevent silent merging of two result lanes.
    seen_by_tag: "dict[str, str]" = {}
    for key, tag in tags.items():
        if tag in seen_by_tag:
            raise ValueError(
                f"study_config.toml [roster.tags] assigns tag {tag!r} to both "
                f"{seen_by_tag[tag]!r} and {key!r}; two checkpoints sharing "
                f"one analysis tag would put two lanes' results in one "
                f"analysis directory"
            )
        seen_by_tag[tag] = key

    roster = RosterConfig(
        families=MappingProxyType(families),
        tags=MappingProxyType(tags),
    )

    return StudyConfig(results=results, fleet=fleet, roster=roster)


@functools.lru_cache(maxsize=None)
def _load_cached(resolved_path: Path) -> StudyConfig:
    """Parse and validate a resolved TOML path.

    Cache by resolved path so equivalent paths share one configuration.

    Parameters
    ----------
    resolved_path : Path
    Returns
    -------
    StudyConfig
    """
    with resolved_path.open("rb") as fh:
        data = tomllib.load(fh)
    return _parse_study_config(data)


def load_study_config(path: "Optional[Path]" = None) -> StudyConfig:
    """Load and validate the study configuration.

    Cached configurations remain immutable because they are shared.

    Parameters
    ----------
    path : Optional[Path], optional
    Returns
    -------
    StudyConfig
    """
    resolved = (path if path is not None else _DEFAULT_CONFIG_PATH).resolve()
    return _load_cached(resolved)


def roster_keys() -> "tuple[str, ...]":
    """Return checkpoint keys in ladder order."""
    return tuple(
        key for rungs in load_study_config().roster.families.values() for key in rungs
    )


def families() -> "Mapping[str, tuple[str, ...]]":
    """Return roster families in ladder order."""
    return load_study_config().roster.families


def tag_for(key: str) -> str:
    """Return `key`'s short analysis tag.

    Parameters
    ----------
    key : str
    Returns
    -------
    str
    Raises
    ------
    KeyError
    """
    return load_study_config().roster.tags[key]
