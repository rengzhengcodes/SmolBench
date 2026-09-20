"""Offline acceptance tests for post-cutoff declaration selection.

Only GitHub PR lookup is stubbed; scanner, filters, git history, and artifact run for real.
"""

# pylint: disable=missing-function-docstring

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests._paths import FIXTURES, SCRIPTS, load_by_path

_PATH = SCRIPTS / "deduction" / "postcutoff_names.py"
pcn = load_by_path(_PATH, "postcutoff_names")

SAMPLE = FIXTURES / "postcutoff" / "sample.lean"


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sample_decls() -> dict:
    """`scan_lean_text` over the checked-in fixture, keyed by full name."""
    text = SAMPLE.read_text(encoding="utf-8")
    decls = pcn.scan_lean_text(text, "Mathlib/Sample.lean")
    return {d.full_name: d for d in decls}


#: Exact scanner expectations, derived from rules rather than implementation.
EXPECTED_SAMPLE_NAMES = {
    "topLevelThm",
    "Alpha.inNamespace",
    "Alpha.protectedThm",  # protected keeps the namespace
    "RootLevel.escaped",  # _root_. drops the namespace
    "Alpha.Beta.nested",
    "Alpha.Beta.sectionScoped",  # `section Helper` adds no name component
    "Alpha.Beta.afterSectionEnd",  # `end Helper` pops the section, not Beta
    "Alpha.inNoncomputableSection",
    "Alpha.namedInst",
    "Alpha.afterOpenIn",
    "Alpha.sameLineOpenIn",
    "Alpha.simpTagged",
    "Alpha.deprecatedThm",
    "Alpha.oldName",
    "Alpha.plainAlias",
    "Alpha.iffBackward",
    "Alpha.Struct",
    "Alpha.MyClass",
    "Alpha.Abbrev",
    "Alpha.Ind",
    "Alpha.universeDef",
    "rootAfterEnd",
}


def test_scanner_yields_exactly_the_expected_names(sample_decls: dict) -> None:
    assert set(sample_decls) == EXPECTED_SAMPLE_NAMES


@pytest.mark.parametrize(
    "absent",
    [
        "Alpha.privateThm",
        "privateThm",  # private is excluded
        "commentedOutBlock",
        "Alpha.commentedOutBlock",
        "nestedCommented",
        "Alpha.nestedCommented",  # nested block comment
        "docCommented",
        "Alpha.docCommented",  # /-- doc comment -/
        "lineCommented",
        "Alpha.lineCommented",  # -- line comment
        "Alpha.Struct.theorem",
        "Alpha.theorem",  # indented structure field
    ],
)
def test_scanner_omits_names_it_must_never_emit(
    sample_decls: dict, absent: str
) -> None:
    assert absent not in sample_decls


def test_scanner_skips_unnamed_instances(sample_decls: dict) -> None:
    """`instance : C` and `instance [I] : C` declare no scannable name."""
    instances = [d for d in sample_decls.values() if d.kind == "instance"]
    assert [d.full_name for d in instances] == ["Alpha.namedInst"]


def _line_of(prefix: str) -> int:
    """1-based line number of the first fixture line starting with `prefix`."""
    for i, line in enumerate(SAMPLE.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith(prefix):
            return i
    raise AssertionError(f"fixture has no line starting with {prefix!r}")


@pytest.mark.parametrize(
    "name, prefix, kind",
    [
        ("topLevelThm", "theorem topLevelThm", "theorem"),
        ("Alpha.Beta.nested", "lemma nested", "lemma"),
        ("Alpha.deprecatedThm", "theorem deprecatedThm", "theorem"),
        ("Alpha.oldName", "alias oldName", "alias"),
        ("Alpha.Struct", "structure Struct", "structure"),
        ("Alpha.MyClass", "class MyClass", "class"),
        ("Alpha.Abbrev", "abbrev Abbrev", "abbrev"),
        ("Alpha.Ind", "inductive Ind", "inductive"),
        ("Alpha.universeDef", "def universeDef", "def"),
        ("Alpha.sameLineOpenIn", "open Nat in theorem sameLineOpenIn", "theorem"),
    ],
)
def test_scanner_records_kind_and_line(
    sample_decls: dict, name: str, prefix: str, kind: str
) -> None:
    decl = sample_decls[name]
    assert decl.kind == kind
    assert decl.line == _line_of(prefix)
    assert decl.file_path == "Mathlib/Sample.lean"


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Alpha.deprecatedThm", True),
        ("Alpha.oldName", True),
        ("Alpha.iffBackward", True),
        ("Alpha.simpTagged", False),
        ("Alpha.plainAlias", False),
        ("topLevelThm", False),
    ],
)
def test_scanner_marks_deprecated_declarations(
    sample_decls: dict, name: str, expected: bool
) -> None:
    assert sample_decls[name].deprecated is expected


