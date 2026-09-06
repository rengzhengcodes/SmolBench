"""Docs and notebooks that state the post-cutoff contract (A5, A7).

Prose goes stale silently, so the load-bearing claims are pinned here: the
Mathlib-vs-dependency filter's actual predicate, the notebooks' JSON shape (an
edit script that stringifies `source` or drops outputs makes every later diff
unreviewable), and the attribution of the OLD study's 300/805/944 counts.
"""

import json
import re

import pytest

from tests._paths import NOTEBOOKS

STATS_NB = NOTEBOOKS / "statistical_analyses.ipynb"
LEAN_NB = NOTEBOOKS / "deduction" / "lean_eval.ipynb"
README = NOTEBOOKS / "deduction" / "README.md"

#: Counts that describe the OLD, pre-cutoff study ONLY.
#:
#: 13-20: ``300`` was removed from this set. It is the LIVE ``theorems.limit``
#: in `run_study.build_config` and the live `runner.EXPECTED_THEOREMS`, so
#: demanding a "pre-cutoff" marker beside it forced current documentation to
#: label its own configuration as history -- and, worse, made the guard read as
#: though 300 were settled as historical when it is the number a reader most
#: needs to trust. 805 (the retired ``novel_premises``/``val`` pool) and 944
#: (that pool's rendered cell count) remain: neither describes anything the
#: post-cutoff corpus produces.
OLD_STUDY_NUMBERS = re.compile(r"\b(805|944)\b")

def _paragraphs(text: str):
    """Yield ``(paragraph_text, [lines])`` for each blank-line-delimited block."""
    block: list[str] = []
    for line in text.splitlines():
        if line.strip():
            block.append(line)
        elif block:
            yield "\n".join(block), block
            block = []
    if block:
        yield "\n".join(block), block


def _unmarked_lines(text: str, pattern=None, *, marker: str = "pre-cutoff") -> list[str]:
    """Lines matching `pattern` whose enclosing PARAGRAPH lacks `marker`.

    13-20: the guard this replaces exempted a WHOLE CELL whenever the marker
    appeared anywhere in it, so a single historical aside licensed every number
    in a long cell -- and it never looked at the README's prose or at code
    cells at all. The paragraph is the right unit: strict enough that an
    unrelated section cannot vouch for a number, loose enough for real writing,
    where "300 theorems drawn from the\n`novel_premises`/`val` pool -- but 300
    is the\npre-cutoff study's pool size" legitimately puts the marker two
    lines below the number it qualifies.

    Returns the offending LINES (not indices), so a failure names the prose
    that has to change.
    """
    pattern = pattern or OLD_STUDY_NUMBERS
    offenders = []
    for paragraph, lines in _paragraphs(text):
        if marker in paragraph:
            continue
        offenders.extend(line.strip() for line in lines if pattern.search(line))
    return offenders


@pytest.fixture(scope="module")
def stats_nb() -> dict:
    if not STATS_NB.exists():
        pytest.skip("statistical_analyses.ipynb lives in the top stack slice")
    return json.loads(STATS_NB.read_text())


@pytest.fixture(scope="module")
def lean_nb() -> dict:
    return json.loads(LEAN_NB.read_text())


def _cell_source(nb: dict, needle: str) -> str:
    hits = [c for c in nb["cells"] if needle in "".join(c["source"])]
    assert len(hits) == 1, f"expected exactly one cell containing {needle!r}, got {len(hits)}"
    return "".join(hits[0]["source"])


@pytest.mark.parametrize("path", [STATS_NB, LEAN_NB], ids=lambda p: p.name)
def test_notebook_json_shape_survives_editing(path):
    """Round-trips byte-for-byte at indent=1, keeps list-of-lines `source`, no outputs.

    This is the recipe any edit script must use. A whole-file renormalization
    (or a `source` collapsed to one string) would bury the real change in noise.
    """
    if not path.exists():
        pytest.skip(f"{path.name} lives in a later stack slice")
    raw = path.read_text()
    nb = json.loads(raw)
    assert json.dumps(nb, indent=1, ensure_ascii=False) + "\n" == raw
    for i, cell in enumerate(nb["cells"]):
        assert isinstance(cell["source"], list), f"cell {i} source is not a list of lines"
        assert not cell.get("outputs"), f"cell {i} gained stored outputs"
        assert cell.get("execution_count") is None, f"cell {i} gained an execution_count"


