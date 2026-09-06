"""Every reader and writer of a compliance label goes through `COMPLIANT`.

``smolbench.evals.quiz`` stopped overloading ``None``: `COMPLIANT` is the
string ``"compliant"``, `NOT_ASSESSED` is ``"not-assessed"``, and ``Marks.load``
carries a documented shim mapping a STORED ``null`` (rows written before the
split) back to `COMPLIANT`. The shim is what makes the two dangerous habits
below silent rather than loud: a module that still asks ``if mark.compliance:``
or compares the field to ``None`` gets a plausible answer on every row, and the
answer is backwards for exactly the two outcomes the split exists to
distinguish.

``tests/evals/test_marks_io.py`` pins the datamodel and the shim; this pins the
CONSUMERS -- the analysis scripts the statistics notebook imports, the fleet and
results tooling, and the benchmark packages -- because the shim's retirement
(together with the legacy YAML tags) has to be safe to do, and it is only safe
if nothing depends on the ``None`` spelling.

Structural, not textual: the checks below walk the AST, so prose that mentions
``compliance: null`` in a docstring (several modules explain the shim, as they
should) is not mistaken for code that reads it.
"""

from __future__ import annotations

import ast

import pytest

from tests._paths import REPO_ROOT

#: Package roots whose modules read or write compliance labels.
SOURCE_ROOTS = ("smolbench", "scripts", "notebooks")

#: The one module allowed to spell the label as a literal: it is the module
#: that DEFINES it.
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


def test_no_module_reads_a_compliance_field_as_a_truth_value(modules):
    """``if mark.compliance:`` is the exact defect `COMPLIANT` was split out of.

    Under the old spelling that test read FALSE for a compliant mark and TRUE
    for an unassessed one -- backwards both ways. It would now read true for
    both, which is a different wrong answer, so the pattern stays forbidden
    rather than merely fixed.
    """
    offenders = []
    for path, tree in modules:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.If, ast.IfExp, ast.While)):
                continue
            test = node.test
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                test = test.operand
            named = (isinstance(test, ast.Attribute) and test.attr == "compliance") or \
                    (isinstance(test, ast.Name) and test.id == "compliance")
            if named:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, f"compliance read as a truth value at {offenders}"


def test_no_module_compares_a_compliance_field_to_none(modules):
    """``None`` is a STORED spelling, never a value the code should meet.

    ``Marks.load``'s shim translates it at the boundary, so any comparison to
    ``None`` further in is either dead (it can never be true) or a second,
    divergent copy of the shim.
    """
    offenders = []
    for path, tree in modules:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            left = node.left
            named = (isinstance(left, ast.Attribute) and left.attr == "compliance") or \
                    (isinstance(left, ast.Name) and left.id == "compliance")
            against_none = any(isinstance(c, ast.Constant) and c.value is None
                               for c in node.comparators)
            if named and against_none:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, f"compliance compared against None at {offenders}"


def test_the_compliant_label_is_spelled_only_where_it_is_defined(modules):
    """No second copy of the literal ``"compliant"``.

    A copy would keep working right up until the label changes, and then keep
    working -- wrongly -- in whichever module still carries the old spelling.
    The label has one home; everyone else imports it.
    """
    offenders = []
    for path, tree in modules:
        if path == LABEL_HOME:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "compliant":
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, f'the literal "compliant" is spelled at {offenders}'


def test_the_statistics_notebook_delegates_compliance_entirely(modules):
    """The notebook holds no compliance logic of its own -- section 3 imports it.

    Its significance-report section calls the live module
    (``notebooks/induction/analysis/significance_report.py``, which imports
    `COMPLIANT` and `NOT_ASSESSED` from the datamodel); the notebook itself must
    not grow a private census that could disagree with the published one.
    """
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