@pytest.mark.parametrize(
    "name, targets",
    [
        ("Alpha.oldName", {"newName", "Alpha.newName"}),
        ("Alpha.plainAlias", {"inNamespace", "Alpha.inNamespace"}),
        ("Alpha.iffBackward", {"someIff", "Alpha.someIff"}),
    ],
)
def test_alias_targets_carry_both_resolution_candidates(
    sample_decls: dict, name: str, targets: set[str]
) -> None:
    assert set(sample_decls[name].alias_targets) == targets


def test_statement_is_the_normalised_source_line(sample_decls: dict) -> None:
    assert (
        sample_decls["topLevelThm"].statement == "theorem topLevelThm : True := trivial"
    )


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  theorem   foo :  True :=\ttrivial  ", "theorem foo : True := trivial"),
        ("", ""),
        ("   \t ", ""),
    ],
)
def test_normalise_line_collapses_whitespace(raw: str, expected: str) -> None:
    assert pcn.normalise_line(raw) == expected


def test_deprecation_excluded_names_covers_alias_targets(sample_decls: dict) -> None:
    excluded = pcn.deprecation_excluded_names(sample_decls.values())
    # Deprecated declarations and alias targets go.
    assert {
        "Alpha.deprecatedThm",
        "Alpha.oldName",
        "newName",
        "Alpha.newName",
        "Alpha.iffBackward",
        "someIff",
        "Alpha.someIff",
    } <= excluded
    # A live alias must not exclude its target.
    assert "Alpha.plainAlias" not in excluded
    assert "Alpha.inNamespace" not in excluded
    assert "inNamespace" not in excluded
    assert "Alpha.simpTagged" not in excluded


# ---------------------------------------------------------------------------
# Bors / merge-queue PR-number parser
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message, expected",
    [
        ("chore(Basic/Logic/Basic): remove stale comment (#43225)", 43225),
        ("feat: thing (#123)\n\nlong body mentioning (#456)\n", 123),
        ("feat: thing (#123) \n", 123),
        ("feat: (#12) number in the middle of the subject", None),
        ("no pr number at all", None),
        ("bad number (#abc)", None),
        ("", None),
        ("body only\n\nsubjectless (#99)", None),
    ],
)
def test_parse_pr_number(message: str, expected: int | None) -> None:
    assert pcn.parse_pr_number(message) == expected


# ---------------------------------------------------------------------------
# Two-tree selection pipeline
# ---------------------------------------------------------------------------

OLD_A = """namespace Old

theorem stays : True := trivial

theorem moved : 1 = 1 := rfl

end Old
"""

NEW_A = """namespace Old

theorem stays : True := trivial

theorem moved : 1 = 1 := rfl

@[deprecated (since := "2026-06-01")]
alias renamedOld := reallyNew

theorem reallyNew : True := trivial

end Old

namespace Dup

theorem moved : 1 = 1 := rfl

end Dup
"""

NEW_B = """namespace New

theorem moved : 1 = 1 := rfl

end New
"""

NEW_C = """namespace Fresh

theorem genuinelyNew : 3 = 3 := rfl

end Fresh
"""


def _write_tree(root: Path, files: dict) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def two_trees(tmp_path: Path) -> tuple[Path, Path]:
    old, new = tmp_path / "old", tmp_path / "new"
    _write_tree(old, {"Mathlib/A.lean": OLD_A})
    _write_tree(
        new, {"Mathlib/A.lean": NEW_A, "Mathlib/B.lean": NEW_B, "Mathlib/C.lean": NEW_C}
    )
    return old, new


