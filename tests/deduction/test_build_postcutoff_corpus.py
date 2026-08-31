"""Acceptance tests for scripts/deduction/build_postcutoff_corpus.py and the EC2 runbook.

Written from POSTCUTOFF_SPEC_B2 before the builder existed, so every expected
value here (split assignment, digest recipe, refusal messages, summary schema)
comes from the spec rather than from the implementation's behaviour.

The fixture under ``tests/fixtures/postcutoff/mini_export`` is a synthetic
LeanDojo-v2 export: three theorems, each present once in the ``random`` family
and once in ``novel_premises`` (in a DIFFERENT split), so the builder's
union-across-families + dedup path and its own re-splitting are both exercised.
Only ``Mini.postB`` survives (post-cutoff AND >= 2 traced tactics).
"""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys

import pytest

import smolbench.deduction.lean.corpus as corpus
from tests._paths import FIXTURES, SCRIPTS

_PATH = SCRIPTS / "deduction" / "build_postcutoff_corpus.py"
_SPEC = importlib.util.spec_from_file_location("build_postcutoff_corpus", _PATH)
build = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = build
_SPEC.loader.exec_module(build)

RUNBOOK = SCRIPTS / "deduction" / "trace_mathlib_ec2.sh"

EXPORT = FIXTURES / "postcutoff" / "mini_export"
NAMES = FIXTURES / "postcutoff" / "mini_names.json"

NEW_COMMIT = "2ca39e62989124794bd8405bb2e60805f63d37bc"
OLD_COMMIT = "69c8a067c87c2bb6ba583f03fbf46090564be370"
GITHUB_URL = "https://github.com/leanprover-community/mathlib4"
DATASET_NAME = "SmolBench post-cutoff mathlib4 (LeanDojo-v2 trace)"
NEW_DATE = "2026-08-30"
OLD_DATE = "2026-04-30"


def _build(out, export=EXPORT, names=NAMES, extra=()):
    """Run the builder's ``main`` and return ``<out>/leandojo_benchmark_4``."""
    rc = build.main([
        "--export", str(export), "--names", str(names), "--out", str(out),
        "--new-commit-date", NEW_DATE, "--old-commit-date", OLD_DATE, *extra,
    ])
    assert rc == 0
    return out / "leandojo_benchmark_4"


def _json(path):
    return json.loads(path.read_text())


@pytest.fixture
def built(tmp_path):
    """The fixture export, built once into ``tmp_path/out``."""
    return _build(tmp_path / "out")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_only_the_postcutoff_multi_tactic_theorem_survives(built):
    """Pre-cutoff and single-tactic post-cutoff rows are dropped; one row remains."""
    rows = _json(built / "random" / "val.json")
    assert [r["full_name"] for r in rows] == ["Mini.postB"]
    (row,) = rows
    assert row["postcutoff"] is True
    assert row["postcutoff_provenance"] == {
        "introduced_commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        # null pr_number/pr_created_at are LEGAL (B1's reason="commit-date"
        # path): absent KEYS are a refusal, null VALUES are not.
        "pr_number": None,
        "pr_created_at": None,
        "reason": "commit-date",
    }
    # Untouched pass-through fields survive the rewrite.
    assert row["commit"] == NEW_COMMIT
    assert row["file_path"] == "Mini/New.lean"
    assert row["theorem_statement"] == "theorem postB (n : ℕ) : G0 n"
    assert len(row["traced_tactics"]) == 3
    assert row["start"] == [20, 1]


def test_local_url_is_rewritten_to_github(built):
    """The export's LOCAL checkout path becomes the canonical GitHub URL."""
    assert _json(EXPORT / "metadata.json")["from_repo"]["url"] == "/mnt/data/mathlib4"
    (row,) = _json(built / "random" / "val.json")
    assert row["url"] == GITHUB_URL
    assert _json(built / "metadata.json")["from_repo"]["url"] == GITHUB_URL


def test_split_assignment_is_sha256_deterministic(built):
    """sha256(full_name)[:8] % 100 -> <80 train, <90 val, else test.

    ``Mini.postB`` hashes to bucket 89 -- val -- even though the export filed
    it under ``random/test``, so this also proves output splits are re-derived
    rather than inherited.
    """
    assert int(hashlib.sha256(b"Mini.postB").hexdigest()[:8], 16) % 100 == 89
    for kind in ("random", "novel_premises"):
        assert _json(built / kind / "train.json") == []
        assert _json(built / kind / "test.json") == []
        assert [r["full_name"] for r in _json(built / kind / "val.json")] == ["Mini.postB"]


