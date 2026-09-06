"""The root README's claims about the tree, pinned against the tree itself.

Four of them: that the package map names every module it indexes AND names no
module the tree has lost, that the "Where do I go?" table points at the entry
points that exist today, that the Lean prose credits the backend that actually
runs, and that the test section's skip count matches the module those skips
come from.

The map in ``README.md`` calls itself "an annotated tree of the whole
repository ... this section is the map". A map is only useful if it is
complete: a module absent from it is a module a reader never learns exists,
and ``smolbench/deduction/lean/replbackend.py`` -- the module that actually
drives Lean -- was absent from it while every other module in that package was
listed. The converse is the same defect read backwards: ``sft.py`` was deleted
and stayed on the map, so the map sent readers to a module that is gone. Both
directions are checked, and for three packages rather than one -- ``evals/``
and ``fleet/`` grew and split in later slices with nothing pinning their
blocks.

The prose tests here pin the other half of the same drift. Verification moved
off LeanDojo onto ``lean-interact``: ``smolbench/deduction/lean/verify.py``
imports ``lean_interact`` and describes its own contract as "unchanged from the
retired LeanDojo-backed version". ``lean-dojo`` is still a declared dependency
(corpus tracing and premise slicing use it, and it is what pins
``Requires-Python <3.13``), so the check below is deliberately narrow: it
forbids only the claim that lean-dojo VERIFIES, not every mention of it.

Deliberately importing nothing from ``smolbench.deduction.lean``: these are
text-only guarantees about documentation, and they must hold whether or not the
``lean`` extra is installed.
"""

from __future__ import annotations

import re

import pytest

from tests._paths import REPO_ROOT

README = REPO_ROOT / "README.md"


def _package_map() -> str:
    """Return the fenced ASCII tree under ``## Package layout``."""
    text = README.read_text()
    block = text[text.index("## Package layout"):]
    first = block.index("```")
    return block[first: block.index("```", first + 3)]


def _map_block(*path: str) -> str:
    """Return the sub-block of the package map at `path`, walked one level at a time.

    `path` is the sequence of stripped line prefixes to descend
    (``_map_block("smolbench/", "evals/")``); each block is its own line plus
    every following line indented deeper than it, i.e. exactly that directory's
    entries.

    Walked rather than searched, because directory names REPEAT across the map:
    ``evals/``, ``induction/`` and ``deduction/`` each name both a package and a
    test group, and ``induction/`` also names a notebooks directory. A one-shot
    search would silently pin the wrong block; descending from the top-level
    entry makes each anchor unique.

    Scoped for the same reason at file level: names like ``cli.py``,
    ``runner.py`` and ``_config.py`` recur across packages, so a whole-tree
    substring search would report a module as documented because some other
    package happens to ship a file of that name.

    Raises
    ------
    AssertionError
        If any path segment does not match exactly one line of the block it is
        looked up in -- an ambiguous anchor fails loudly instead of pinning the
        wrong block.
    """
    lines = _package_map().splitlines()
    for entry in path:
        starts = [i for i, line in enumerate(lines) if line.strip().startswith(entry)]
        assert len(starts) == 1, \
            f"{entry!r} matches {len(starts)} lines of {path}, need exactly 1"
        start = starts[0]
        depth = len(lines[start]) - len(lines[start].lstrip())
        end = start + 1
        while end < len(lines) and (
                not lines[end].strip()
                or len(lines[end]) - len(lines[end].lstrip()) > depth):
            end += 1
        lines = lines[start:end]
    return "\n".join(lines)


#: ``(map entry, directory, suffixes)`` for every package the map indexes
#: file by file. The map's own claim is that it is "an annotated tree of the
#: whole repository"; these are the blocks where that claim is checkable
#: mechanically, in BOTH directions (below).
#:
#: ``smolbench/evals/`` and ``scripts/fleet/`` are pinned alongside
#: ``deduction/lean/`` because both grew modules in later slices --
#: ``study_config.py``/``experiment.py`` and the ``run_fleet.py`` split into
#: ``_config``/``lane_env``/``supervisor``/``policy``/``shards`` -- and only
#: the lean block was pinned, so those additions could land unmapped.
#:
#: ``.toml`` counts as a mapped file, not as data: ``study_config.toml`` and
#: ``decontam_config.toml`` ARE the configuration those slices moved out of
#: code, so a reader who cannot find them in the map cannot find the roster or
#: the decontam constants at all.
MAPPED_PACKAGES = [
    (("smolbench/", "deduction/lean/"),
     REPO_ROOT / "smolbench" / "deduction" / "lean", (".py", ".toml")),
    (("smolbench/", "evals/"), REPO_ROOT / "smolbench" / "evals", (".py", ".toml")),
    (("scripts/", "fleet/"), REPO_ROOT / "scripts" / "fleet", (".py",)),
]


