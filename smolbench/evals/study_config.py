"""Load the committed induction family-ladder study config.

``smolbench/evals/study_config.toml`` (parsed here) is the ONE place the
study's results bucket/region, fleet regions/tag vocabulary, and 21-checkpoint
roster are written down. Before this module existed, each of those facts was
duplicated by hand across ``providers/ec2.py`` (``_DEFAULT_REGIONS``),
``results_store.py`` (the bucket, spelled out in error messages and docs),
``notebooks/induction/run_study.py`` (``MODELS``), and
``notebooks/induction/analysis/power_analysis.py`` (a SECOND ``MODELS`` /
``FAMILIES`` pair, hand-kept in sync with the driver's by a runtime guard).
This module gives all four consumers one file to read instead.

Environment handling
---------------------
This module reads NO environment variables, by design. Two existing
consumers disagree about WHEN they read theirs: ``providers/ec2.py`` freezes
its ``EC2_*`` module constants at IMPORT time (its own module docstring's
"Env-read timing" section), so ``EC2_REGIONS`` must already be resolved
before ``ec2`` is imported anywhere in the process, while
``results_store.resolve_store`` reads ``SMOLBENCH_RESULTS_S3`` /
``SMOLBENCH_RESULTS_S3_REGION`` at CALL time, specifically so a notebook's
``load_dotenv(keys.env)`` -- which runs AFTER ``import smolbench`` -- still
takes effect.

If :func:`load_study_config` baked environment overrides into the
``StudyConfig`` it returns, the memoized (see below) return value would weld
those two timing models together: whichever import happened first would
freeze the environment as it stood at that moment into a value every later
caller reuses, silently disagreeing with a consumer that expects a call-time
read. Keeping this module environment-blind means each consumer applies its
own override at its own read time, exactly as it does today, and this module
only supplies the DEFAULT that override falls back to.

Caching
-------
:func:`load_study_config` is memoized with :func:`functools.lru_cache`, keyed
on the RESOLVED config path (not the raw argument), so that the ~21 call
sites spread across this study's driver, analysis script, and provider
modules parse the TOML file at most once per distinct path -- typically
exactly once, since almost every caller uses the default path. Keying on the
resolved path rather than the raw argument means ``Path("study_config.toml")``
and an equivalent absolute path passed by a different caller still share one
cache entry, and a test that points the loader at a ``tmp_path`` fixture
never collides with the committed file's cache entry.
"""

from __future__ import annotations

import functools
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional

#: The committed config, resolved relative to this module's own file so it is
#: found regardless of the caller's working directory.
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("study_config.toml")


@dataclass(frozen=True)
class ResultsConfig:
    """The provisioned results bucket a study logs to by default.

    Parameters
    ----------
    bucket : str
        S3 bucket name, provisioned by
        ``scripts/results/provision_results_bucket.py``.
    region : str
        Region `bucket` lives in. Describes THIS bucket only --
        ``results_store.resolve_store`` must never apply it to a URI naming
        a different bucket, which may live anywhere.
    base_prefix : str
        Namespace prefix under which every experiment's log keys are
        written; ``""`` means the log sits at the bucket root.
    """

    bucket: str
    region: str
    base_prefix: str


@dataclass(frozen=True)
class FleetConfig:
    """Regions and experiment-tag vocabulary for the EC2 spot fleet.

    Parameters
    ----------
    regions : tuple of str
        Default spot-capacity hunt regions, in try-order after whatever
        region a caller's own ``AWS_REGION`` already names.
    tag_prefix : str
        Prefix ``scripts/fleet/run_fleet.py`` gives each lane's
        ``EC2_EXPERIMENT_TAG`` (``f"{tag_prefix}{spec_key}"``), so
        fleet-management tooling can recognize fleet-owned boxes by tag.
    standalone_tag : str
        Default ``EC2_EXPERIMENT_TAG`` for a standalone (non-fleet) run,
        deliberately outside `tag_prefix`'s namespace so fleet tooling never
        lists or terminates a standalone box.
    """

    regions: "tuple[str, ...]"
    tag_prefix: str
    standalone_tag: str


