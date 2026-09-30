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
    #: Rungs per family; every family lists this many, so it is one number.
    n_rungs: int


@dataclass(frozen=True)
class StudyParams:
    """Collection parameters the driver and the analysis chain share."""

    n_replicates: int
    base_seed: int
    n_harmonics: int


@dataclass(frozen=True)
class AnalysisParams:
    """Analysis-wide statistical knobs."""

    seed: int
    alpha: float
    power_targets: "tuple[float, ...]"
    equivalence_deltas: "tuple[float, ...]"


@dataclass(frozen=True)
class StudyConfig:
    """The whole committed study config: results bucket, fleet, roster, study, analysis."""

    results: ResultsConfig
    fleet: FleetConfig
    roster: RosterConfig
    study: StudyParams
    analysis: AnalysisParams


def _require(mapping: dict, name: str, within: str = "") -> Any:
    """Return a required mapping value.

    Parameters
    ----------
    mapping : dict
        Mapping containing the required key.
    name : str
        Key to retrieve, optionally spelled as a TOML table.
    within : str, optional
        TOML section suffix included in an error message.

    Returns
    -------
    Any
        Value associated with `name`.
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
        Parsed TOML document.

    Returns
    -------
    StudyConfig
        Validated study configuration.
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

    dupes = sorted({key for key in all_members if all_members.count(key) > 1})
    if dupes:
        raise ValueError(
            f"study_config.toml [roster.families] lists {dupes} in more than one "
            "family; families must partition the roster"
        )

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

    # One rung count for the whole ladder: the contrast tiers assume it.
    rung_counts = {name: len(rungs) for name, rungs in families.items()}
    if len(set(rung_counts.values())) != 1:
        raise ValueError(
            f"study_config.toml [roster.families] lists unequal rung counts "
            f"{rung_counts}; every family must have the same number of rungs"
        )
    roster = RosterConfig(
        families=MappingProxyType(families),
        tags=MappingProxyType(tags),
        n_rungs=next(iter(rung_counts.values())),
    )

    study_raw = _require(data, "[study]")
    study = StudyParams(
        n_replicates=_positive_int(study_raw, "n_replicates", " [study]"),
        base_seed=_require(study_raw, "base_seed", " [study]"),
        n_harmonics=_positive_int(study_raw, "n_harmonics", " [study]"),
    )
    if not isinstance(study.base_seed, int) or study.base_seed < 0:
        raise ValueError(
            "study_config.toml [study] base_seed must be a non-negative integer"
        )

    analysis_raw = _require(data, "[analysis]")
    analysis = AnalysisParams(
        seed=_require(analysis_raw, "seed", " [analysis]"),
        alpha=_require(analysis_raw, "alpha", " [analysis]"),
        power_targets=_ascending_unit_floats(
            analysis_raw, "power_targets", " [analysis]"
        ),
        equivalence_deltas=_ascending_unit_floats(
            analysis_raw, "equivalence_deltas", " [analysis]"
        ),
    )
    if not 0 < analysis.alpha < 1:
        raise ValueError(
            f"study_config.toml [analysis] alpha must be in (0, 1), got {analysis.alpha}"
        )
    # The sizing tables print exactly two power columns.
    if len(analysis.power_targets) != 2:
        raise ValueError(
            "study_config.toml [analysis] power_targets must list exactly two levels, "
            f"got {list(analysis.power_targets)}"
        )

    return StudyConfig(
        results=results, fleet=fleet, roster=roster, study=study, analysis=analysis
    )


def _positive_int(mapping: dict, name: str, within: str) -> int:
    """Return `mapping[name]` after checking it is a positive integer.

    Parameters
    ----------
    mapping : dict
        TOML section holding the key.
    name : str
        Key to read.
    within : str
        TOML section suffix for the error message.

    Returns
    -------
    int
        The validated value.
    """
    value = _require(mapping, name, within)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(
            f"study_config.toml{within} {name} must be a positive integer, got {value!r}"
        )
    return value


def _ascending_unit_floats(
    mapping: dict, name: str, within: str
) -> "tuple[float, ...]":
    """Return `mapping[name]` as a non-empty, strictly ascending tuple of values in (0, 1).

    Parameters
    ----------
    mapping : dict
        TOML section holding the key.
    name : str
        Key to read.
    within : str
        TOML section suffix for the error message.

    Returns
    -------
    tuple[float, ...]
        The validated levels.
    """
    values = tuple(float(v) for v in _require(mapping, name, within))
    if (
        not values
        or any(not 0 < v < 1 for v in values)
        or list(values) != sorted(set(values))
    ):
        raise ValueError(
            f"study_config.toml{within} {name} must be a non-empty ascending list of "
            f"values in (0, 1), got {list(values)}"
        )
    return values


@functools.lru_cache(maxsize=None)
def _load_cached(resolved_path: Path) -> StudyConfig:
    """Parse and validate a resolved TOML path.

    Cache by resolved path so equivalent paths share one configuration.

    Parameters
    ----------
    resolved_path : Path
        Resolved TOML config path.

    Returns
    -------
    StudyConfig
        Parsed and validated study configuration.
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
        Config path to load.

    Returns
    -------
    StudyConfig
        Loaded and validated study configuration.
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


def n_rungs() -> int:
    """Return the rung count every family shares."""
    return load_study_config().roster.n_rungs


def study_params() -> StudyParams:
    """Return the ``[study]`` collection parameters."""
    return load_study_config().study


def analysis_params() -> AnalysisParams:
    """Return the ``[analysis]`` statistical knobs."""
    return load_study_config().analysis


def tag_for(key: str) -> str:
    """Return `key`'s short analysis tag.

    Parameters
    ----------
    key : str
        Roster checkpoint spec key.

    Returns
    -------
    str
        Short analysis tag for `key`.

    Raises
    ------
    KeyError
        If `key` is not in the roster.
    """
    return load_study_config().roster.tags[key]