def _select(old: Path, new: Path) -> Any:
    old_decls, old_lines = pcn._scan_tree_state(old, "Mathlib")[:2]
    new_decls = pcn.scan_tree(new)
    old_files = {p.relative_to(old).as_posix() for p in old.rglob("*.lean")}
    return pcn.select_postcutoff_names(new_decls, old_decls, old_lines, old_files)


def test_selection_keeps_only_genuinely_new_declarations(
    two_trees: tuple[Path, Path],
) -> None:
    kept, _ = _select(*two_trees)
    assert set(kept) == {"Dup.moved", "Fresh.genuinelyNew"}


def test_selection_drops_a_deprecated_alias_and_its_target(
    two_trees: tuple[Path, Path],
) -> None:
    kept, _ = _select(*two_trees)
    assert "Old.renamedOld" not in kept  # the alias itself
    assert "Old.reallyNew" not in kept  # the rename target: not new mathematics


def test_selection_drops_a_move_into_a_new_file(two_trees: tuple[Path, Path]) -> None:
    """`New.moved` is a verbatim statement re-homed into a file new at old."""
    kept, _ = _select(*two_trees)
    assert "New.moved" not in kept


def test_selection_keeps_a_duplicate_statement_in_a_pre_existing_file(
    two_trees: tuple[Path, Path],
) -> None:
    """Both conjuncts matter: same text, but A.lean existed at old -> kept."""
    kept, _ = _select(*two_trees)
    assert "Dup.moved" in kept


def test_selection_keeps_a_new_file_whose_text_is_not_at_old(
    two_trees: tuple[Path, Path],
) -> None:
    """The move filter's negative arm: new file, novel statement -> kept."""
    kept, _ = _select(*two_trees)
    assert "Fresh.genuinelyNew" in kept


def test_selection_counts(two_trees: tuple[Path, Path]) -> None:
    kept, counts = _select(*two_trees)
    assert list(counts) == [
        "n_old_decls",
        "n_new_decls",
        "n_name_diff",
        "n_after_deprecated",
        "n_after_move",
    ]
    assert counts == {
        "n_old_decls": 2,
        "n_new_decls": 7,
        "n_name_diff": 5,
        "n_after_deprecated": 3,
        "n_after_move": 2,
    }
    assert counts["n_after_move"] == len(kept)


def test_selection_is_sorted_by_name(two_trees: tuple[Path, Path]) -> None:
    kept, _ = _select(*two_trees)
    assert list(kept) == sorted(kept)


def test_scan_tree_reports_paths_relative_to_the_root(
    two_trees: tuple[Path, Path],
) -> None:
    _, new = two_trees
    decls = pcn.scan_tree(new)
    assert decls["Fresh.genuinelyNew"].file_path == "Mathlib/C.lean"


# ---------------------------------------------------------------------------
# End-to-end provenance, PR-date filter, artifact.

TARGET_DATE = "2026-06-01"

REPO_A_OLD = """namespace Old

theorem base : True := trivial

theorem moved : 1 = 1 := rfl

end Old
"""

REPO_B_NEW = """namespace New

theorem afterCutoff : 2 = 2 := rfl

end New
"""

REPO_A_LONG_LIVED = REPO_A_OLD.replace(
    "end Old\n", "theorem longLived : 3 = 3 := rfl\n\nend Old\n"
)

REPO_A_NO_PR = REPO_A_LONG_LIVED.replace(
    "end Old\n", "theorem noPr : 4 = 4 := rfl\n\nend Old\n"
)

#: #200 opened after the cutoff; #150 merged after but opened before it.
STUB_PRS = {200: "2026-06-10T09:00:00Z", 150: "2026-05-20T09:00:00Z"}


def _git(repo: Path, *args: str, date: str | None = None) -> str:
    env = {
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(repo),
    }
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    out = subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout.strip()