@dataclass(frozen=True)
class RosterConfig:
    """The family-ladder roster: which checkpoints exist and their tags.

    Parameters
    ----------
    families : Mapping[str, tuple of str]
        ``{family_name: (spec_key, ...)}``, in ladder order: families in
        declaration order, each family's rungs in declaration order.
        Read-only (:class:`types.MappingProxyType`) so a consumer cannot
        mutate the shared cached config.
    tags : Mapping[str, str]
        ``{spec_key: analysis_tag}``, total over every key `families` lists
        and injective (validated at load; see :func:`load_study_config`).
        Also read-only.
    """

    families: "Mapping[str, tuple[str, ...]]"
    tags: "Mapping[str, str]"


@dataclass(frozen=True)
class StudyConfig:
    """The whole committed study config: results bucket, fleet, roster.

    Parameters
    ----------
    results : ResultsConfig
    fleet : FleetConfig
    roster : RosterConfig
    """

    results: ResultsConfig
    fleet: FleetConfig
    roster: RosterConfig


def _require_section(data: dict, section: str) -> dict:
    """Return ``data[section]``, raising ``ValueError`` naming `section` if absent."""
    if section not in data:
        raise ValueError(
            f"study_config.toml is missing the required [{section}] section"
        )
    return data[section]


def _require_key(section_data: dict, section: str, key: str):
    """Return ``section_data[key]``, raising ``ValueError`` naming `section`/`key` if absent."""
    if key not in section_data:
        raise ValueError(
            f"study_config.toml [{section}] is missing the required key {key!r}"
        )
    return section_data[key]


