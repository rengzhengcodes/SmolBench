"""Pin the root README tree in both directions and its operational claims.

The checks hold with or without the ``lean`` extra, and index ``evals/``,
``fleet/``, and ``deduction/lean/`` because each can outgrow an unpinned map.
"""

from __future__ import annotations

import re
from pathlib import Path

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
    """Raise unless each path segment matches one line, avoiding a silently wrong block."""
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


#: Index these packages because their module sets can outgrow an unpinned map;
#: ``.toml`` is module configuration, not data.
MAPPED_PACKAGES = [
    (("smolbench/", "deduction/lean/"),
     REPO_ROOT / "smolbench" / "deduction" / "lean", (".py", ".toml")),
    (("smolbench/", "evals/"), REPO_ROOT / "smolbench" / "evals", (".py", ".toml")),
    (("scripts/", "fleet/"), REPO_ROOT / "scripts" / "fleet", (".py",)),
]


@pytest.mark.parametrize("entry, directory, suffixes", MAPPED_PACKAGES,
                         ids=["".join(p[0]) for p in MAPPED_PACKAGES])
def test_readme_map_names_every_module_in_a_mapped_package(
        entry: tuple[str, ...], directory: Path, suffixes: tuple[str, ...]) -> None:
    """Map files while deliberately excluding ``__init__.py`` and one-line-indexed subdirectories."""
    block = _map_block(*entry)
    names = sorted(p.name for p in directory.iterdir()
                   if p.suffix in suffixes and not p.name.startswith("__"))
    assert names, f"no files found under {directory}"
    missing = [n for n in names if n not in block]
    assert not missing, f"README package map omits {missing} from the {entry} block"


@pytest.mark.parametrize("entry, directory, suffixes", MAPPED_PACKAGES,
                         ids=["".join(p[0]) for p in MAPPED_PACKAGES])
def test_readme_map_names_no_file_a_mapped_package_lost(
        entry: tuple[str, ...], directory: Path, suffixes: tuple[str, ...]) -> None:
    """Mapped names still resolve within their package."""
    block = _map_block(*entry)
    named = sorted(set(re.findall(r"[\w./-]*[\w-]+\.(?:py|toml|yaml|sh)", block)))
    assert named, f"the {entry} block names no files at all"
    # Basenames resolve in-package; slash paths are explicit cross-package references.
    def _resolves(name: str) -> bool:
        if "/" not in name:
            return any(directory.rglob(name))
        return any(p.as_posix().endswith(f"/{name}")
                   for p in REPO_ROOT.rglob(name.rsplit("/", 1)[1]))

    ghosts = [n for n in named if not _resolves(n)]
    assert not ghosts, f"README package map names {ghosts} under {entry}, not in {directory}"


def test_every_file_the_map_names_exists_somewhere_in_the_tree() -> None:
    """This weaker basename-only check covers blocks indexed by job rather than file by file."""
    tree = _package_map()
    named = sorted(set(re.findall(r"[\w.-]+\.(?:py|toml|yaml|ipynb|sh|md)", tree)))
    assert named, "the package map names no files at all"
    present = {p.name for p in REPO_ROOT.rglob("*") if p.is_file()
               and ".venv" not in p.parts and ".git" not in p.parts}
    ghosts = [n for n in named if n not in present]
    assert not ghosts, f"README package map names files that do not exist: {ghosts}"


def test_readme_map_names_every_test_group() -> None:
    """The ``tests/`` block names every test group."""
    block = _map_block("tests/")
    groups = sorted(p.name for p in (REPO_ROOT / "tests").iterdir()
                    if p.is_dir() and not p.name.startswith(("_", ".")))
    assert groups, "no test group directories found"
    missing = [g for g in groups if f"{g}/" not in block]
    assert not missing, f"README package map omits test groups {missing}"


#: Point to the driver rather than four hand-run scripts, and to direct S3 readers
#: rather than a locally synced tree.
WHERE_DO_I_GO_POINTERS = ["run_all.py", "--s3"]


def test_where_do_i_go_points_at_the_driver_and_the_s3_readers() -> None:
    """The reproduce row names ``run_all.py`` and ``--s3`` readers."""
    text = README.read_text()
    table = text[text.index("### Where do I go?"):]
    table = table[: table.index("\n## ")]
    row = [ln for ln in table.splitlines() if "Reproduce a published number" in ln]
    assert len(row) == 1, row
    missing = [p for p in WHERE_DO_I_GO_POINTERS if p not in row[0]]
    assert not missing, f"the reproduce-a-number row never mentions {missing}: {row[0]}"


def test_map_credits_lean_interact_for_verification() -> None:
    """``verify.py`` names ``lean-interact``, not ``lean-dojo``."""
    # Boundaries avoid matching ``nullverify.py``.
    verify_lines = [ln for ln in _map_block("smolbench/", "deduction/lean/").splitlines()
                    if re.search(r"(?<![A-Za-z0-9_])verify\.py", ln)]
    assert len(verify_lines) == 1, verify_lines
    assert "lean-interact" in verify_lines[0], verify_lines[0]
    assert "lean-dojo" not in verify_lines[0], verify_lines[0]


# --- the "Run the tests" section -------------------------------------------

S3_ARCHIVE_TESTS = REPO_ROOT / "tests" / "deduction" / "test_s3_archive.py"


def _s3_gated_test_count() -> int:
    """Count tests gated by ``s3_archive``, including its ``tracked`` wrapper."""
    import ast

    tree = ast.parse(S3_ARCHIVE_TESTS.read_text())
    params = {node.name: {a.arg for a in node.args.args} for node in tree.body
              if isinstance(node, ast.FunctionDef)}
    gated = {"s3_archive"} | {name for name, args in params.items()
                              if not name.startswith("test_") and "s3_archive" in args}
    return sum(1 for name, args in params.items()
               if name.startswith("test_") and (args & gated))


def test_readme_skip_count_matches_the_gated_module() -> None:
    """README skip count equals the gated-test count."""
    text = README.read_text()
    stated = re.search(r"All (\d+) skips", text)
    assert stated, "README's test section no longer states a skip count"
    assert int(stated.group(1)) == _s3_gated_test_count()
    # The quoted pytest summary must repeat that count.
    summary = re.search(r"`\d+ passed, (\d+) skipped`", text)
    assert summary, "README's test section no longer quotes a pytest summary line"
    assert int(summary.group(1)) == int(stated.group(1))
    assert "test_s3_archive.py" in text and "SMOLBENCH_ARCHIVE_S3" in text
    # Do not pin the pass count here because a test that pins it changes that count.