def _commit(repo: Path, files: dict, message: str, date: str) -> str:
    _write_tree(repo, files)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message, date=date)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def fake_mathlib(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, str]]:
    """Four-commit local mathlib stand-in, including no-Mathlib root and PR cases."""
    repo = tmp_path_factory.mktemp("fake_mathlib")
    _git(repo, "init", "-q", "-b", "master")
    shas = {}
    shas["root"] = _commit(
        repo,
        {"README.md": "no Mathlib here\n"},
        "chore: root (#1)",
        "2026-04-01T00:00:00+0000",
    )
    shas["old"] = _commit(
        repo,
        {"Mathlib/A.lean": REPO_A_OLD},
        "feat: base (#100)",
        "2026-05-01T00:00:00+0000",
    )
    shas["pr200"] = _commit(
        repo,
        {"Mathlib/B.lean": REPO_B_NEW},
        "feat: after cutoff (#200)",
        "2026-06-10T00:00:00+0000",
    )
    shas["pr150"] = _commit(
        repo,
        {"Mathlib/A.lean": REPO_A_LONG_LIVED},
        "feat: long lived (#150)",
        "2026-06-11T00:00:00+0000",
    )
    shas["new"] = _commit(
        repo,
        {"Mathlib/A.lean": REPO_A_NO_PR},
        "wip: no pr number in this subject",
        "2026-06-12T00:00:00+0000",
    )
    return repo, shas


