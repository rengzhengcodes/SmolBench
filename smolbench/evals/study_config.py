"""Load the committed study config (bucket, fleet regions, checkpoint roster).

Environment overrides are left to each consumer: ``providers/ec2.py`` freezes
``EC2_*`` at import time while ``results_store`` reads
``SMOLBENCH_RESULTS_S3`` at call time, so baking them in here would freeze
one timing model into the cached value. The cache is keyed on the resolved
config path so a ``tmp_path`` fixture never shares the committed file's
cache entry.
"""

from __future__ import annotations

import functools
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional

#: Resolved relative to this module's own file, not the caller's cwd.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("study_config.toml")


@dataclass(frozen=True)
class ResultsConfig:
    """The provisioned results bucket a study logs to by default.

    region describes THIS bucket only -- ``results_store.resolve_store`` must
    never apply it to a URI naming a different bucket.
    """

    bucket: str
    region: str
    base_prefix: str


@dataclass(frozen=True)
class FleetConfig:
    """Regions and experiment-tag vocabulary for the EC2 spot fleet.

    regions: try-order after whatever region the caller's own ``AWS_REGION``
    already names. standalone_tag sits outside `tag_prefix`'s namespace so
    fleet tooling never lists or terminates a standalone box.
    """

    regions: "tuple[str, ...]"
    tag_prefix: str
    standalone_tag: str


@dataclass(frozen=True)
class RosterConfig:
    """The family-ladder roster: which checkpoints exist and their tags.

    Both mappings are read-only (:class:`types.MappingProxyType`) so a
    consumer cannot mutate the shared cached config. `tags` is total over
    every `families` member and injective, validated at load.
    """

    families: "Mapping[str, tuple[str, ...]]"
    tags: "Mapping[str, str]"


@dataclass(frozen=True)
class StudyConfig:
    """The whole committed study config: results bucket, fleet, roster."""

    results: ResultsConfig
    fleet: FleetConfig
    roster: RosterConfig


def _require(mapping: dict, name: str, within: str = ""):
    """Return ``mapping[name]``, raising ``ValueError`` naming it if absent.

    A ``"[table]"``-spelled `name` reads as its unbracketed key but reports as
    the TOML table the reader has to add.
    """
    key = name.strip("[]")
    if key not in mapping:
        label = name if name.startswith("[") else repr(name)
        raise ValueError(
            f"study_config.toml{within} is missing the required {label}"
        )
    return mapping[key]


def _parse_study_config(data: dict) -> StudyConfig:
    """Build and validate a :class:`StudyConfig` from a parsed TOML document.

    Validates that every family member has a tag, every tag names a family
    member, and tags are unique; the ``ValueError`` message names the
    offending section, key, or checkpoint/tag.
    """
    # Presence checked before content, so a missing key surfaces as a
    # ValueError naming it rather than a KeyError three functions downstream.
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

    # tomllib preserves declaration order, which is the ladder order this
    # config promises downstream consumers.
    families = {name: tuple(rungs) for name, rungs in families_raw.items()}
    tags = dict(tags_raw)

    # Order matters: a family member missing its tag is checked before a tag
    # missing its family member, so an edit that trips both is reported for
    # the newly-untagged member first.
    all_members = [key for rungs in families.values() for key in rungs]

    # Without this, a missing tag surfaces only later as a KeyError out of
    # `tag_for`, wherever that checkpoint's tag is first asked for.
    for key in all_members:
        if key not in tags:
            raise ValueError(
                f"study_config.toml [roster.tags] is missing an entry for "
                f"{key!r}, which [roster.families] lists as a family member"
            )

    # A tag for a checkpoint no family lists would silently describe a rung
    # nothing ever runs.
    member_set = set(all_members)
    for key in tags:
        if key not in member_set:
            raise ValueError(
                f"study_config.toml [roster.tags] names {key!r}, which no "
                f"family in [roster.families] lists as a member"
            )

    # Two checkpoints sharing one analysis tag would write two lanes' results
    # into the same results directory, silently merging them.
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
    """Parse and validate `resolved_path`, memoized on the resolved path itself.

    Split out from :func:`load_study_config` so the cache key is always the
    resolved path, never the raw ``Path | None`` argument a caller passed in.
    """
    with resolved_path.open("rb") as fh:
        data = tomllib.load(fh)
    return _parse_study_config(data)


def load_study_config(path: "Optional[Path]" = None) -> StudyConfig:
    """Load and validate the committed study config.

    ``path=None`` (default) resolves to ``study_config.toml`` beside this
    module; tests pass an explicit `path` to load a scratch fixture. Cached:
    repeated calls resolving to the same file return the SAME object, so a
    consumer must never mutate it.
    """
    resolved = (path if path is not None else _DEFAULT_CONFIG_PATH).resolve()
    return _load_cached(resolved)


def roster_keys() -> "tuple[str, ...]":
    """Return every roster checkpoint's spec key, in ladder order.

    ``run_study.MODELS`` and ``power_analysis.MODELS``/``FAMILIES`` both
    derive their own iteration order from this.
    """
    return tuple(
        key for rungs in load_study_config().roster.families.values() for key in rungs
    )


def families() -> "Mapping[str, tuple[str, ...]]":
    """Return the ``{family_name: (spec_key, ...)}`` roster mapping, in ladder order."""
    return load_study_config().roster.families


def tag_for(key: str) -> str:
    """Return the short analysis tag for roster checkpoint `key`.

    Raises ``KeyError`` if `key` is not in the roster.
    """
    return load_study_config().roster.tags[key]
