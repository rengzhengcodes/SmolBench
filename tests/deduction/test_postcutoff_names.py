"""Acceptance tests for scripts/deduction/postcutoff_names.py.

The script builds the provably post-cutoff mathlib4 declaration set between
two commits. These tests pin the parts that decide *what lands in the
artifact*: the namespace-aware Lean scanner, the deprecation/move filters,
the Bors ``(#NNNNN)`` commit-message parser, the PR-date provenance filter
and the JSON artifact shape.

Everything here is offline. The provenance tests drive the real script
against a throwaway *local* git repository built in ``tmp_path`` (so `git
clone`, `git blame` and the commit walk are genuinely exercised) with the
GitHub PR lookup replaced by an in-test stub; no test reaches the network.
"""

import importlib.util
import json
import subprocess
import sys

import pytest

from tests._paths import FIXTURES, SCRIPTS

_PATH = SCRIPTS / "deduction" / "postcutoff_names.py"
_SPEC = importlib.util.spec_from_file_location("postcutoff_names", _PATH)
pcn = importlib.util.module_from_spec(_SPEC)
# Register before exec_module: a module loaded by path is otherwise absent
# from sys.modules, which breaks dataclass field resolution under PEP 563.
sys.modules[_SPEC.name] = pcn
_SPEC.loader.exec_module(pcn)

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


#: Every name the fixture must yield -- and, by exact-set equality, nothing
#: else. Derived from the spec's scanner rules, not from the implementation.
EXPECTED_SAMPLE_NAMES = {
    "topLevelThm",
    "Alpha.inNamespace",
    "Alpha.protectedThm",          # protected keeps the namespace
    "RootLevel.escaped",           # _root_. drops the namespace
    "Alpha.Beta.nested",
    "Alpha.Beta.sectionScoped",    # `section Helper` adds no name component
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


def test_scanner_yields_exactly_the_expected_names(sample_decls):
    assert set(sample_decls) == EXPECTED_SAMPLE_NAMES


@pytest.mark.parametrize(
    "absent",
    [
        "Alpha.privateThm", "privateThm",          # private is excluded
        "commentedOutBlock", "Alpha.commentedOutBlock",
        "nestedCommented", "Alpha.nestedCommented",  # nested block comment
        "docCommented", "Alpha.docCommented",        # /-- doc comment -/
        "lineCommented", "Alpha.lineCommented",      # -- line comment
        "Alpha.Struct.theorem", "Alpha.theorem",     # indented structure field
    ],
)
def test_scanner_omits_names_it_must_never_emit(sample_decls, absent):
    assert absent not in sample_decls


def test_scanner_skips_unnamed_instances(sample_decls):
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
def test_scanner_records_kind_and_line(sample_decls, name, prefix, kind):
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
def test_scanner_marks_deprecated_declarations(sample_decls, name, expected):
    assert sample_decls[name].deprecated is expected


@pytest.mark.parametrize(
    "name, targets",
    [
        ("Alpha.oldName", {"newName", "Alpha.newName"}),
        ("Alpha.plainAlias", {"inNamespace", "Alpha.inNamespace"}),
        ("Alpha.iffBackward", {"someIff", "Alpha.someIff"}),
    ],
)
def test_alias_targets_carry_both_resolution_candidates(sample_decls, name, targets):
    assert set(sample_decls[name].alias_targets) == targets


def test_statement_is_the_normalised_source_line(sample_decls):
    assert sample_decls["topLevelThm"].statement == "theorem topLevelThm : True := trivial"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  theorem   foo :  True :=\ttrivial  ", "theorem foo : True := trivial"),
        ("", ""),
        ("   \t ", ""),
    ],
)
def test_normalise_line_collapses_whitespace(raw, expected):
    assert pcn.normalise_line(raw) == expected


