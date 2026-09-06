"""Constants -- and the by-path module loader -- shared across ``scripts/fleet``.

This file exists so the study's ``scaling-`` EC2 tag prefix and its default
region list have exactly ONE place the fleet family reads them from --
``run_fleet.py`` (and the modules it was split into, ``lane_env.py`` and
``supervisor.py``), ``fleet_status.py``, ``fleet_teardown.py`` (via
``fleet_status``, which it already imports) and ``run_shards.py`` all come
here -- instead of each spelling its own copy that can silently drift from
the others, the way
``fleet_status.SCALING_TAG_PREFIX``/``STATUS_REGIONS`` and the supervisor's
own ``DEFAULT_REGIONS``/``Lane.experiment_tag`` (then in ``run_fleet.py``,
today in ``lane_env.py``) did before this file existed, with only a comment
(not code) asserting they agreed.

No CONSTANT below is DECLARED here any more: every one is a VIEW on
``smolbench/evals/study_config.toml``, read through
``smolbench.evals.study_config``. That file is the study's single committed
audit surface for its results bucket, fleet regions/tag vocabulary and
21-checkpoint roster, and ``providers/ec2.py``, ``run_study.py`` and
``analysis/power_analysis.py`` already read from it; the fleet scripts used
to re-type the region list, the tag prefix and the standalone tag as their
own literals, with nothing keeping any of them equal to the TOML. Sourcing
them removes that whole class of drift: editing the TOML moves the fleet
with it.

The cost of that sourcing is ONE non-stdlib import --
``smolbench.evals.study_config``; everything else this module imports is
stdlib (``importlib.util``, ``sys`` and ``pathlib`` for `load_fleet_module`,
``types`` and ``typing`` for annotating the constants) -- and it is
deliberately a cheap one. ``study_config.py`` itself is stdlib-only (it
parses the TOML with ``tomllib``) and reads NO environment variable by
design, and the package
``__init__`` modules the import walks through on the way (``smolbench``, then
``smolbench.evals``, which re-exports ``smolbench.evals.quiz``) are
stdlib-only and environment-blind too. So nothing in that chain imports an
AWS SDK or touches ``os.environ``, and the only side effect of importing this
module is parsing one committed config file -- memoized on its resolved path,
so at most once per process however many fleet scripts load it.
``fleet_status.py`` in particular is documented as importable with no AWS
SDK, for analysis notebooks, and keeps that property. What the import DOES
newly require is that ``smolbench`` be importable at all -- which every
consumer already satisfies, because they run under the repo ``.venv``'s
editable install and the fleet supervisor already imports
``smolbench.evals.providers.ec2`` (in ``lane_env.py``) and
``smolbench.evals.results_store`` (in ``supervisor.py``) at module scope.

This module stays environment-blind for exactly the reason
``study_config.py`` does: ``EC2_REGIONS`` is applied by ``ec2.py`` at its own
read time, and folding that override in here would freeze one consumer's
notion of the environment into a value every other consumer reuses. The
values below are the DEFAULTS such an override falls back to, nothing more.

It is loaded BY FILE PATH, never a bare ``import _config`` or
``from _config import ...`` (see the ``_load_fleet_config`` loader each
consumer defines): ``scripts/fleet`` has no ``__init__.py`` -- it is not a
package -- and every module in it is already loaded under a private module
name by its callers (``tests/tooling/test_run_fleet.py``,
``supervisor._fleet_status_module``, ``fleet_teardown._fleet_status``), so a
bare import name would be ambiguous at best and simply absent from
``sys.path`` at worst.

That by-path load is now implemented ONCE, here, as `load_fleet_module` --
the generalisation of the ``_load_fleet_config`` snippet each consumer used
to copy for every sibling it needed. This file is its natural home because it
is the one module every other fleet module already bootstraps by hand, so
importing the loader costs a consumer nothing it was not already paying.
Two consequences worth spelling out:

- The hand-written ``_load_fleet_config`` bootstrap stays in each consumer,
  but ONLY for ``_config`` itself: this module cannot load itself through its
  own function, since that function does not exist until the module has been
  executed. Everything else -- ``policy.py``, ``shards.py``, ``lane_env.py``
  and ``supervisor.py`` -- goes through `load_fleet_module`, so there is one
  loader implementation instead of one per consumer.
- `load_fleet_module` adds only ``importlib.util``, ``sys`` and ``pathlib``,
  all stdlib. This module's documented properties -- no AWS SDK anywhere in
  its import chain, environment-blind, and no side effect on import beyond
  parsing one committed config file -- are unchanged, and
  ``fleet_status.py`` stays importable in an analysis notebook with no AWS
  SDK installed.

NOTE (scope): ``smolbench.evals.providers.ec2._DEFAULT_REGIONS`` is a THIRD,
deliberately DIFFERENT region spelling -- it puts the calling process's own
``AWS_REGION`` first (``",".join(dict.fromkeys((AWS_REGION, "us-east-1",
"us-east-2", "us-west-2")))``), which matters for that module's standalone,
non-fleet callers (e.g. a lone ``notebooks/induction/run_study.py`` launch),
where "closest region first" is the right hunt order. That spelling is out
of scope for this file; do not fold it in here.

Every fleet script now reads these from here: ``fleet_status.py``
(``SCALING_TAG_PREFIX``/``STATUS_REGIONS``, the latter from `REGION_TUPLE`),
``lane_env.py`` (its ``DEFAULT_REGIONS`` constant, ``TIER_REGIONS``,
``Lane.experiment_tag`` from `SCALING_TAG_PREFIX`, and its ``LANES`` table
and ``_drift_guard`` from `ROSTER_KEYS`/`ROSTER_TAGS`), ``run_shards.py``
(via its own ``_load_fleet_config``: `SCALING_TAG_PREFIX` for
``refuse_fleet_prefix_tag`` and `STANDALONE_TAG` for its ``--tag`` default)
and ``fleet_teardown.py`` (transitively, through ``fleet_status``).
``run_fleet.py`` and ``supervisor.py`` read none of these constants
directly: they take the roster and the per-lane environment from
``lane_env.py``, which is the point of the split.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Mapping

from smolbench.evals.study_config import load_study_config, roster_keys, tag_for


def load_fleet_module(stem: str) -> ModuleType:
    """Load ``scripts/fleet/<stem>.py`` by file path, cached in ``sys.modules``.

    Parameters
    ----------
    stem : str
        The sibling module's file stem, without ``.py`` -- e.g. ``"policy"``
        or ``"shards"``. Resolved against THIS file's directory, so it does
        not matter what working directory the calling script was launched
        from.

    Returns
    -------
    types.ModuleType
        The loaded module, registered in ``sys.modules`` under
        ``f"smolbench_fleet_{stem}"``. Every caller in a process therefore
        gets the SAME object: ``supervisor`` and ``run_shards`` both reading
        ``load_fleet_module("policy")`` share one policy module, which is the
        whole point of having one restart policy rather than two copies (and
        ``run_fleet`` and ``supervisor`` likewise share one ``lane_env``, so
        there is one roster per process).

    Raises
    ------
    ImportError
        If ``importlib`` produces no spec or no loader for the path -- the
        file exists but is not something it knows how to execute. Raised
        explicitly rather than letting ``module_from_spec`` fail on ``None``
        with an opaque ``AttributeError``.
    FileNotFoundError
        If ``scripts/fleet/<stem>.py`` does not exist. Note that this does NOT
        come out as an ``ImportError``: ``spec_from_file_location`` builds a
        perfectly good spec for a path that is not there, and the failure
        surfaces later, from ``exec_module``, when the loader tries to read
        the source.
    Exception
        Anything the loaded module itself raises while executing is
        propagated unchanged, after the half-initialised module is removed
        from ``sys.modules`` so a later call retries a clean load instead of
        handing out a partially executed module.

    Notes
    -----
    The module object is registered in ``sys.modules`` BEFORE
    ``exec_module`` runs, not after. That ordering is load-bearing, not
    tidiness: under PEP 563 (``from __future__ import annotations``, which
    every module here uses) ``@dataclass`` resolves a class's module through
    ``sys.modules[cls.__module__]``, so a dataclass defined in a module that
    is not yet registered raises ``AttributeError`` during its own class
    body. ``policy.Decision`` is exactly such a dataclass. The existing
    ``_load_fleet_config`` bootstraps already do this; the ordering is
    preserved here rather than reinvented.

    Examples
    --------
    >>> policy = load_fleet_module("policy")
    >>> policy.classify_exit("InsufficientInstanceCapacity", True)
    'reclaim'
    """
    name = f"smolbench_fleet_{stem}"
    module = sys.modules.get(name)
    if module is not None:
        return module
    path = Path(__file__).resolve().parent / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load fleet module {stem!r} from {path}")
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module -- see Notes; a PEP 563 dataclass in the
    # module being executed looks itself up here while its class body runs.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        # Not a fallback: the error is re-raised untouched. Only the cache
        # entry is undone, so a failed load cannot leave a half-executed
        # module behind for the next caller to receive as a cache hit.
        sys.modules.pop(name, None)
        raise
    return module

# Read once, at import: `load_study_config` is memoized on the resolved config
# path, so this is the same object every other consumer in the process holds
# and re-reading it below costs nothing.
_FLEET = load_study_config().fleet

#: The study's default spot-capacity hunt regions, in try-order -- read from
#: ``study_config.toml``'s ``[fleet].regions``, which is already a tuple and is
#: the config's OWN shape for this fact. Derived rather than declared so the
#: fleet cannot hunt a different region set than ``providers/ec2.py`` does.
REGION_TUPLE: tuple[str, ...] = _FLEET.regions

#: `REGION_TUPLE`, comma-joined. Derived FROM the tuple -- note the direction:
#: the tuple is the config's own shape for the region list, and this string is
#: merely the RENDERING that shape takes as an ``EC2_REGIONS`` environment
#: value (see ``lane_env.Lane.regions``, which falls back to this for every
#: tier but D, and ``run_shards.py --regions``). Deriving it here rather than
#: declaring it means the two forms can never disagree, and only the tuple has
#: to be kept faithful to the config.
DEFAULT_REGIONS: str = ",".join(REGION_TUPLE)

#: Every fleet lane's ``smolbench:experiment`` EC2 tag is
#: ``f"{SCALING_TAG_PREFIX}{spec_key}"`` (see ``lane_env.Lane.experiment_tag``).
#: Read from ``[fleet].tag_prefix`` rather than declared, so this file and the
#: committed config cannot name two different fleet namespaces -- which would
#: make ``fleet_status``'s server-side tag filter blind to the boxes
#: ``run_fleet`` actually launched.
SCALING_TAG_PREFIX: str = _FLEET.tag_prefix

#: The default ``EC2_EXPERIMENT_TAG`` for a STANDALONE, non-fleet run -- both
#: ``notebooks/induction/run_study.py``'s own default and ``run_shards.py``'s
#: ``--tag`` default. Spelled in ``[fleet].standalone_tag`` deliberately
#: OUTSIDE `SCALING_TAG_PREFIX`'s namespace, so ``fleet_status.py``'s tag
#: filter never LISTS a standalone box and ``fleet_teardown.py --terminate``
#: can never TERMINATE one; whoever launched it owns its teardown. That is
#: also why it is a separate config key and not a derivation of the prefix.
#: Read from the config rather than declared because the driver already reads
#: it from there: two spellings would put a shard box under a tag no other
#: tool expects.
STANDALONE_TAG: str = _FLEET.standalone_tag

#: Every roster checkpoint's spec key, in ladder order (families in
#: ``[roster.families]`` declaration order, each family's rungs in the order
#: listed). Read from the committed config, NOT from the induction driver:
#: the driver is one more consumer of the roster, not its owner, so a rung
#: added to the config reaches the fleet without anyone remembering to touch
#: a second list.
ROSTER_KEYS: tuple[str, ...] = roster_keys()

#: Spec key -> analysis tag, in ladder order -- the same mapping
#: ``run_study.MODELS`` and ``power_analysis`` build, from the same file.
#: Built as a comprehension over `ROSTER_KEYS` rather than aliasing the
#: config's own ``roster.tags`` mapping, because that one is in
#: ``[roster.tags]`` declaration order: the loader guarantees the two share a
#: key SET, not a key ORDER, and ladder order is what downstream iteration
#: promises. Wrapped read-only (``types.MappingProxyType``) for the same
#: reason ``study_config`` wraps its own: this is a shared module-level
#: mapping, and a caller mutating it in place would silently change every
#: other consumer's view of the roster.
ROSTER_TAGS: Mapping[str, str] = MappingProxyType(
    {key: tag_for(key) for key in ROSTER_KEYS}
)