def test_both_split_families_carry_the_same_rows(built):
    """novel_premises is a copy of random so every loader path works."""
    for split in ("train", "val", "test"):
        assert _json(built / "random" / f"{split}.json") == _json(
            built / "novel_premises" / f"{split}.json")


def test_metadata_block_matches_package_a_contract(built):
    """metadata.json copies the export and adds the `postcutoff` block."""
    meta = _json(built / "metadata.json")
    assert meta["dataset_name"] == DATASET_NAME
    assert meta["from_repo"] == {"url": GITHUB_URL, "commit": NEW_COMMIT}
    # creation_time / leandojo_version are copied through from the export.
    assert meta["leandojo_version"] == "2.0.0"
    assert meta["postcutoff"] == {
        "method": "name-set-difference+pr-opened-after-T",
        "new_commit": NEW_COMMIT,
        "new_commit_date": NEW_DATE,
        "old_commit": OLD_COMMIT,
        "old_commit_date": OLD_DATE,
        "target_date": "2026-06-03",
        "n_new_decls": 4,
        "n_old_decls": 2,
        "n_postcutoff_decls": 2,
    }


def test_premise_files_pass_through_byte_identical(built):
    """corpus.jsonl and traced_files.jsonl are copied unfiltered."""
    for name in ("corpus.jsonl", "traced_files.jsonl"):
        assert (built / name).read_bytes() == (EXPORT / name).read_bytes()


def test_build_summary_records_every_filter_step(tmp_path, built):
    """BUILD_SUMMARY.json sits beside the corpus with counts and the pool pin."""
    summary = _json(tmp_path / "out" / "BUILD_SUMMARY.json")
    assert summary["new_commit"] == NEW_COMMIT
    assert summary["old_commit"] == OLD_COMMIT
    assert summary["target_date"] == "2026-06-03"
    assert summary["min_traced_tactics"] == 2
    assert summary["counts"] == {
        "rows_read": 6,
        "unique_theorems": 3,
        "duplicates_dropped": 3,
        "postcutoff_named": 2,
        "with_min_tactics": 1,
        "written": 1,
        "per_split": {"train": 0, "val": 1, "test": 0},
    }
    assert summary["rows_per_source_file"] == {
        "random/train.json": 1, "random/val.json": 1, "random/test.json": 1,
        "novel_premises/train.json": 1, "novel_premises/val.json": 1,
        "novel_premises/test.json": 1,
    }
    assert summary["full_names"] == ["Mini.postB"]
    assert summary["sha256_of_sorted_full_names"] == (
        "d3ce8aa996d11342f560ea4afd0c4fc4650313b8187e6e8cd891df526fa99ca6")


# ---------------------------------------------------------------------------
# Digest recipe with more than one name (a 1-name pool cannot distinguish
# join separators) and a second occupied split
# ---------------------------------------------------------------------------


def _synthetic_export(root, names_and_tactics):
    """Write a minimal v2 export carrying ``{full_name: n_traced_tactics}``."""
    rows = []
    for i, (name, ntac) in enumerate(sorted(names_and_tactics.items())):
        rows.append({
            "url": "/mnt/data/mathlib4", "commit": NEW_COMMIT,
            "file_path": "Mini/New.lean", "full_name": name,
            "theorem_statement": f"theorem {name}", "start": [i + 1, 1], "end": [i + 2, 1],
            "traced_tactics": [
                {"tactic": f"s{j}", "annotated_tactic": [f"s{j}"],
                 "state_before": "⊢ A", "state_after": "no goals"}
                for j in range(ntac)],
        })
    for kind in ("random", "novel_premises"):
        (root / kind).mkdir(parents=True, exist_ok=True)
        (root / kind / "train.json").write_text(json.dumps(rows))
        for split in ("val", "test"):
            (root / kind / f"{split}.json").write_text("[]")
    (root / "metadata.json").write_text(json.dumps({
        "dataset_name": "synthetic", "creation_time": "2026-08-30 00:00:00.000000",
        "from_repo": {"url": "/mnt/data/mathlib4", "commit": NEW_COMMIT},
        "leandojo_version": "2.0.0"}))
    (root / "corpus.jsonl").write_text('{"path": "Mini/New.lean", "premises": []}\n')
    (root / "traced_files.jsonl").write_text('{"path": "Mini/New.lean"}\n')
    return root


