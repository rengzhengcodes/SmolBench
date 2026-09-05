"""Shared machinery for the ``statistical_analyses.ipynb`` cell tests.

``tests/tooling/test_analysis_stats.py`` exercises the analysis MODULES that
notebook imports. Its ``test_stats_notebook_*`` siblings exercise the code the
notebook implements INLINE: sections 0, 7 and 8 define an archive reader, a
posterior-power classifier and a set of flip-rate estimators that live nowhere
else in the tree, so nothing else in the suite can catch them drifting from the
live modules they are supposed to agree with.

Each test pulls one cell's source out of the ``.ipynb`` by a stable needle and
``exec``s it, the same way ``tests/deduction/test_postcutoff_docs.py`` already
does for ``is_mathlib_cell``. Nothing here executes the notebook: the cells
under test are pure, and the one that builds an S3 client is handed a stubbed
``_aws.fresh_client`` so no AWS call is possible.

Not named ``test_*`` on purpose -- it holds no tests and must not be collected.
"""

from __future__ import annotations

import json

from tests._paths import NOTEBOOKS

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"


def load_notebook() -> dict:
    """Parse ``statistical_analyses.ipynb``."""
    return json.loads(STATS_NB.read_text())


def cell_source(nb: dict, needle: str) -> str:
    """Return the source of the ONE cell containing `needle`.

    Cells are addressed by content, never by index: the notebook gains and
    loses cells, and an index-keyed test would silently start asserting about
    a different cell instead of failing.
    """
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])