def test_deprecation_excluded_names_covers_alias_targets(sample_decls):
    excluded = pcn.deprecation_excluded_names(sample_decls.values())
    # deprecated declarations and the targets of deprecated aliases go
    assert {"Alpha.deprecatedThm", "Alpha.oldName", "newName", "Alpha.newName",
            "Alpha.iffBackward", "someIff", "Alpha.someIff"} <= excluded
    # a NON-deprecated alias must not drag its (real, live) target out
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
def test_parse_pr_number(message, expected):
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


def _write_tree(root, files: dict) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def two_trees(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    _write_tree(old, {"Mathlib/A.lean": OLD_A})
    _write_tree(new, {"Mathlib/A.lean": NEW_A, "Mathlib/B.lean": NEW_B,
                      "Mathlib/C.lean": NEW_C})
    return old, new


def _select(old, new):
    old_decls = pcn.scan_tree(old)
    new_decls = pcn.scan_tree(new)
    old_lines = pcn.collect_normalised_lines(old)
    old_files = {p.relative_to(old).as_posix() for p in old.rglob("*.lean")}
    return pcn.select_postcutoff_names(new_decls, old_decls, old_lines, old_files)


def test_selection_keeps_only_genuinely_new_declarations(two_trees):
    kept, _ = _select(*two_trees)
    assert set(kept) == {"Dup.moved", "Fresh.genuinelyNew"}


def test_selection_drops_a_deprecated_alias_and_its_target(two_trees):
    kept, _ = _select(*two_trees)
    assert "Old.renamedOld" not in kept   # the alias itself
    assert "Old.reallyNew" not in kept    # the rename target: not new mathematics


def test_selection_drops_a_move_into_a_new_file(two_trees):
    """`New.moved` is a verbatim statement re-homed into a file new at old."""
    kept, _ = _select(*two_trees)
    assert "New.moved" not in kept


def test_selection_keeps_a_duplicate_statement_in_a_pre_existing_file(two_trees):
    """Both conjuncts matter: same text, but A.lean existed at old -> kept."""
    kept, _ = _select(*two_trees)
    assert "Dup.moved" in kept


def test_selection_keeps_a_new_file_whose_text_is_not_at_old(two_trees):
    """The move filter's negative arm: new file, novel statement -> kept."""
    kept, _ = _select(*two_trees)
    assert "Fresh.genuinelyNew" in kept


def test_selection_counts(two_trees):
    kept, counts = _select(*two_trees)
    assert list(counts) == ["n_old_decls", "n_new_decls", "n_name_diff",
                            "n_after_deprecated", "n_after_move"]
    assert counts == {"n_old_decls": 2, "n_new_decls": 7, "n_name_diff": 5,
                      "n_after_deprecated": 3, "n_after_move": 2}
    assert counts["n_after_move"] == len(kept)


def test_selection_is_sorted_by_name(two_trees):
    kept, _ = _select(*two_trees)
    assert list(kept) == sorted(kept)


def test_scan_tree_reports_paths_relative_to_the_root(two_trees):
    _, new = two_trees
    decls = pcn.scan_tree(new)
    assert decls["Fresh.genuinelyNew"].file_path == "Mathlib/C.lean"


def test_collect_normalised_lines_is_normalised(two_trees):
    old, _ = two_trees
    lines = pcn.collect_normalised_lines(old)
    assert "theorem moved : 1 = 1 := rfl" in lines
    assert "" not in lines


# ---------------------------------------------------------------------------
# End-to-end: provenance, PR-date filter, artifact
# ---------------------------------------------------------------------------
#
# These drive the real CLI against a throwaway local git repository, so the
# clone, worktree, blame and commit-metadata code all run for real. Only the
# single GitHub entry point (`fetch_pr_created_at`) is stubbed, which is also
# the assertion that no other code path talks to the network.

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

#: PR number -> GitHub ``created_at``. #200 was opened after the cutoff (its
#: declaration is post-cutoff); #150 was opened BEFORE the cutoff and merged
#: after it -- the case the whole PR-date filter exists for.
STUB_PRS = {200: "2026-06-10T09:00:00Z", 150: "2026-05-20T09:00:00Z"}


def _git(repo, *args, date=None):
    env = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
           "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    out = subprocess.run(["git", "-c", "commit.gpgsign=false", *args],
                         cwd=repo, env=env, capture_output=True, text=True)
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout.strip()


