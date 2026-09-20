"""Shared env-isolated path loaders for deduction tests."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from tests._paths import load_by_path


def load_env_isolated(
    path: Path,
    name: str,
    *,
    clear: Iterable[str] = (),
    forget_module: bool = False,
    **env: str,
) -> ModuleType:
    """Load `path` as module `name` with `os.environ` restored afterwards.

    `clear` drops ambient keys first because lane-tag imports guard on them;
    `env` applies during the import; `forget_module` pops ``sys.modules[name]``
    on exit so a same-named later load re-executes.
    """
    saved = dict(os.environ)
    for stale in clear:
        os.environ.pop(stale, None)
    os.environ.update(env)
    try:
        return load_by_path(path, name)
    finally:
        if forget_module:
            sys.modules.pop(name, None)
        os.environ.clear()
        os.environ.update(saved)
