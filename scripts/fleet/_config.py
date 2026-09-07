"""Constants and the by-path module loader shared across ``scripts/fleet``.

Every constant below is a VIEW on ``smolbench/evals/study_config.toml``
(via ``smolbench.evals.study_config``), never a separate declaration, so the
fleet family can't silently drift from that committed config or from each
other. This module reads no environment variable and imports no AWS SDK
(the ``study_config``/``smolbench`` import chain is stdlib-only), so
``fleet_status.py`` stays importable with neither, for analysis notebooks;
an override like ``EC2_REGIONS`` is applied by the consumer that reads it
(e.g. ``ec2.py``) at its own read time, not baked in here.

``scripts/fleet`` has no ``__init__.py``, so every module in it -- this one
included -- is loaded by file path (`load_module_by_path`, wrapped per-stem
as `load_fleet_module`) rather than a bare import; each consumer still
hand-bootstraps ``_config`` itself, since that function doesn't exist until
this module has run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Mapping

from smolbench.evals.study_config import load_study_config, roster_keys, tag_for


def load_module_by_path(name: str, path) -> ModuleType:
    """Execute `path` as a module under `name`, cached in ``sys.modules``.

    A cache hit returns the same object to every caller, so e.g. both
    supervisors reading ``load_fleet_module("policy")`` share one restart
    policy, not a copy each. Registered in ``sys.modules`` before
    ``exec_module``: PEP 563 ``@dataclass`` resolves its module through
    ``sys.modules[cls.__module__]``, so an unregistered module would raise
    ``AttributeError`` on ``policy.Decision``/``shards.Shard``'s own class body.
    """
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name!r} from {path}")
    sys.modules[name] = module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except BaseException:
        # Undo only the cache entry and re-raise, so a failed load can't hand
        # the next caller a half-executed module.
        sys.modules.pop(name, None)
        raise
    return module


def load_fleet_module(stem: str) -> ModuleType:
    """Load the sibling ``scripts/fleet/<stem>.py``, resolved against THIS file."""
    return load_module_by_path(
        f"smolbench_fleet_{stem}", Path(__file__).resolve().parent / f"{stem}.py"
    )

# Memoized on the resolved config path, so this is the same object every
# other consumer in the process holds; re-reading it below costs nothing.
_FLEET = load_study_config().fleet

#: Spot-capacity hunt regions, in try-order; read from ``[fleet].regions`` so
#: the fleet can't hunt a different region set than ``providers/ec2.py`` does.
#: ``ec2._DEFAULT_REGIONS`` is a deliberately different, third spelling (own
#: ``AWS_REGION`` first) for that module's standalone, non-fleet callers,
#: where closest-region-first is the right hunt order; out of scope here.
REGION_TUPLE: tuple[str, ...] = _FLEET.regions

#: `REGION_TUPLE`, comma-joined for the ``EC2_REGIONS`` environment value
#: (see ``lane_env.Lane.regions``, ``run_shards.py --regions``). Derived, not
#: declared, so the two forms can never disagree.
DEFAULT_REGIONS: str = ",".join(REGION_TUPLE)

#: Every lane's ``smolbench:experiment`` tag is
#: ``f"{SCALING_TAG_PREFIX}{spec_key}"`` (see ``lane_env.Lane.experiment_tag``).
#: Read from ``[fleet].tag_prefix``, not declared, so ``fleet_status``'s
#: server-side tag filter can't go blind to what ``run_fleet`` launched.
SCALING_TAG_PREFIX: str = _FLEET.tag_prefix

#: Default ``EC2_EXPERIMENT_TAG`` for a standalone, non-fleet run
#: (``run_study.py``'s own default, ``run_shards.py --tag``'s default). Kept
#: outside `SCALING_TAG_PREFIX`'s namespace so ``fleet_status.py`` never
#: lists, and ``fleet_teardown.py --terminate`` never reaches, a standalone
#: box; whoever launched it owns its teardown.
STANDALONE_TAG: str = _FLEET.standalone_tag

#: Every roster checkpoint's spec key, in ladder order. Read from the
#: committed config, not the induction driver -- a consumer of the roster,
#: not its owner -- so a rung added there reaches the fleet with no second
#: list to remember to update.
ROSTER_KEYS: tuple[str, ...] = roster_keys()

#: Spec key -> analysis tag, in ladder order. Built over `ROSTER_KEYS`
#: rather than aliasing the config's own ``roster.tags`` mapping, which is
#: only guaranteed to share the same key set, not the same order.
#: Read-only (``MappingProxyType``): an in-place mutation here would
#: silently change every other consumer's view of the roster.
ROSTER_TAGS: Mapping[str, str] = MappingProxyType(
    {key: tag_for(key) for key in ROSTER_KEYS}
)