@pytest.mark.parametrize("entry, directory, suffixes", MAPPED_PACKAGES,
                         ids=["".join(p[0]) for p in MAPPED_PACKAGES])
def test_readme_map_names_every_module_in_a_mapped_package(entry, directory, suffixes):
    """Every file of a mapped package appears in that package's map block.

    ``__init__.py`` is excluded on purpose: it is package machinery, not one of
    the subsystems the map indexes. Non-recursive, so ``providers/`` and
    ``payloads/`` (which the map indexes as directories, one line each) are not
    dragged in.
    """
    block = _map_block(*entry)
    names = sorted(p.name for p in directory.iterdir()
                   if p.suffix in suffixes and not p.name.startswith("__"))
    assert names, f"no files found under {directory}"
    missing = [n for n in names if n not in block]
    assert not missing, f"README package map omits {missing} from the {entry} block"


@pytest.mark.parametrize("entry, directory, suffixes", MAPPED_PACKAGES,
                         ids=["".join(p[0]) for p in MAPPED_PACKAGES])
def test_readme_map_names_no_file_a_mapped_package_lost(entry, directory, suffixes):
    """The converse: every file NAMED in a package's block still exists in it.

    Omission is only half the drift. ``sft.py`` was deleted from
    ``smolbench/deduction/lean/`` and stayed in the map, sending a reader to a
    module that is gone -- which the omission check above cannot see. Scoped to
    the block for the same reason `_map_block` is scoped.
    """
    block = _map_block(*entry)
    named = sorted(set(re.findall(r"[\w./-]*[\w-]+\.(?:py|toml|yaml|sh)", block)))
    assert named, f"the {entry} block names no files at all"
    # Two rules, because a block line says two different kinds of thing.
    #
    # A BARE basename claims to be an entry of this package, and is resolved
    # recursively under it -- recursively, because a line may cite a module of
    # a sub-package the map indexes as a single line (``_aws.py``'s annotation
    # names ``providers/aws.py``). Scoping to the PACKAGE is what stops a
    # same-named module elsewhere in the repo from vouching for this block.
    #
    # A token WITH a separator is an explicit cross-reference (the fleet block
    # citing ``evals/study_config.toml``), so it is resolved against the whole
    # tree by path SUFFIX. Forbidding those outright would push accurate
    # cross-package references out of the map and into vaguer prose, which is
    # the opposite of what this map is for.
    def _resolves(name: str) -> bool:
        if "/" not in name:
            return any(directory.rglob(name))
        return any(p.as_posix().endswith(f"/{name}")
                   for p in REPO_ROOT.rglob(name.rsplit("/", 1)[1]))

    ghosts = [n for n in named if not _resolves(n)]
    assert not ghosts, f"README package map names {ghosts} under {entry}, not in {directory}"


def test_every_file_the_map_names_exists_somewhere_in_the_tree():
    """No line of the map may name a file the repository does not have.

    Weaker than the per-package converse above -- it matches on BASENAME
    anywhere in the tree -- but it covers the blocks that are indexed by job
    rather than file by file (``notebooks/``, ``scripts/results/``,
    ``tests/``), where a per-directory rule would not hold.
    """
    tree = _package_map()
    named = sorted(set(re.findall(r"[\w.-]+\.(?:py|toml|yaml|ipynb|sh|md)", tree)))
    assert named, "the package map names no files at all"
    present = {p.name for p in REPO_ROOT.rglob("*") if p.is_file()
               and ".venv" not in p.parts and ".git" not in p.parts}
    ghosts = [n for n in named if n not in present]
    assert not ghosts, f"README package map names files that do not exist: {ghosts}"


def test_readme_map_names_every_test_group():
    """The ``tests/`` block names every group directory the suite actually has.

    ``tests/analysis/`` landed with the analysis-driver work and the map never
    grew a line for it, so a reader looking for the driver tests was sent to
    four groups that do not hold them.
    """
    block = _map_block("tests/")
    groups = sorted(p.name for p in (REPO_ROOT / "tests").iterdir()
                    if p.is_dir() and not p.name.startswith(("_", ".")))
    assert groups, "no test group directories found"
    missing = [g for g in groups if f"{g}/" not in block]
    assert not missing, f"README package map omits test groups {missing}"


#: Where the "Where do I go?" table must send a reader for the two things
#: slices 3-4 moved. Both are behaviour changes a stale table hides: the
#: induction numbers now come from ONE driver rather than four scripts run by
#: hand, and the deduction reports read S3 themselves instead of a local tree
#: someone had to sync first.
WHERE_DO_I_GO_POINTERS = ["run_all.py", "--s3"]