def _parse_study_config(data: dict) -> StudyConfig:
    """Build and validate a :class:`StudyConfig` from a parsed TOML document.

    Parameters
    ----------
    data : dict
        The document ``tomllib.loads``/``tomllib.load`` produced.

    Returns
    -------
    StudyConfig
        Fully validated: every declared section/key present, every family
        member has a tag, every tag names a family member, and tags are
        unique.

    Raises
    ------
    ValueError
        On any structural defect. The message names the offending
        section, key, or checkpoint/tag so the failure points straight at
        the line to fix in ``study_config.toml``.
    """
    # Phase 1: presence -- every declared section/key must exist before we
    # attempt to interpret its contents, so a missing key never surfaces as
    # a confusing KeyError three functions downstream.
    results_raw = _require_section(data, "results")
    results = ResultsConfig(
        bucket=_require_key(results_raw, "results", "bucket"),
        region=_require_key(results_raw, "results", "region"),
        base_prefix=_require_key(results_raw, "results", "base_prefix"),
    )

    fleet_raw = _require_section(data, "fleet")
    fleet = FleetConfig(
        regions=tuple(_require_key(fleet_raw, "fleet", "regions")),
        tag_prefix=_require_key(fleet_raw, "fleet", "tag_prefix"),
        standalone_tag=_require_key(fleet_raw, "fleet", "standalone_tag"),
    )

    roster_raw = _require_section(data, "roster")
    families_raw = _require_key(roster_raw, "roster", "families")
    tags_raw = _require_key(roster_raw, "roster", "tags")

    # Design: families_raw/tags_raw are themselves dicts (TOML's
    # "roster.families" / "roster.tags" dotted headers implicitly nest them
    # under "roster"); tomllib preserves declaration order in both, which is
    # exactly the ladder order this config promises downstream consumers.
    families = {name: tuple(rungs) for name, rungs in families_raw.items()}
    tags = dict(tags_raw)

    # Phase 2: cross-reference checks. Order matters for error clarity when a
    # single mutation trips more than one guard: a family member missing its
    # tag is checked before a tag missing its family member, so (for example)
    # a family edit that simultaneously orphans an old tag entry is reported
    # for the newly-untagged member first.
    all_members = [key for rungs in families.values() for key in rungs]

    # Guard: every family member has a `[roster.tags]` entry. Without this, a
    # missing tag would surface only much later as a KeyError out of
    # `tag_for`, on whatever call site first asks for that checkpoint's tag.
    for key in all_members:
        if key not in tags:
            raise ValueError(
                f"study_config.toml [roster.tags] is missing an entry for "
                f"{key!r}, which [roster.families] lists as a family member"
            )

    # Guard: every tag key names an actual family member. A tag for a
    # checkpoint no family lists would silently describe a rung nothing ever
    # runs -- catching it here is the only place that can name it.
    member_set = set(all_members)
    for key in tags:
        if key not in member_set:
            raise ValueError(
                f"study_config.toml [roster.tags] names {key!r}, which no "
                f"family in [roster.families] lists as a member"
            )

    # Guard: tags are unique. Two checkpoints sharing one analysis tag would
    # write two lanes' results into the same results directory, silently
    # merging them.
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
    fully resolved path (see that function's docstring), never the raw
    ``Path | None`` argument a caller passed in.
    """
    with resolved_path.open("rb") as fh:
        data = tomllib.load(fh)
    return _parse_study_config(data)


def load_study_config(path: "Optional[Path]" = None) -> StudyConfig:
    """Load and validate the committed study config.

    Parameters
    ----------
    path : pathlib.Path or None, optional
        Config file to load. ``None`` (the default) resolves to
        ``study_config.toml`` beside this module -- the committed file every
        production caller should use; tests pass an explicit `path` to load
        a scratch fixture instead.

    Returns
    -------
    StudyConfig
        Validated and cached: repeated calls with a path that resolves to
        the same file return the SAME object (see the module docstring's
        "Caching" section), so a consumer must never mutate it -- `roster`'s
        mapping fields are already read-only
        (:class:`types.MappingProxyType`) to make that mistake fail loudly
        instead of corrupting every other consumer's view.

    Raises
    ------
    ValueError
        The file is structurally invalid: see :func:`_parse_study_config`
        for the specific checks and their messages.
    FileNotFoundError
        `path` (or the default) does not exist.
    tomllib.TOMLDecodeError
        The file is not valid TOML.

    Notes
    -----
    Reads no environment variables; see the module docstring's "Environment
    handling" section for why that is deliberate. Pure I/O + parsing, no AWS
    calls.
    """
    resolved = (path if path is not None else _DEFAULT_CONFIG_PATH).resolve()
    return _load_cached(resolved)


def roster_keys() -> "tuple[str, ...]":
    """Return every roster checkpoint's spec key, in ladder order.

    Returns
    -------
    tuple of str
        All families' rungs concatenated in ``[roster.families]``
        declaration order -- the study's canonical order, which
        ``run_study.MODELS`` and ``power_analysis.MODELS``/``FAMILIES`` both
        derive their own iteration order from.
    """
    return tuple(
        key for rungs in load_study_config().roster.families.values() for key in rungs
    )


def families() -> "Mapping[str, tuple[str, ...]]":
    """Return the ``{family_name: (spec_key, ...)}`` roster mapping.

    Returns
    -------
    Mapping[str, tuple of str]
        Read-only view (:class:`types.MappingProxyType`) onto the cached
        config's roster; families and rungs both in ladder order.
    """
    return load_study_config().roster.families


def tag_for(key: str) -> str:
    """Return the short analysis tag for roster checkpoint `key`.

    Parameters
    ----------
    key : str
        A roster spec key (an ``EC2_DEPLOY_SPECS`` key); must be one of
        :func:`roster_keys`'s entries.

    Returns
    -------
    str
        The checkpoint's analysis tag, used in result directory names and
        figure legends.

    Raises
    ------
    KeyError
        `key` is not in the roster.
    """
    return load_study_config().roster.tags[key]
