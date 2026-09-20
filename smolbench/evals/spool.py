"""Shared deduction spool address resolution."""

import os

#: Default S3 key prefix for deduction runs.
DEDUCTION_SPOOL_PREFIX: str = "deduction_postcutoff/runs"


def spool_prefix() -> str:
    """Resolve the S3 key prefix used by deduction writers and readers.

    Resolving at call time lets a long-lived process observe a changed
    ``LEAN_SPOOL_PREFIX`` without retaining a stale archive destination.

    Returns
    -------
    str
        Override or default prefix, without trailing slash.
    """
    raw = os.environ.get("LEAN_SPOOL_PREFIX", "").strip()
    return raw.rstrip("/") if raw else DEDUCTION_SPOOL_PREFIX