def _commit(repo, files: dict, message: str, date: str) -> str:
    _write_tree(repo, files)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message, date=date)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def fake_mathlib(tmp_path_factory):
    """A four-commit local stand-in for mathlib4.

    Returns ``(repo_path, shas)`` where ``shas`` maps a label to its commit:
    ``root`` (no Mathlib/ at all), ``old``, ``pr200``, ``pr150``, ``new``.
    """
    repo = tmp_path_factory.mktemp("fake_mathlib")
    _git(repo, "init", "-q", "-b", "master")
    shas = {}
    shas["root"] = _commit(repo, {"README.md": "no Mathlib here\n"},
                           "chore: root (#1)", "2026-04-01T00:00:00+0000")
    shas["old"] = _commit(repo, {"Mathlib/A.lean": REPO_A_OLD},
                          "feat: base (#100)", "2026-05-01T00:00:00+0000")
    shas["pr200"] = _commit(repo, {"Mathlib/B.lean": REPO_B_NEW},
                            "feat: after cutoff (#200)", "2026-06-10T00:00:00+0000")
    shas["pr150"] = _commit(repo, {"Mathlib/A.lean": REPO_A_LONG_LIVED},
                            "feat: long lived (#150)", "2026-06-11T00:00:00+0000")
    shas["new"] = _commit(repo, {"Mathlib/A.lean": REPO_A_NO_PR},
                          "wip: no pr number in this subject",
                          "2026-06-12T00:00:00+0000")
    return repo, shas


@pytest.fixture
def stub_pr_lookup(monkeypatch):
    """Replace the ONE GitHub entry point; count its calls."""
    calls = []

    def _fake(pr_number, token):
        calls.append(pr_number)
        return STUB_PRS.get(pr_number)

    monkeypatch.setattr(pcn, "fetch_pr_created_at", _fake)
    return calls


def _run(tmp_path, repo, old, new, out_name="postcutoff_names.json", extra=()):
    out = tmp_path / out_name
    argv = ["--old", old, "--new", new, "--target-date", TARGET_DATE,
            "--out", str(out), "--workdir", str(tmp_path / "wd"),
            "--repo-url", f"file://{repo}", "--jobs", "2", *extra]
    rc = pcn.main(argv)
    return rc, out


@pytest.fixture
def artifact(tmp_path, fake_mathlib, stub_pr_lookup, capsys):
    repo, shas = fake_mathlib
    rc, out = _run(tmp_path, repo, shas["old"], shas["new"])
    captured = capsys.readouterr().out
    assert rc == 0, captured
    return json.loads(out.read_text()), captured, shas, stub_pr_lookup


def test_artifact_top_level_shape(artifact):
    data, _, shas, _ = artifact
    assert set(data) == {"new_commit", "old_commit", "target_date", "method",
                         "n_new_decls", "n_old_decls", "n_postcutoff", "decls"}
    assert data["old_commit"] == shas["old"]
    assert data["new_commit"] == shas["new"]
    assert data["target_date"] == TARGET_DATE
    assert data["method"] == "name-set-difference+pr-opened-after-T"
    assert data["n_old_decls"] == 2      # Old.base, Old.moved
    assert data["n_new_decls"] == 5      # + Old.longLived, Old.noPr, New.afterCutoff
    assert data["n_postcutoff"] == len(data["decls"])


def test_pr_opened_before_the_target_date_is_dropped(artifact):
    """#150 was merged after the cutoff but OPENED before it: not post-cutoff."""
    data, _, _, _ = artifact
    assert "Old.longLived" not in data["decls"]


def test_declaration_from_a_pr_opened_after_the_target_is_kept(artifact):
    data, _, shas, _ = artifact
    entry = data["decls"]["New.afterCutoff"]
    assert entry["file_path"] == "Mathlib/B.lean"
    assert entry["introduced_commit"] == shas["pr200"]
    assert entry["pr_number"] == 200
    assert entry["pr_created_at"] == STUB_PRS[200]
    assert entry["reason"] == "pr-opened-after-T"