def _names_json(path, decls):
    path.write_text(json.dumps({
        "new_commit": NEW_COMMIT, "old_commit": OLD_COMMIT,
        "target_date": "2026-06-03", "method": "name-set-difference+pr-opened-after-T",
        "n_new_decls": 4, "n_old_decls": 2, "n_postcutoff": len(decls),
        "decls": decls}))
    return path


def _decl(**over):
    d = {"file_path": "Mini/New.lean", "introduced_commit": "c" * 40,
         "pr_number": 1, "pr_created_at": "2026-06-10T09:15:00Z", "reason": "new-name"}
    d.update(over)
    return d


def test_two_survivor_pool_pins_the_digest_and_lands_in_two_splits(tmp_path):
    """sha256 over sorted full_names joined by "\\n" (audit_lean_pinning's recipe)."""
    export = _synthetic_export(tmp_path / "exp", {"Mini.postA": 2, "Mini.postB": 2})
    names = _names_json(tmp_path / "names.json",
                        {"Mini.postA": _decl(), "Mini.postB": _decl()})
    built = _build(tmp_path / "out", export=export, names=names)
    assert [r["full_name"] for r in _json(built / "random" / "train.json")] == ["Mini.postA"]
    assert [r["full_name"] for r in _json(built / "random" / "val.json")] == ["Mini.postB"]
    assert _json(built / "random" / "test.json") == []
    summary = _json(tmp_path / "out" / "BUILD_SUMMARY.json")
    assert summary["full_names"] == ["Mini.postA", "Mini.postB"]
    assert summary["counts"]["per_split"] == {"train": 1, "val": 1, "test": 0}
    assert summary["sha256_of_sorted_full_names"] == (
        "0b74faf6265d2bcc451cbdb928c96947f6162b201f85e529e5ba9b4fa7a87064")
    assert summary["sha256_of_sorted_full_names"] == hashlib.sha256(
        "\n".join(sorted(summary["full_names"])).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Refusals -- each starts from a REAL, buildable export and breaks exactly one
# thing, so none of them can pass merely because the input was unreadable.
# ---------------------------------------------------------------------------


def _real_export_copy(tmp_path):
    dst = tmp_path / "exp"
    shutil.copytree(EXPORT, dst)
    return dst


def test_refuses_when_export_commit_disagrees_with_names_json(tmp_path):
    """Commit mismatch -> SystemExit naming BOTH commits."""
    export = _real_export_copy(tmp_path)
    meta = _json(export / "metadata.json")
    meta["from_repo"]["commit"] = "f" * 40
    (export / "metadata.json").write_text(json.dumps(meta))
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", export=export)
    msg = str(exc.value)
    assert "f" * 40 in msg and NEW_COMMIT in msg


def test_refuses_when_a_selected_row_carries_a_foreign_commit(tmp_path):
    """A row traced at another commit cannot be part of this pool."""
    export = _real_export_copy(tmp_path)
    # Mini.postB occurs once per family; poison BOTH, so the refusal cannot be
    # dodged by whichever occurrence dedup happens to keep.
    for rel in ("random/test.json", "novel_premises/val.json"):
        rows = _json(export / rel)
        rows[0]["commit"] = "e" * 40
        (export / rel).write_text(json.dumps(rows))
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", export=export)
    assert "Mini.postB" in str(exc.value) and "e" * 40 in str(exc.value)


def test_refuses_when_provenance_key_is_missing(tmp_path):
    """Missing `introduced_commit` KEY -> SystemExit naming decl and key."""
    decls = _json(NAMES)["decls"]
    del decls["Mini.postB"]["introduced_commit"]
    names = _names_json(tmp_path / "names.json", decls)
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", names=names)
    assert "Mini.postB" in str(exc.value) and "introduced_commit" in str(exc.value)


def test_refuses_when_reason_is_null(tmp_path):
    """`reason` must be non-null; only pr_number/pr_created_at may be null."""
    decls = _json(NAMES)["decls"]
    decls["Mini.postB"]["reason"] = None
    names = _names_json(tmp_path / "names.json", decls)
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", names=names)
    assert "Mini.postB" in str(exc.value) and "reason" in str(exc.value)


def test_refuses_when_the_final_pool_is_empty(tmp_path):
    """Real export, names that match nothing in it -> SystemExit."""
    names = _names_json(tmp_path / "names.json", {"Mini.notPresent": _decl()})
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", names=names)
    assert "empty" in str(exc.value).lower()


def test_refuses_when_the_pool_is_emptied_by_the_tactic_floor(tmp_path):
    """A post-cutoff name with only 1 traced tactic is not a usable theorem."""
    names = _names_json(tmp_path / "names.json", {"Mini.postA": _decl()})
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", names=names)
    assert "empty" in str(exc.value).lower()


def test_refuses_when_a_required_export_file_is_missing(tmp_path):
    """Missing corpus.jsonl -> SystemExit naming the path."""
    export = _real_export_copy(tmp_path)
    (export / "corpus.jsonl").unlink()
    with pytest.raises(SystemExit) as exc:
        _build(tmp_path / "out", export=export)
    assert "corpus.jsonl" in str(exc.value)


# ---------------------------------------------------------------------------
# The built corpus loads through the real loader (Package A's API)
# ---------------------------------------------------------------------------


def test_built_corpus_metadata_reads_through_the_corpus_module(built, monkeypatch):
    """Raw metadata assertion -- independent of Package A having landed."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(built))
    corpus.reset_caches()
    try:
        assert corpus.metadata()["postcutoff"]["new_commit"] == NEW_COMMIT
        assert corpus.metadata()["from_repo"]["commit"] == NEW_COMMIT
    finally:
        corpus.reset_caches()


def test_built_corpus_satisfies_package_a_postcutoff_api(built, monkeypatch):
    """`is_postcutoff_corpus` + the per-row flag (Package A, corpus.py)."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(built))
    corpus.reset_caches()
    try:
        assert corpus.is_postcutoff_corpus() is True
        thms = corpus.load_split("random", "val")
        assert [t.full_name for t in thms] == ["Mini.postB"]
        assert all(t.postcutoff for t in thms)
        assert thms[0].url == GITHUB_URL and thms[0].has_proof
    finally:
        corpus.reset_caches()


# ---------------------------------------------------------------------------
# trace_mathlib_ec2.sh -- runbook; only --dry-run is executable on this box
# ---------------------------------------------------------------------------


def test_runbook_parses(tmp_path):
    """`bash -n` accepts the script."""
    r = subprocess.run(["bash", "-n", str(RUNBOOK)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _dry_run(tmp_path, extra=()):
    """Run the runbook's --dry-run under a bare environment: no elan, no lake,
    no aws, no python3.12, no network, no token, no root."""
    (tmp_path / "home").mkdir(exist_ok=True)
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path / "home")}
    r = subprocess.run(["bash", str(RUNBOOK), "--dry-run", *extra], cwd=tmp_path,
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def test_runbook_dry_run_prints_the_plan(tmp_path):
    """The plan names the pinned commit, deps, precondition and S3 destination."""
    out = _dry_run(tmp_path)
    for needle in (
        "2ca39e62989124794bd8405bb2e60805f63d37bc",
        "NUM_PROCS=48",
        "/mnt/data/cache",
        "/mnt/data/tmp",
        "lean-dojo-v2==1.0.9",
        "lake exe cache get",
        "generate_benchmark",
        "build_deps=True",
        "s3://smolbench-results-414266451290/deduction_postcutoff/corpus/",
    ):
        assert needle in out, f"missing {needle!r} in --dry-run plan:\n{out}"


def test_runbook_dry_run_writes_nothing(tmp_path):
    """--dry-run creates no file anywhere it would write for real.

    ``--workdir`` is pointed INSIDE tmp_path deliberately: the log, the two
    ``mkdir -p`` calls, the clone and the venv all live under $WORKDIR, which
    defaults to /mnt/data. Asserting emptiness of $HOME alone would pass even
    if every dry-run guard were removed, because the script never writes to
    $HOME in the first place.
    """
    workdir = tmp_path / "wd"
    _dry_run(tmp_path, ["--workdir", str(workdir)])
    assert not workdir.exists(), "dry-run created its workdir (log/mkdir not gated)"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["home"]
    assert list((tmp_path / "home").iterdir()) == []


def test_runbook_shims_the_hard_imports_and_pins_deps():
    """v2's utils/__init__ hard-imports deepspeed + pytorch_lightning."""
    src = RUNBOOK.read_text()
    assert "deepspeed" in src and "pytorch_lightning" in src
    for dep in ("loguru", "tqdm", "networkx", "lxml", "gitpython", "PyGithub",
                "python-dotenv", "toml"):
        assert dep in src, dep
    assert "--no-deps" in src
    assert "GITHUB_ACCESS_TOKEN" in src