def test_dependency_filter_covers_every_lake_package(stats_nb):
    """Std was renamed Batteries; the filter must key on `.lake/packages/`, not one name.

    A marker naming only `std` silently reclassified every Batteries theorem as
    Mathlib once mathlib4 switched, inflating the "Mathlib-only" population.
    """
    src = _cell_source(stats_nb, "def is_mathlib_cell")
    ns: dict = {}
    exec(compile(src, str(STATS_NB), "exec"), ns)
    is_mathlib_cell = ns["is_mathlib_cell"]

    for dep in (".lake/packages/std/Std/Data/List.lean",
                ".lake/packages/batteries/Batteries/Data/List.lean",
                ".lake/packages/aesop/Aesop/Frontend.lean",
                ".lake/packages/plausible/Plausible.lean"):
        assert is_mathlib_cell({"file_path": dep}) is False, dep
    for mathlib in ("Mathlib/Algebra/Group/Basic.lean", "Mathlib/Data/Nat/Defs.lean"):
        assert is_mathlib_cell({"file_path": mathlib}) is True, mathlib
    # A missing path is not evidence of a dependency; keep treating it as Mathlib.
    assert is_mathlib_cell({}) is True
    assert is_mathlib_cell({"file_path": None}) is True


def test_lean_eval_attributes_the_old_counts(lean_nb):
    """805 / 944 are the pre-cutoff study's numbers, in EVERY cell type.

    13-20: this scanned ``cell_type == "markdown"`` only, so a code cell could
    carry ``805`` freely -- and cell 4 did exactly that, calling
    ``iter_replay_passing("novel_premises", "val")`` against a split family the
    post-cutoff corpus does not have. It also exempted a whole cell whenever
    "pre-cutoff" appeared anywhere in it. Now every cell is scanned and the
    marker must sit within one line of the number.
    """
    offenders = {
        i: bad for i, c in enumerate(lean_nb["cells"])
        if (bad := _unmarked_lines("".join(c["source"])))
    }
    assert not offenders, (
        f"cells state 805/944 without marking them as the pre-cutoff study's "
        f"numbers: {offenders}")


def test_lean_eval_does_not_ask_for_the_retired_split_family():
    """13-14: the notebook must not name a split family the corpus lacks.

    The post-cutoff corpus has a single ``random`` family; cell 4 asked for
    ``novel_premises``, which is why running the notebook offline raised
    before it could validate a single prompt.
    """
    retired = re.compile(r"novel_premises")
    nb = json.loads(LEAN_NB.read_text())
    offenders = {
        i: bad for i, cell in enumerate(nb["cells"])
        if (bad := _unmarked_lines("".join(cell["source"]), retired))
    }
    assert not offenders, (
        f"cells name novel_premises outside a pre-cutoff paragraph: {offenders}")


def test_readme_data_sections_describe_the_post_cutoff_corpus():
    """13-14 / 13-20: the README's own prose is scanned, not exempt by construction.

    `test_postcutoff_docs` guarded the notebook's markdown cells and ONE README
    section, so the Data-bootstrap / pinned-300 / not-in-scope prose -- which
    described the Zenodo LeanDojo Benchmark 4 download that
    `run_study.build_config` now SystemExits on -- was outside every guard.
    """
    text = README.read_text()
    offenders = _unmarked_lines(text)
    assert not offenders, (
        "README states 805/944 without a nearby pre-cutoff marker:\n  "
        + "\n  ".join(offenders))
    # The retired corpus may still be NAMED -- pinned_theorems.json's recorded
    # derivation and the published S3 prefix both describe it -- but only from
    # a paragraph that says so, so a reader cannot mistake it for the corpus to
    # bootstrap today.
    retired = re.compile(r"zenodo|leandojo_benchmark_4", re.I)
    stale = _unmarked_lines(text, retired)
    assert not stale, (
        "README points at the retired pre-cutoff corpus from an unmarked "
        "paragraph:\n  " + "\n  ".join(stale))
    # ... and the section a reader follows today must name the builder.
    assert "build_postcutoff_corpus.py" in text


def test_readme_states_what_the_code_now_enforces():
    """The cutoff section must describe the enforced contract and point at Package B."""
    text = README.read_text()
    start = text.index("### Corpus date vs. model cutoffs")
    section = text[start:text.index("\n## ", start)]
    for token in ("require_postcutoff", "is_postcutoff_corpus", "ROSTER_LATEST_RELEASE",
                  "build_postcutoff_corpus.py"):
        assert token in section, f"{token!r} missing from the cutoff section"
    # The S3 layout section must not still promise the published study's prefix
    # for NEW runs.
    assert "deduction_postcutoff/runs" in text
