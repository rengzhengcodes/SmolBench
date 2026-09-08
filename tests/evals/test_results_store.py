"""Replicate results store: local tree, S3 append-only log, env resolution, sync_down."""

import dataclasses
import hashlib
import io
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Self
import pytest
from botocore.exceptions import ClientError

from smolbench.evals import Mark, Marks, Numeric, _aws, provider, replicates
from smolbench.evals.quiz import COMPLIANT
from smolbench.evals import results_store as rs
from smolbench.evals.results_store import (
    LocalResultsStore, ReplicateAddress, S3ResultsStore, experiment_name,
    format_run_ts, parse_s3_uri, resolve_store, sync_down,
)

BUCKET = "smolbench-results-414266451290"
URI = f"s3://{BUCKET}"
TS1 = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)  # 20260810T193000Z
TS2 = datetime(2026, 8, 11, 4, 5, 6, tzinfo=timezone.utc)  # 20260811T040506Z
TAGS = {"gpt-oss-120b": "moe", "stub-model": "decode"}


def sample_marks(model: str = "stub-model", n: int = 2, score: int = 1) -> Marks:
    # Pinned date keeps equality and dumped bytes exact.
    marks = tuple(Mark(query=f"q{i}", answer=i, response=str(i), score=score,
                       compliance=COMPLIANT) for i in range(n))
    return Marks(model=model, marks=marks, date=datetime(2026, 8, 10, tzinfo=timezone.utc))


def addr(tag: str = "decode", info: str = "intens", seed: int = 1776,
         model: str | None = "stub-model") -> ReplicateAddress:
    return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)


def log_key(model: str, seed: int, info: str, ts: datetime,
            experiment: str = "periodic") -> str:
    return f"{experiment}/{model}/seed={seed}/{info}--{format_run_ts(ts)}.yaml"


def patch_utcnow(monkeypatch: pytest.MonkeyPatch, fn: Callable[[], datetime]) -> None:
    for mod in (rs, replicates):  # both modules may have bound the utcnow seam
        monkeypatch.setattr(mod, "utcnow", fn)