@pytest.fixture
def stub_pr_lookup(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Replace the one GitHub entry point; count its calls."""
    calls = []

    def _fake(pr_number: int, token: str | None) -> str | None:
        calls.append(pr_number)
        return STUB_PRS.get(pr_number)

    monkeypatch.setattr(pcn, "fetch_pr_created_at", _fake)
    return calls


def _run(
    tmp_path: Path,
    repo: Path,
    old: str,
    new: str,
    out_name: str = "postcutoff_names.json",
    extra: tuple[str, ...] = (),
) -> tuple[int, Path]:
    out = tmp_path / out_name
    argv = [
        "--old",
        old,
        "--new",
        new,
        "--target-date",
        TARGET_DATE,
        "--out",
        str(out),
        "--workdir",
        str(tmp_path / "wd"),
        "--repo-url",
        f"file://{repo}",
        "--jobs",
        "2",
        *extra,
    ]
    rc = pcn.main(argv)
    return rc, out


@pytest.fixture
def artifact(
    tmp_path: Path,
    fake_mathlib: tuple[Path, dict[str, str]],
    stub_pr_lookup: list[int],
    capsys: pytest.CaptureFixture[str],
) -> tuple[dict[str, Any], str, dict[str, str], list[int]]:
    repo, shas = fake_mathlib
    rc, out = _run(tmp_path, repo, shas["old"], shas["new"])
    captured = capsys.readouterr().out
    assert rc == 0, captured
    return json.loads(out.read_text()), captured, shas, stub_pr_lookup


def test_artifact_top_level_shape(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    data, _, shas, _ = artifact
    assert set(data) == {
        "new_commit",
        "old_commit",
        "target_date",
        "method",
        "n_new_decls",
        "n_old_decls",
        "n_postcutoff",
        "decls",
    }
    assert data["old_commit"] == shas["old"]
    assert data["new_commit"] == shas["new"]
    assert data["target_date"] == TARGET_DATE
    assert data["method"] == "name-set-difference+pr-opened-after-T"
    assert data["n_old_decls"] == 2  # Old.base, Old.moved
    assert data["n_new_decls"] == 5  # + Old.longLived, Old.noPr, New.afterCutoff
    assert data["n_postcutoff"] == len(data["decls"])


def test_pr_opened_before_the_target_date_is_dropped(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    """#150 was merged after the cutoff but opened before it: not post-cutoff."""
    data, _, _, _ = artifact
    assert "Old.longLived" not in data["decls"]


def test_declaration_from_a_pr_opened_after_the_target_is_kept(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    data, _, shas, _ = artifact
    entry = data["decls"]["New.afterCutoff"]
    assert entry["file_path"] == "Mathlib/B.lean"
    assert entry["introduced_commit"] == shas["pr200"]
    assert entry["pr_number"] == 200
    assert entry["pr_created_at"] == STUB_PRS[200]
    assert entry["reason"] == "pr-opened-after-T"


def test_commit_date_fallback_when_no_pr_number(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    data, _, shas, _ = artifact
    entry = data["decls"]["Old.noPr"]
    assert entry["introduced_commit"] == shas["new"]
    assert entry["pr_number"] is None
    assert entry["pr_created_at"] is None
    assert entry["reason"] == "commit-date"


def test_kept_set_is_exactly_the_post_cutoff_declarations(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    data, _, _, _ = artifact
    assert set(data["decls"]) == {"New.afterCutoff", "Old.noPr"}


def test_every_decl_entry_has_the_documented_keys(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    data, _, _, _ = artifact
    for entry in data["decls"].values():
        assert set(entry) == {
            "file_path",
            "introduced_commit",
            "pr_number",
            "pr_created_at",
            "reason",
        }
        assert entry["reason"] in {"new-name", "pr-opened-after-T", "commit-date"}


def test_summary_reports_counts_at_every_step(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    _, captured, _, _ = artifact
    for line in [
        "postcutoff: n_old_decls=2",
        "postcutoff: n_new_decls=5",
        "postcutoff: n_name_diff=3",
        "postcutoff: n_after_deprecated=3",
        "postcutoff: n_after_move=3",
        "postcutoff: n_with_provenance=3",
        "postcutoff: n_postcutoff=2",
    ]:
        assert line in captured, captured


def test_only_the_stubbed_entry_point_talks_to_github(
    artifact: tuple[dict[str, Any], str, dict[str, str], list[int]],
) -> None:
    _, _, _, calls = artifact
    # A no-PR declaration must cost no API call.
    assert sorted(calls) == [150, 200]


def test_rerun_is_byte_identical_and_hits_no_api(
    tmp_path: Path,
    fake_mathlib: tuple[Path, dict[str, str]],
    stub_pr_lookup: list[int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, shas = fake_mathlib
    rc1, out1 = _run(tmp_path, repo, shas["old"], shas["new"], "first.json")
    capsys.readouterr()
    stub_pr_lookup.clear()
    rc2, out2 = _run(tmp_path, repo, shas["old"], shas["new"], "second.json")
    captured = capsys.readouterr().out
    assert (rc1, rc2) == (0, 0)
    assert out1.read_bytes() == out2.read_bytes()
    assert stub_pr_lookup == [], "second run must be served from the PR cache"
    assert "postcutoff: github_api_calls=0" in captured, captured


def test_empty_old_tree_is_refused_not_silently_diffed(
    tmp_path: Path,
    fake_mathlib: tuple[Path, dict[str, str]],
    stub_pr_lookup: list[int],
) -> None:
    """Refuse an empty old tree because every name would otherwise look new."""
    repo, shas = fake_mathlib
    with pytest.raises(SystemExit) as excinfo:
        _run(tmp_path, repo, shas["root"], shas["new"], "never.json")
    assert "old" in str(excinfo.value).lower()


def test_token_is_never_printed(
    tmp_path: Path,
    fake_mathlib: tuple[Path, dict[str, str]],
    stub_pr_lookup: list[int],
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, shas = fake_mathlib
    secret = "ghp_THIS_MUST_NOT_BE_PRINTED_0123456789"
    rc, _ = _run(
        tmp_path,
        repo,
        shas["old"],
        shas["new"],
        "tok.json",
        extra=["--github-token", secret],
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert secret not in captured.out
    assert secret not in captured.err


def test_rate_limit_stops_calling_and_still_writes_what_it_had(
    tmp_path: Path,
    fake_mathlib: tuple[Path, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rate limit must degrade, not abort or fabricate results."""
    repo, shas = fake_mathlib
    calls = []

    def _limited(pr_number: int, token: str | None) -> None:
        calls.append(pr_number)
        raise pcn.RateLimitError(f"rate limited on #{pr_number}")

    monkeypatch.setattr(pcn, "fetch_pr_created_at", _limited)
    rc, out = _run(tmp_path, repo, shas["old"], shas["new"], "limited.json")
    captured = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out.read_text())
    # Unresolved PR declarations drop; no-PR declarations use commit date.
    assert set(data["decls"]) == {"Old.noPr"}
    assert len(calls) == 1, "must stop calling after the first rate limit"
    assert "rate_limited=2" in captured, captured


def test_parse_pr_number_is_what_drives_provenance(
    fake_mathlib: tuple[Path, dict[str, str]],
) -> None:
    """The Bors parser and the real commit subjects agree."""
    repo, shas = fake_mathlib
    subject = _git(repo, "log", "-1", "--format=%s", shas["pr200"])
    assert pcn.parse_pr_number(subject) == 200