def test_commit_date_fallback_when_no_pr_number(artifact):
    data, _, shas, _ = artifact
    entry = data["decls"]["Old.noPr"]
    assert entry["introduced_commit"] == shas["new"]
    assert entry["pr_number"] is None
    assert entry["pr_created_at"] is None
    assert entry["reason"] == "commit-date"


def test_kept_set_is_exactly_the_post_cutoff_declarations(artifact):
    data, _, _, _ = artifact
    assert set(data["decls"]) == {"New.afterCutoff", "Old.noPr"}


def test_every_decl_entry_has_the_documented_keys(artifact):
    data, _, _, _ = artifact
    for entry in data["decls"].values():
        assert set(entry) == {"file_path", "introduced_commit", "pr_number",
                              "pr_created_at", "reason"}
        assert entry["reason"] in {"new-name", "pr-opened-after-T", "commit-date"}


def test_summary_reports_counts_at_every_step(artifact):
    _, captured, _, _ = artifact
    for line in ["postcutoff: n_old_decls=2",
                 "postcutoff: n_new_decls=5",
                 "postcutoff: n_name_diff=3",
                 "postcutoff: n_after_deprecated=3",
                 "postcutoff: n_after_move=3",
                 "postcutoff: n_with_provenance=3",
                 "postcutoff: n_postcutoff=2"]:
        assert line in captured, captured


def test_only_the_stubbed_entry_point_talks_to_github(artifact):
    _, _, _, calls = artifact
    # Two PR-numbered commits are reachable from the kept set; the third
    # declaration has no PR number and must cost no API call.
    assert sorted(calls) == [150, 200]


def test_rerun_is_byte_identical_and_hits_no_api(tmp_path, fake_mathlib,
                                                 stub_pr_lookup, capsys):
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


def test_empty_old_tree_is_refused_not_silently_diffed(tmp_path, fake_mathlib,
                                                       stub_pr_lookup):
    """An empty old tree would make every name look new -- refuse it."""
    repo, shas = fake_mathlib
    with pytest.raises(SystemExit) as excinfo:
        _run(tmp_path, repo, shas["root"], shas["new"], "never.json")
    assert "old" in str(excinfo.value).lower()


def test_token_is_never_printed(tmp_path, fake_mathlib, stub_pr_lookup, capsys):
    repo, shas = fake_mathlib
    secret = "ghp_THIS_MUST_NOT_BE_PRINTED_0123456789"
    rc, _ = _run(tmp_path, repo, shas["old"], shas["new"], "tok.json",
                 extra=["--github-token", secret])
    captured = capsys.readouterr()
    assert rc == 0
    assert secret not in captured.out
    assert secret not in captured.err


def test_rate_limit_stops_calling_and_still_writes_what_it_had(
    tmp_path, fake_mathlib, monkeypatch, capsys
):
    """A rate limit must degrade the run, not abort it or fake a result."""
    repo, shas = fake_mathlib
    calls = []

    def _limited(pr_number, token):
        calls.append(pr_number)
        raise pcn.RateLimitError(f"rate limited on #{pr_number}")

    monkeypatch.setattr(pcn, "fetch_pr_created_at", _limited)
    rc, out = _run(tmp_path, repo, shas["old"], shas["new"], "limited.json")
    captured = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out.read_text())
    # The PR-numbered declarations are dropped unresolved; the one with no PR
    # number never needed the API and survives on its commit date.
    assert set(data["decls"]) == {"Old.noPr"}
    assert len(calls) == 1, "must stop calling after the first rate limit"
    assert "rate_limited=2" in captured, captured


def test_parse_pr_number_is_what_drives_provenance(fake_mathlib):
    """The Bors parser and the real commit subjects agree."""
    repo, shas = fake_mathlib
    subject = _git(repo, "log", "-1", "--format=%s", shas["pr200"])
    assert pcn.parse_pr_number(subject) == 200