class FakeS3Client:
    """In-memory stand-in for the S3 calls the store makes, over one dict."""

    def __init__(self) -> None:
        self.objects: dict = {}
        self.etags: dict = {}  # key -> ETag override; unset = a correct quoted MD5
        self.probes: list = []  # (Prefix, MaxKeys) of every list_objects_v2 call
        self.requested: list = []  # (service, region) of every client build

    def _fresh(self, service: str, region: str | None = None) -> Self:
        self.requested.append((service, region))
        return self

    def _entry(self, key: str) -> dict[str, Any]:
        body = self.objects[key]
        return {"Key": key, "Size": len(body),
                "ETag": self.etags.get(key, f'"{hashlib.md5(body).hexdigest()}"')}

    def _matching(self, prefix: str) -> list[str]:
        return sorted(k for k in self.objects if k.startswith(prefix))

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:
        self.objects[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "no"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def list_objects_v2(self, Bucket: str, Prefix: str = "",
                        MaxKeys: int | None = None) -> dict[str, Any]:
        self.probes.append((Prefix, MaxKeys))
        return {"Contents": [self._entry(k) for k in self._matching(Prefix)[:MaxKeys]],
                "IsTruncated": False}

    def get_paginator(self, operation_name: str) -> Self:
        return self

    def paginate(self, Bucket: str | None = None, Prefix: str = "",
                 **kwargs: Any) -> Iterator[dict[str, Any]]:
        """One key per page, plus a trailing page carrying no ``Contents``."""
        for key in self._matching(Prefix):
            yield {"Contents": [self._entry(key)]}
        yield {}


@pytest.fixture
def fake_s3(monkeypatch: pytest.MonkeyPatch) -> FakeS3Client:
    client = FakeS3Client()
    monkeypatch.setattr(_aws, "fresh_client", client._fresh)
    return client


@pytest.fixture
def s3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")


@pytest.fixture(autouse=True)
def _no_ambient_store_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear ambient store settings for isolated tests."""
    for var in ("SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION", "AWS_REGION"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # Prevent writes to the checkout.
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(rs, "repo_root", lambda: root)
    return root


def test_local_layout_is_the_unchanged_analysis_tree(tmp_path: Path) -> None:
    """Keyed by tag/info/seed only; model and run_ts do not appear, last write wins."""
    store = LocalResultsStore(tmp_path)
    marks = sample_marks()
    assert not store.exists(addr())
    store.dump_marks(marks, addr(), TS1)
    d = tmp_path / "decode_intens"
    marks.dump(tmp_path / "reference.yaml")
    assert (d / "rep_1776.yaml").read_bytes() == (tmp_path / "reference.yaml").read_bytes()
    assert store.exists(addr()) and store.load_marks(addr()) == marks
    LocalResultsStore(tmp_path, "one_hop_").dump_marks(marks, addr(), TS1)
    assert (tmp_path / "one_hop_decode_intens" / "rep_1776.yaml").is_file()
    store.dump_marks(sample_marks(score=0), addr(model="model-b"), TS2)
    assert sorted(p.name for p in d.glob("*")) == ["rep_1776.yaml"]
    assert store.load_marks(addr()).marks[0].score == 0
    # List only direct replicate seeds.
    (d / "nested").mkdir()
    for name in ("rep_2.yaml", "rep_10.yaml", "summary.yaml", "rep_abc.yaml"):
        (d / name).write_text("x")
    (d / "nested" / "rep_9.yaml").write_text("x")
    assert store.list_seeds(None, "decode", "intens") == [2, 10, 1776]
    assert store.list_seeds(None, "never_ran", "intens") == []


def test_s3_log_is_append_only_and_earliest_wins(fake_s3: FakeS3Client) -> None:
    """Pinned key scheme; a re-run adds a key; reads and list_seeds take the earliest."""
    store = S3ResultsStore(BUCKET, "", "periodic_moe", "us-west-2")  # bucket/base/exp/region
    with pytest.raises(FileNotFoundError):
        store.load_marks(addr())
    moe = ReplicateAddress(tag="moe", info="extens", seed=1776, model="gpt-oss-120b")
    store.dump_marks(sample_marks(score=1), moe, TS1)
    store.dump_marks(sample_marks(score=0), moe, TS2)  # a re-run adds, never overwrites
    assert sorted(fake_s3.objects) == [
        "periodic_moe/gpt-oss-120b/seed=1776/extens--20260810T193000Z.yaml",
        "periodic_moe/gpt-oss-120b/seed=1776/extens--20260811T040506Z.yaml"]
    assert store.load_marks(moe).marks[0].score == 1
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    other = addr(seed=1777)
    store.dump_marks(sample_marks(score=0), other, TS2)  # newer, written first
    store.dump_marks(sample_marks(score=1), other, TS1)  # older, written second
    assert store.load_marks(other).marks[0].score == 1
    store.dump_marks(sample_marks(), addr(seed=1778, info="extens"), TS1)
    assert store.list_seeds("stub-model", "decode", "intens") == [1776, 1777]
    assert store.list_seeds("stub-model", "decode", "extens") == [1778]
    assert store.list_seeds("never-served", "decode", "intens") == []
    based = S3ResultsStore(BUCKET, "archive/2026-08", "periodic_moe", "us-west-2")
    based.dump_marks(sample_marks(), addr(seed=1), TS1)
    assert ("archive/2026-08/periodic_moe/stub-model/seed=1/intens--20260810T193000Z.yaml"
            in fake_s3.objects)
    # ``--`` prevents sibling info-prefix matches.
    assert store.exists(addr())
    assert fake_s3.probes[-1] == ("periodic_moe/stub-model/seed=1776/intens--", 1)
    assert set(fake_s3.requested) == {("s3", "us-west-2")}
    store.dump_marks(sample_marks(), addr(info="noise_intens"), TS1)
    assert store.exists(addr(info="noise_intens"))
    assert not store.exists(addr(info="int"))  # "--" stops a prefix-of-info match
    # Model-less addresses are read-only; ``None/`` would persist.
    logged = len(fake_s3.objects)
    with pytest.raises(ValueError):
        store.dump_marks(sample_marks(), addr(model=None), TS1)
    assert len(fake_s3.objects) == logged, "a refused write must leave no object behind"
    assert not store.exists(addr(model=None))


def test_resolve_store(monkeypatch: pytest.MonkeyPatch, fake_repo: Path,
                       tmp_path: Path) -> None:
    """Unset env is local; a non-repo dir stays local even with the S3 env set."""
    # Fixed-width UTC enables lexical earliest-run lookup.
    assert format_run_ts(TS1) == "20260810T193000Z"
    assert format_run_ts(TS2) == "20260811T040506Z"
    now = rs.utcnow()
    assert now.tzinfo is not None and now.utcoffset().total_seconds() == 0
    assert experiment_name(fake_repo / "somewhere/else") == "somewhere/else"
    local = resolve_store(tmp_path)
    assert isinstance(local, LocalResultsStore) and local.root == tmp_path
    assert resolve_store(tmp_path, "one_hop_").prefix == "one_hop_"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    assert isinstance(resolve_store(tmp_path / "results"), LocalResultsStore)
    for uri, rel, prefix, base, exp in [
        (URI, "notebooks/periodic_moe/results", "", "", "periodic_moe"),
        (URI, "notebooks/divisor/results", "one_hop_", "", "divisor/one_hop"),
        (URI, "notebooks/brand_new/results", "", "", "brand_new"),  # need not exist
        (f"{URI}/archive/2026-08", "notebooks/periodic/results", "", "archive/2026-08",
         "periodic"),
    ]:
        monkeypatch.setenv("SMOLBENCH_RESULTS_S3", uri)
        store = resolve_store(fake_repo / rel, prefix)  # S3 fields imply the S3 store
        assert (store.bucket, store.base_prefix, store.experiment) == (BUCKET, base, exp)
        assert store.describe() == f"s3://{BUCKET}/" + "/".join(p for p in (base, exp) if p)
    results = fake_repo / "notebooks/periodic/results"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    # Only the project bucket uses the configured region fallback.
    from smolbench.evals import study_config

    assert resolve_store(results).region == study_config.load_study_config().results.region
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://a-different-bucket")
    assert resolve_store(results).region is None
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    assert resolve_store(results).region == "eu-central-1"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")
    assert resolve_store(results).region == "us-west-2"
    assert parse_s3_uri(f"s3://{BUCKET}/") == (BUCKET, "")
    assert parse_s3_uri(f"s3://{BUCKET}/archive/2026-08/") == (BUCKET, "archive/2026-08")
    for bad in ("bucket", "https://bucket/x", "s3://", "s3://buck//archive", "s3://bu ck"):
        with pytest.raises(ValueError):
            parse_s3_uri(bad)
    # Validate before repository anchoring so typos fail loudly.
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://")
    with pytest.raises(ValueError):
        resolve_store(tmp_path / "somewhere-else")


def test_sync_down_translates_and_guards(monkeypatch: pytest.MonkeyPatch, s3_env: None,
                                        fake_repo: Path, fake_s3: FakeS3Client,
                                        tmp_path: Path) -> None:
    """model -> tag, into ``{prefix}{tag}_{info}/rep_{seed}.yaml``, earliest run only."""
    results = fake_repo / "notebooks/periodic/results"
    body = sample_marks(score=1).dumps().encode()
    rerun = sample_marks(score=0).dumps().encode()
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS2)] = rerun  # later re-run
    assert sync_down(results, TAGS) == 2
    assert (results / "moe_extens" / "rep_1776.yaml").read_bytes() == body
    assert (results / "decode_intens" / "rep_1777.yaml").read_bytes() == body
    divisor = fake_repo / "notebooks/divisor/results"
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1, "divisor/one_hop")] = body
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1, "divisor/one_hop")] = body
    argv = [str(divisor), "--tag", "stub-model=decode", "--tag", "gpt-oss-120b=moe",
            "--prefix", "one_hop_"]
    assert rs.main(argv) == 0  # the CLI re-types the repeatable tag map, then calls sync_down
    assert (divisor / "one_hop_decode_intens" / "rep_1776.yaml").read_bytes() == body
    assert (divisor / "one_hop_moe_extens" / "rep_1776.yaml").read_bytes() == body
    with pytest.raises(SystemExit):
        rs.main([str(results), "--tag", "no-equals-sign"])
    # Refetch on unverifiable ETags or changed same-length regrades.
    assert len(rerun) == len(body) and rerun != body, "premise"
    for seed, local, suffix, downloads in [(1, body, "", 0), (2, rerun, "", 1),
                                           (3, body, "-2", 1)]:
        fake_s3.objects.clear()
        key = log_key("stub-model", seed, "intens", TS1)
        fake_s3.objects[key] = body
        if suffix:
            fake_s3.etags[key] = f'"{hashlib.md5(body).hexdigest()}{suffix}"'
        rep = results / "decode_intens" / f"rep_{seed}.yaml"
        rep.write_bytes(local)
        assert sync_down(results, TAGS) == downloads, seed
        assert rep.read_bytes() == body
    fake_s3.objects.clear()
    # Refuse path traversal and local-store resolutions.
    fake_s3.objects[log_key("evil-model", 1776, "intens", TS1)] = b"pwned"
    with pytest.raises(ValueError):
        sync_down(results, {"evil-model": "../../ESCAPED"})
    assert not (fake_repo / "ESCAPED_intens").exists()
    with pytest.raises(RuntimeError):
        sync_down(tmp_path / "elsewhere", TAGS)
    # Refuse empty log prefixes before ``sync_down`` can list a bucket.
    with pytest.raises(ValueError):
        sync_down(fake_repo, TAGS)
    with pytest.raises(ValueError):
        S3ResultsStore(BUCKET, "", "", "us-west-2")
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3")
    with pytest.raises(RuntimeError):
        sync_down(results, TAGS)


def _log(fake_s3: FakeS3Client, seed: int, info: str, ts: datetime,
         body: bytes | None = None) -> None:
    key = log_key("stub-model", seed, info, ts, experiment="periodic_moe")
    fake_s3.objects[key] = body or Marks(model="stub-model", marks=()).dumps().encode()


@pytest.fixture
def s3_harness(fake_repo: Path, s3_env: None, fake_s3: FakeS3Client,
               monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[tuple[int, int]]]:
    """(harness on the log store, list of (seed, quiz size) per faked evaluate() call)."""
    calls: list = []

    def _evaluate(quiz: Any, model: str, seed: int, **kwargs: Any) -> Marks:
        calls.append((seed, len(quiz)))
        return Marks(model=model, marks=tuple(
            Mark(query=q.prompt, answer=q.answer, response=str(q.answer), score=1,
                 compliance=COMPLIANT)
            for q in quiz))
    monkeypatch.setattr(provider, "evaluate", _evaluate)
    return replicates.ReplicateHarness(
        results_dir=fake_repo / "notebooks/periodic_moe/results", seeds=(1, 2),
        archetype_tags={"stub-model": "decode"}, info_types=("intens", "extens"),
        make_quizzes=lambda seed, model: {
            "intens": tuple(Numeric(prompt=f"i{i}/{seed}", answer=i) for i in (1, 2)),
            "extens": (Numeric(prompt=f"e1/{seed}", answer=3),)}), calls


def test_harness_runs_summarizes_and_syncs_down(
        s3_harness: tuple[Any, list[tuple[int, int]]], fake_s3: FakeS3Client,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """The store is the cached log store; a run logs only to S3; sync_down lands it."""
    s3_harness, evaluated = s3_harness
    assert isinstance(s3_harness.store, S3ResultsStore)
    assert s3_harness.store.experiment == "periodic_moe"
    assert s3_harness.store is s3_harness.store  # cached_property
    patch_utcnow(monkeypatch, lambda: TS1)
    assert s3_harness.has_outstanding("stub-model")
    for info in ("intens", "extens"):
        _log(fake_s3, 1, info, TS1)  # already logged -> skipped, whatever its timestamp
    s3_harness.run_replicates("stub-model")
    assert evaluated == [(2, 3)]  # seed 1 skipped, seed 2 pooled
    assert sorted(fake_s3.objects) == [
        f"periodic_moe/stub-model/seed={seed}/{info}--{format_run_ts(TS1)}.yaml"
        for seed in (1, 2) for info in ("extens", "intens")]
    assert not s3_harness.has_outstanding("stub-model")
    assert not s3_harness.results_dir.exists()
    body = sample_marks().dumps().encode()
    _log(fake_s3, 1776, "extens", TS1, body)
    assert s3_harness.sync_down() == 5
    assert (s3_harness.results_dir / "decode_extens" / "rep_1776.yaml").read_bytes() == body
    fake_s3.objects.clear()
    for seed in (1, 2):
        _log(fake_s3, seed, "intens", TS1, sample_marks(score=1).dumps().encode())
        _log(fake_s3, seed, "intens", TS2, sample_marks(score=0).dumps().encode())
    s3_harness.summarize("stub-model")
    out = capsys.readouterr().out
    # Earliest run scored one of four correct.
    assert "decode/intens: 2/2 replicates -- correct=4 incorrect=0 invalid=0 acc=1.000" in out
    assert "decode/extens: 0/2 replicates -- correct=0 incorrect=0 invalid=0 acc=n/a" in out
    fake_s3.objects.clear()
    stamps = iter([TS1, TS2])  # one per pooled call: a per-dump utcnow() would exhaust this
    patch_utcnow(monkeypatch, lambda: next(stamps))
    s3_harness.run_replicates("stub-model")
    keys = {s: [k for k in fake_s3.objects if f"seed={s}/" in k] for s in (1, 2)}
    assert [len(v) for v in keys.values()] == [2, 2]  # both infos logged, per seed
    stamps_of = {s: {k.rsplit("--", 1)[1] for k in v} for s, v in keys.items()}
    assert len(stamps_of[1]) == len(stamps_of[2]) == 1 and stamps_of[1] != stamps_of[2]



SUPERSEDED_REASON = "re-collected past the resume-skip"


def s3_store() -> S3ResultsStore:
    """The log store the supersede tests below share."""
    return S3ResultsStore(BUCKET, "", "periodic_moe", "us-west-2")


def marker_key(seed: int = 1776, info: str = "intens", ts: datetime = TS1,
               model: str = "stub-model") -> str:
    return (f"periodic_moe/{model}/seed={seed}/{info}--{format_run_ts(ts)}"
            f".superseded")


def test_supersede_writes_a_json_marker_beside_the_run(fake_s3: FakeS3Client) -> None:
    """The marker is a sibling key, so the run itself is never mutated or deleted."""
    import json

    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    store.supersede(addr(), format_run_ts(TS1), SUPERSEDED_REASON)

    assert marker_key() in fake_s3.objects
    # Run objects remain immutable.
    assert (fake_s3.objects[f"periodic_moe/stub-model/seed=1776/intens--"
                            f"{format_run_ts(TS1)}.yaml"]
            == sample_marks(score=1).dumps().encode())
    body = json.loads(fake_s3.objects[marker_key()].decode())
    assert body["reason"] == SUPERSEDED_REASON
    # Marker timestamp remains parseable UTC.
    assert datetime.fromisoformat(body["superseded_at"]).tzinfo is not None


def test_reads_skip_a_superseded_run_and_take_the_earliest_survivor(fake_s3: FakeS3Client) -> None:
    """Earliest-wins applies over the survivors, not over every logged run."""
    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)   # the run to retire
    store.dump_marks(sample_marks(score=0), addr(), TS2)   # its replacement
    assert store.load_marks(addr()).marks[0].score == 1

    store.supersede(addr(), format_run_ts(TS1), SUPERSEDED_REASON)
    assert store.list_runs(addr()) == [format_run_ts(TS2)]
    assert store.load_marks(addr()).marks[0].score == 0


def test_a_marker_is_not_itself_a_run(fake_s3: FakeS3Client) -> None:
    """A ``.superseded`` key must never be listed, loaded or counted as a run."""
    store = s3_store()
    store.dump_marks(sample_marks(), addr(), TS1)
    store.supersede(addr(), format_run_ts(TS1), SUPERSEDED_REASON)
    assert store.list_runs(addr()) == []
    # Presence probes stay marker-blind for resume skipping.
    assert store.exists(addr())
    assert store.list_seeds("stub-model", "decode", "intens") == [1776]
    # Empty reads name the affected prefix.
    with pytest.raises(FileNotFoundError) as exc:
        store.load_marks(addr())
    assert "periodic_moe/stub-model/seed=1776/intens--" in str(exc.value)
    assert "superseded" in str(exc.value)


def test_supersede_all_retires_every_surviving_run(fake_s3: FakeS3Client) -> None:
    """The harness's one call: however many runs an address has, retire them all."""
    store = s3_store()
    assert store.supersede_all(addr(), SUPERSEDED_REASON) == 0  # nothing logged yet
    store.dump_marks(sample_marks(), addr(), TS1)
    store.dump_marks(sample_marks(), addr(), TS2)
    assert store.supersede_all(addr(), SUPERSEDED_REASON) == 2
    assert store.list_runs(addr()) == []
    # Markers are siblings of their runs.
    assert sorted(fake_s3.objects) == [
        marker_key(ts=TS1),
        f"periodic_moe/stub-model/seed=1776/intens--{format_run_ts(TS1)}.yaml",
        marker_key(ts=TS2),
        f"periodic_moe/stub-model/seed=1776/intens--{format_run_ts(TS2)}.yaml",
    ]
    # Repeated superseding writes nothing.
    before = dict(fake_s3.objects)
    assert store.supersede_all(addr(), SUPERSEDED_REASON) == 0
    assert fake_s3.objects == before


def test_sync_down_skips_superseded_runs(fake_repo: Path, s3_env: None,
                                         fake_s3: FakeS3Client) -> None:
    """Synced trees honor superseding markers."""
    results = fake_repo / "notebooks/periodic_moe/results"
    _log(fake_s3, 1, "intens", TS1, sample_marks(score=1).dumps().encode())
    _log(fake_s3, 1, "intens", TS2, sample_marks(score=0).dumps().encode())
    store = resolve_store(results)
    store.supersede(ReplicateAddress(tag="decode", info="intens", seed=1,
                                     model="stub-model"),
                    format_run_ts(TS1), SUPERSEDED_REASON)

    assert sync_down(results, {"stub-model": "decode"}) == 1
    landed = Marks.load(results / "decode_intens" / "rep_1.yaml")
    assert landed.marks[0].score == 0
    assert landed == store.load_marks(
        ReplicateAddress(tag="decode", info="intens", seed=1, model="stub-model")
    )


def test_local_supersede_renames_and_every_reader_ignores_the_file(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local superseding renames files without changing bytes."""
    patch_utcnow(monkeypatch, lambda: TS1)
    store = LocalResultsStore(tmp_path)
    store.dump_marks(sample_marks(), addr(), TS1)
    live = tmp_path / "decode_intens" / "rep_1776.yaml"
    body = live.read_bytes()

    retired = store.supersede(addr(), SUPERSEDED_REASON)
    assert not live.exists()
    assert retired.name == f"rep_1776.SUPERSEDED-{format_run_ts(TS1)}.yaml"
    assert retired.read_bytes() == body
    assert store.list_seeds(None, "decode", "intens") == []
    assert not store.exists(addr())
    with pytest.raises(FileNotFoundError):
        store.load_marks(addr())

    # Empty superseding is a harness-wide no-op.
    assert store.supersede(addr(seed=999), SUPERSEDED_REASON) is None
    assert store.supersede_all(addr(), SUPERSEDED_REASON) == 0


def test_regrade_writes_a_self_describing_run_and_retires_the_old_one(
        fake_s3: FakeS3Client) -> None:
    """Regrades name the replaced run and add a marker."""
    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    regraded = dataclasses.replace(
        sample_marks(score=0), regraded_from=format_run_ts(TS1)
    )
    store.regrade(regraded, addr(), TS2, reason="re-graded with the fixed parser")

    assert store.list_runs(addr()) == [format_run_ts(TS2)]
    loaded = store.load_marks(addr())
    assert loaded.marks[0].score == 0
    assert loaded.regraded_from == format_run_ts(TS1)
    assert marker_key(ts=TS1) in fake_s3.objects

    # Refuse regrades without a self-describing predecessor.
    with pytest.raises(ValueError):
        store.regrade(sample_marks(score=1), addr(seed=1777), TS2, reason="x")
