"""Shared fleet constants and by-path loader.

Constants view committed study config so fleet consumers cannot drift. This
module has no AWS or environment dependency, keeping status importable offline.
Fleet scripts load by path because the directory is not a package.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Mapping

from smolbench.evals.study_config import load_study_config, roster_keys


def load_module_by_path(name: str, path: Path) -> ModuleType:
    """Execute `path` as a module under `name`, cached in ``sys.modules``.

    Cache before execution: dataclasses resolve their module through
    ``sys.modules`` during class creation.

    Parameters
    ----------
    name : str
        Cache key.
    path : Path
        Module file.

    Returns
    -------
    ModuleType
        Loaded module.
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
        # Remove failed loads so callers cannot receive a partial module.
        sys.modules.pop(name, None)
        raise
    return module


def load_fleet_module(stem: str) -> ModuleType:
    """Load the sibling ``scripts/fleet/<stem>.py``, resolved against THIS file."""
    return load_module_by_path(
        f"smolbench_fleet_{stem}", Path(__file__).resolve().parent / f"{stem}.py"
    )

# The loader cache gives every fleet consumer the same config object.
_STUDY = load_study_config()
_FLEET = _STUDY.fleet

#: Fleet region order from config, preventing divergence from EC2 provisioning.
REGION_TUPLE: tuple[str, ...] = _FLEET.regions

#: Comma-joined ``REGION_TUPLE``; derived so the forms cannot disagree.
DEFAULT_REGIONS: str = ",".join(REGION_TUPLE)

#: Configured tag prefix, shared so listing matches launched instances.
SCALING_TAG_PREFIX: str = _FLEET.tag_prefix

#: Standalone tag lies outside the fleet prefix, protecting its box from teardown.
STANDALONE_TAG: str = _FLEET.standalone_tag

#: Roster keys from config so new rungs need no second fleet list.
ROSTER_KEYS: tuple[str, ...] = roster_keys()

#: Validated, read-only spec-key-to-analysis-tag mapping.
ROSTER_TAGS: Mapping[str, str] = _STUDY.roster.tags