def test_where_do_i_go_points_at_the_driver_and_the_s3_readers():
    """The reproduce-a-number row must name `run_all.py` and the ``--s3`` readers."""
    text = README.read_text()
    table = text[text.index("### Where do I go?"):]
    table = table[: table.index("\n## ")]
    row = [ln for ln in table.splitlines() if "Reproduce a published number" in ln]
    assert len(row) == 1, row
    missing = [p for p in WHERE_DO_I_GO_POINTERS if p not in row[0]]
    assert not missing, f"the reproduce-a-number row never mentions {missing}: {row[0]}"


def test_map_credits_lean_interact_for_verification():
    """The map's verify.py line must name the backend that actually runs.

    ``verify.py`` imports ``lean_interact`` and raises pointing at the ``lean``
    extra when it is absent; a map line reading "lean-dojo verification" sends
    an operator to install and debug the wrong package.
    """
    # Anchored on a token boundary: a bare ``"verify.py" in line`` also matches
    # ``nullverify.py``, which sits on its own line of the same block.
    verify_lines = [ln for ln in _map_block("smolbench/", "deduction/lean/").splitlines()
                    if re.search(r"(?<![A-Za-z0-9_])verify\.py", ln)]
    assert len(verify_lines) == 1, verify_lines
    assert "lean-interact" in verify_lines[0], verify_lines[0]
    assert "lean-dojo" not in verify_lines[0], verify_lines[0]


#: The three claims the tree contradicts. Narrow substrings, not "any mention
#: of lean-dojo": lean-dojo is still installed and still pins python<3.13, and
#: the README says both of those correctly.
LEAN_DOJO_VERIFICATION_CLAIMS = (
    "lean-dojo verification",
    "lean-dojo verify pass",
    "verification path's `lean-dojo`",
)


def test_readme_does_not_credit_lean_dojo_with_verification():
    text = README.read_text()
    offenders = [claim for claim in LEAN_DOJO_VERIFICATION_CLAIMS if claim in text]
    assert not offenders, f"README still credits lean-dojo with verifying: {offenders}"
    assert "lean-interact" in text


def test_pyproject_lean_comment_does_not_credit_lean_dojo_with_verification():
    """pyproject's own comment block contradicted the comment 6 lines below it.

    The comment above ``lean = [`` said verification needs lean-dojo; the
    comment on the ``lean-dojo`` entry says it stays ONLY for tracing and is no
    longer imported by the verifier. Both cannot be true.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text()
    header = text[text.index("# Lean theorem-proving eval"): text.index("lean = [")]
    assert "verification additionally needs lean-dojo" not in header, header
    assert "lean-interact" in header, header
    # The entry comment below is the authority this header must agree with.
    assert "`lean-dojo` stays ONLY because corpus tracing" in text


# --- the "Run the tests" section -------------------------------------------

S3_ARCHIVE_TESTS = REPO_ROOT / "tests" / "deduction" / "test_s3_archive.py"


def _s3_gated_test_count() -> int:
    """Count tests in ``test_s3_archive.py`` that depend on the ``s3_archive`` fixture.

    Transitive: the module defines its own ``tracked`` fixture on top of
    ``s3_archive``, and a test requesting only ``tracked`` skips just the same.
    """
    import ast

    tree = ast.parse(S3_ARCHIVE_TESTS.read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    gated = {"s3_archive"}
    for _ in range(len(functions)):          # closure; the chain is short
        for node in functions:
            params = {a.arg for a in node.args.args}
            if node.name.startswith("test_") or not (params & gated):
                continue
            gated.add(node.name)
    return sum(1 for node in functions
               if node.name.startswith("test_") and ({a.arg for a in node.args.args} & gated))


def test_readme_skip_count_matches_the_gated_module():
    """The README's "All N skips" must be the number of tests actually gated.

    The PASS count in that section cannot be pinned from inside the suite --
    any test that pinned it would change it -- so this pins the half that can
    be: adding a sixth archive gate must not leave the README claiming five.
    """
    text = README.read_text()
    stated = re.search(r"All (\d+) skips", text)
    assert stated, "README's test section no longer states a skip count"
    assert int(stated.group(1)) == _s3_gated_test_count()
    # and the same number must appear in the quoted pytest summary line
    summary = re.search(r"`\d+ passed, (\d+) skipped`", text)
    assert summary, "README's test section no longer quotes a pytest summary line"
    assert int(summary.group(1)) == int(stated.group(1))
    assert "test_s3_archive.py" in text and "SMOLBENCH_ARCHIVE_S3" in text
