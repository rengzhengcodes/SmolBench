"""Every reader and writer of a compliance label goes through `COMPLIANT`.

Structural, not textual: the checks below walk the AST, so prose that mentions
the label in a docstring is not mistaken for code that spells it.
"""

from __future__ import annotations

import ast

import pytest

from tests._paths import REPO_ROOT

#: Package roots whose modules read or write compliance labels.
SOURCE_ROOTS = ("smolbench", "scripts", "notebooks")

#: The one module allowed to spell the label as a literal: it defines it.
LABEL_HOME = REPO_ROOT / "smolbench" / "evals" / "quiz.py"


def _source_files():
    for root in SOURCE_ROOTS:
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path


def _parsed():
    return [(path, ast.parse(path.read_text())) for path in _source_files()]


@pytest.fixture(scope="module")
def modules():
    parsed = _parsed()
    assert len(parsed) > 20, f"only {len(parsed)} modules found; the walk is broken"
    return parsed


def test_the_compliant_label_is_spelled_only_where_it_is_defined(modules):
    """No second literal copy of `"compliant"`: a copy would silently diverge if the label ever changes."""
    offenders = []
    for path, tree in modules:
        if path == LABEL_HOME:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "compliant":
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, f'the literal "compliant" is spelled at {offenders}'


def test_the_statistics_notebook_delegates_compliance_entirely(modules):
    """The notebook delegates compliance entirely to `significance_report.py`; it must not grow a private census that could disagree with the published one."""
    import json

    from tests.tooling._notebook_cells import STATS_NB

    notebook = json.loads(STATS_NB.read_text())
    code = "\n".join("".join(cell["source"]) for cell in notebook["cells"]
                     if cell["cell_type"] == "code")
    for forbidden in ("compliance", "COMPLIANT", "NOT_ASSESSED"):
        assert forbidden not in code, \
            f"the notebook's CODE now mentions {forbidden!r}; it must delegate"

    # and the module it delegates to reads the constant, not a literal
    report = (REPO_ROOT / "notebooks" / "induction" / "analysis"
              / "significance_report.py").read_text()
    assert "from smolbench.evals.quiz import COMPLIANT" in report
