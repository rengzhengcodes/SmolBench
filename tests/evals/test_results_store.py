"""Replicate results store: local tree, S3 append-only log, env resolution, sync_down."""

import hashlib
import io
from datetime import datetime, timezone

import pytest
from botocore.exceptions import ClientError

from smolbench.evals import Mark, Marks, Numeric
from smolbench.evals import _aws, provider, replicates
from smolbench.evals import results_store as rs
from smolbench.evals.results_store import (
    LocalResultsStore,
    ReplicateAddress,
    S3ResultsStore,
    experiment_name,
    format_run_ts,
    parse_s3_uri,
    resolve_store,
    sync_down,
)

BUCKET = "smolbench-results-414266451290"
URI = f"s3://{BUCKET}"

TS1 = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)  # 20260810T193000Z
TS2 = datetime(2026, 8, 11, 4, 5, 6, tzinfo=timezone.utc)  # 20260811T040506Z


def sample_marks(model: str = "stub-model", n: int = 2, score: int = 1) -> Marks:
    """A small Marks with a pinned date so equality is exact."""
    return Marks(
        model=model,
        marks=tuple(
            Mark(query=f"q{i}", answer=i, response=str(i), score=score) for i in range(n)
        ),
        date=datetime(2026, 8, 10, tzinfo=timezone.utc),
    )


class FakeS3Client:
    """In-memory stand-in for the four S3 calls the store makes, over one dict."""

    def __init__(self, objects=None):
        self.objects: dict = dict(objects or {})
        #: key -> ETag override. Unset means a correct single-part quoted MD5.
        self.etags: dict = {}
        self.calls: list = []

    def _entry(self, key):
        body = self.objects[key]
        etag = self.etags.get(key, f'"{hashlib.md5(body).hexdigest()}"')
        return {"Key": key, "Size": len(body), "ETag": etag}

    def _matching(self, prefix):
        return sorted(k for k in self.objects if k.startswith(prefix))

    def put_object(self, Bucket, Key, Body):
        self.calls.append(("put_object", Key))
        self.objects[Key] = Body

    def get_object(self, Bucket, Key):
        self.calls.append(("get_object", Key))
        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "No such key"}}, "GetObject"
            )
        return {"Body": io.BytesIO(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix="", MaxKeys=None):
        self.calls.append(("list_objects_v2", Prefix, MaxKeys))
        keys = self._matching(Prefix)[:MaxKeys]
        return {"Contents": [self._entry(k) for k in keys], "IsTruncated": False}

    def get_paginator(self, operation_name):
        assert operation_name == "list_objects_v2"
        return _FakePaginator(self)


class _FakePaginator:
    """Pages one key per page, plus a trailing page with no ``Contents``."""

    def __init__(self, client: FakeS3Client):
        self._client = client

    def paginate(self, Bucket=None, Prefix="", **kwargs):
        self._client.calls.append(("paginate", Prefix, None))
        for key in self._client._matching(Prefix):
            yield {"Contents": [self._client._entry(key)]}
        yield {}


@pytest.fixture
def fake_s3(monkeypatch):
    """Installs a FakeS3Client behind ``_aws.fresh_client`` and returns it."""
    client = FakeS3Client()
    requested: list = []

    def _fresh_client(service, region=None):
        requested.append((service, region))
        return client

    monkeypatch.setattr(_aws, "fresh_client", _fresh_client)
    client.requested = requested
    return client


@pytest.fixture
def s3_env(monkeypatch):
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")


@pytest.fixture(autouse=True)
def _no_ambient_store_env(monkeypatch):
    """Autouse: a shell's exported env vars must not change what these tests measure."""
    for var in ("SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION", "AWS_REGION"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_repo(monkeypatch, tmp_path):
    """Make ``tmp_path/repo`` the repo root, so nothing writes into the checkout."""
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(rs, "repo_root", lambda: root)
    return root


@pytest.fixture
def freeze_ts(monkeypatch):
    """Freezes the ``utcnow`` seam in both modules that may have bound it."""

    def _set(when):
        monkeypatch.setattr(rs, "utcnow", lambda: when)
        monkeypatch.setattr(replicates, "utcnow", lambda: when)

    return _set


@pytest.mark.parametrize(
    "rel,prefix,expected",
    [
        ("notebooks/periodic_moe/results", "", "periodic_moe"),
        ("notebooks/chromatic/results", "one_hop_", "chromatic/one_hop"),
        ("somewhere/else", "", "somewhere/else"),
    ],
)
def test_experiment_name(fake_repo, rel, prefix, expected):
    assert experiment_name(fake_repo / rel, prefix) == expected


def test_run_ts_is_fixed_width_utc_and_utcnow_is_aware():
    """Fixed width is load-bearing: every "earliest" lookup is a string min."""
    assert format_run_ts(TS1) == "20260810T193000Z"
    assert format_run_ts(TS2) == "20260811T040506Z"
    assert len(format_run_ts(TS1)) == len(format_run_ts(TS2))
    assert format_run_ts(TS1) < format_run_ts(TS2)
    now = rs.utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0


def addr(tag="decode", info="intens", seed=1776, model="stub-model"):
    return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)


def test_local_layout_is_the_unchanged_analysis_tree(tmp_path):
    """Keyed by tag/info/seed only; model and run_ts do not appear, last write wins."""
    store = LocalResultsStore(tmp_path)
    marks = sample_marks()
    assert not store.exists(addr())
    store.dump_marks(marks, addr(), TS1)
    written = tmp_path / "decode_intens" / "rep_1776.yaml"
    reference = tmp_path / "reference.yaml"
    marks.dump(reference)
    assert written.read_bytes() == reference.read_bytes()
    assert store.exists(addr())
    assert store.load_marks(addr()) == marks
    LocalResultsStore(tmp_path, "one_hop_").dump_marks(marks, addr(), TS1)
    assert (tmp_path / "one_hop_decode_intens" / "rep_1776.yaml").is_file()
    store.dump_marks(sample_marks(score=0), addr(model="model-b"), TS2)
    names = sorted(p.name for p in (tmp_path / "decode_intens").glob("*"))
    assert names == ["rep_1776.yaml"]
    assert store.load_marks(addr()).marks[0].score == 0


def test_local_list_seeds_parses_sorted_distinct_ints(tmp_path):
    d = tmp_path / "decode_intens"
    (d / "nested").mkdir(parents=True)
    for name in ("rep_2.yaml", "rep_1.yaml", "rep_10.yaml"):
        (d / name).write_text("x")
    (d / "summary.yaml").write_text("x")  # not a replicate
    (d / "rep_abc.yaml").write_text("x")  # seed does not parse
    (d / "nested" / "rep_9.yaml").write_text("x")  # not a direct child
    store = LocalResultsStore(tmp_path)
    assert store.list_seeds(None, "decode", "intens") == [1, 2, 10]
    assert store.list_seeds(None, "never_ran", "intens") == []


def s3_store(experiment="periodic_moe", base_prefix=""):
    return S3ResultsStore(
        bucket=BUCKET, base_prefix=base_prefix, experiment=experiment, region="us-west-2"
    )


def test_s3_key_scheme(fake_s3):
    """The directive's worked example, and the same key under a base prefix."""
    s3_store().dump_marks(
        sample_marks(),
        ReplicateAddress(tag="moe", info="extens", seed=1776, model="gpt-oss-120b"),
        TS1,
    )
    assert list(fake_s3.objects) == [
        "periodic_moe/gpt-oss-120b/seed=1776/extens--20260810T193000Z.yaml"
    ]
    fake_s3.objects.clear()
    s3_store(base_prefix="archive/2026-08").dump_marks(sample_marks(), addr(), TS1)
    assert list(fake_s3.objects) == [
        "archive/2026-08/periodic_moe/stub-model/seed=1776/intens--20260810T193000Z.yaml"
    ]


def test_s3_dump_is_append_only(fake_s3):
    """A second run of the same (model, seed, info) ADDS an object, never overwrites."""
    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    store.dump_marks(sample_marks(score=0), addr(), TS2)
    assert sorted(fake_s3.objects) == [
        "periodic_moe/stub-model/seed=1776/intens--20260810T193000Z.yaml",
        "periodic_moe/stub-model/seed=1776/intens--20260811T040506Z.yaml",
    ]


def test_s3_load_marks_earliest_wins(fake_s3):
    """The earliest TIMESTAMP is the measurement, whatever the write order."""
    store = s3_store()
    with pytest.raises(FileNotFoundError):
        store.load_marks(addr())
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    store.dump_marks(sample_marks(score=0), addr(), TS2)
    assert store.load_marks(addr()).marks[0].score == 1
    other = addr(seed=1777)
    store.dump_marks(sample_marks(score=0), other, TS2)  # newer, written first
    store.dump_marks(sample_marks(score=1), other, TS1)  # older, written second
    assert store.load_marks(other).marks[0].score == 1


def test_s3_exists_is_a_bounded_prefix_probe(fake_s3):
    """Resume-skip lists at most one key, and ``--`` stops sibling info prefixes."""
    store = s3_store()
    assert not store.exists(addr())
    store.dump_marks(sample_marks(), addr(), TS1)
    assert store.exists(addr())
    probes = [c for c in fake_s3.calls if c[0] == "list_objects_v2"]
    assert probes, "exists must probe via list_objects_v2"
    assert probes[-1][1] == "periodic_moe/stub-model/seed=1776/intens--"
    assert probes[-1][2] == 1
    assert set(fake_s3.requested) == {("s3", "us-west-2")}
    store.dump_marks(sample_marks(), addr(info="noise_intens"), TS1)
    assert store.exists(addr(info="noise_intens"))
    assert not store.exists(addr(info="extens"))


def test_s3_dump_refuses_a_model_less_address(fake_s3):
    """A model-less address is a READ shape: a ``None/`` key would be permanent."""
    store = s3_store()
    with pytest.raises(ValueError):
        store.dump_marks(sample_marks(), addr(model=None), TS1)
    assert fake_s3.objects == {}, "a refused write must leave no object behind"
    assert not store.exists(addr(model=None))


def test_s3_list_seeds_parses_the_log(fake_s3):
    store = s3_store()
    for seed in (1778, 1776):
        store.dump_marks(sample_marks(), addr(seed=seed), TS1)
    store.dump_marks(sample_marks(), addr(seed=1776), TS2)  # 2nd run, same seed
    store.dump_marks(sample_marks(), addr(seed=1777, info="extens"), TS1)  # other info
    assert store.list_seeds("stub-model", "decode", "intens") == [1776, 1778]
    assert store.list_seeds("stub-model", "decode", "extens") == [1777]
    assert store.list_seeds("never-served", "decode", "intens") == []


def test_resolve_store_local(monkeypatch, tmp_path):
    """Unset env is local; a non-repo dir stays local even with the S3 env set."""
    store = resolve_store(tmp_path)
    assert isinstance(store, LocalResultsStore)
    assert store.root == tmp_path
    assert resolve_store(tmp_path, "one_hop_").prefix == "one_hop_"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    assert isinstance(resolve_store(tmp_path / "results"), LocalResultsStore)


def test_resolve_store_s3(s3_env, fake_repo):
    """A repo-anchored dir maps to the log store, prefix folds in, dir need not exist."""
    store = resolve_store(fake_repo / "notebooks/periodic_moe/results")
    assert isinstance(store, S3ResultsStore)
    assert (store.bucket, store.base_prefix, store.experiment) == (BUCKET, "", "periodic_moe")
    assert store.region == "us-west-2"
    assert store.describe() == f"s3://{BUCKET}/periodic_moe"
    prefixed = resolve_store(fake_repo / "notebooks/chromatic/results", "one_hop_")
    assert prefixed.experiment == "chromatic/one_hop"
    fresh = resolve_store(fake_repo / "notebooks/brand_new/results")  # need not exist
    assert fresh.experiment == "brand_new"


def test_resolve_store_honours_a_base_prefix_in_the_uri(monkeypatch, fake_repo):
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", f"s3://{BUCKET}/archive/2026-08")
    store = resolve_store(fake_repo / "notebooks/periodic/results")
    assert (store.base_prefix, store.experiment) == ("archive/2026-08", "periodic")
    assert store.describe() == f"s3://{BUCKET}/archive/2026-08/periodic"


def test_resolve_store_region_precedence(monkeypatch, fake_repo):
    results = fake_repo / "notebooks/periodic/results"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")
    assert resolve_store(results).region == "us-west-2"
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3_REGION")
    assert resolve_store(results).region == "eu-central-1"
    monkeypatch.delenv("AWS_REGION")
    assert resolve_store(results).region is None


def test_s3_uri_parsing(monkeypatch, tmp_path):
    assert parse_s3_uri(f"s3://{BUCKET}") == (BUCKET, "")
    assert parse_s3_uri(f"s3://{BUCKET}/") == (BUCKET, "")
    assert parse_s3_uri(f"s3://{BUCKET}/archive/2026-08/") == (BUCKET, "archive/2026-08")
    for bad in ("bucket", "https://bucket/x", "s3://", "s3://buck//archive", "s3://bu ck"):
        with pytest.raises(ValueError):
            parse_s3_uri(bad)
    # Validation happens BEFORE the repo-anchor check, so a typo always fails loudly.
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://")
    with pytest.raises(ValueError):
        resolve_store(tmp_path / "somewhere-else")


TAGS = {"gpt-oss-120b": "moe", "stub-model": "decode"}


def log_key(model, seed, info, ts, experiment="periodic", base=""):
    head = f"{base}/" if base else ""
    return f"{head}{experiment}/{model}/seed={seed}/{info}--{format_run_ts(ts)}.yaml"


def test_sync_down_translates_the_log_into_the_analysis_layout(
    monkeypatch, fake_repo, fake_s3
):
    """model -> TAG, into ``{prefix}{tag}_{info}/rep_{seed}.yaml``, prefix on both sides."""
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    results = fake_repo / "notebooks/periodic/results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = body
    assert sync_down(results, TAGS) == 2
    assert (results / "moe_extens" / "rep_1776.yaml").read_bytes() == body
    assert (results / "decode_intens" / "rep_1777.yaml").read_bytes() == body
    chromatic = fake_repo / "notebooks/chromatic/results"
    key = log_key("stub-model", 1776, "intens", TS1, experiment="chromatic/one_hop")
    fake_s3.objects[key] = body
    assert sync_down(chromatic, TAGS, "one_hop_") == 1
    assert (chromatic / "one_hop_decode_intens" / "rep_1776.yaml").read_bytes() == body


def test_sync_down_writes_only_the_earliest_run_per_replicate(s3_env, fake_repo, fake_s3):
    """A synced tree must carry the same run ``load_marks`` resolves."""
    results = fake_repo / "notebooks/periodic/results"
    first = sample_marks(score=1).dumps().encode()
    rerun = sample_marks(score=0).dumps().encode()
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1)] = first
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS2)] = rerun
    assert sync_down(results, TAGS) == 1
    assert (results / "decode_intens" / "rep_1776.yaml").read_bytes() == first


def test_sync_down_refetch_policy(s3_env, fake_repo, fake_s3):
    """Skip only on a verified ETag-MD5 match; same-size edits and multipart ETags refetch."""
    results = fake_repo / "notebooks/periodic/results"
    (results / "decode_intens").mkdir(parents=True)
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1)] = body
    (results / "decode_intens" / "rep_1776.yaml").write_bytes(body)
    assert sync_down(results, TAGS) == 0
    # regrade.py flips score 1 -> 0 in place: byte-length preserving, different MD5.
    remote = sample_marks(n=1, score=1).dumps().encode()
    local = sample_marks(n=1, score=0).dumps().encode()
    assert len(remote) == len(local) and remote != local, "premise"
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = remote
    (results / "decode_intens" / "rep_1777.yaml").write_bytes(local)
    assert sync_down(results, TAGS) == 1
    assert (results / "decode_intens" / "rep_1777.yaml").read_bytes() == remote
    key = log_key("stub-model", 1778, "intens", TS1)
    fake_s3.objects[key] = body
    fake_s3.etags[key] = f'"{hashlib.md5(body).hexdigest()}-2"'
    (results / "decode_intens" / "rep_1778.yaml").write_bytes(body)
    assert sync_down(results, TAGS) == 1  # cannot verify -> refetch


def test_sync_down_refuses_a_key_that_escapes_results_dir(s3_env, fake_repo, fake_s3):
    """A tag containing path syntax must not walk out of the results tree."""
    results = fake_repo / "notebooks/periodic/results"
    fake_s3.objects[log_key("evil-model", 1776, "intens", TS1)] = b"pwned"
    with pytest.raises(ValueError):
        sync_down(results, {"evil-model": "../../ESCAPED"})
    assert not (fake_repo / "ESCAPED_intens").exists()


@pytest.mark.parametrize("case", ["no_env", "non_repo_dir"])
def test_sync_down_misuse_raises(monkeypatch, fake_repo, tmp_path, case):
    if case == "no_env":
        target = fake_repo / "notebooks/periodic/results"
    else:
        monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
        target = tmp_path / "elsewhere"
    with pytest.raises(RuntimeError):
        sync_down(target, TAGS)


def test_cli_syncs_with_repeatable_tags_and_a_prefix(s3_env, fake_repo, fake_s3, capsys):
    results = fake_repo / "notebooks/periodic/results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = body
    rc = rs.main([str(results), "--tag", "gpt-oss-120b=moe", "--tag", "stub-model=decode"])
    assert rc == 0
    assert (results / "moe_extens" / "rep_1776.yaml").is_file()
    assert (results / "decode_intens" / "rep_1777.yaml").is_file()
    assert str(results) in capsys.readouterr().out
    with pytest.raises(SystemExit):
        rs.main([str(results), "--tag", "no-equals-sign"])
    chromatic = fake_repo / "notebooks/chromatic/results"
    key = log_key("stub-model", 1776, "intens", TS1, experiment="chromatic/one_hop")
    fake_s3.objects[key] = body
    assert rs.main([str(chromatic), "--tag", "stub-model=decode", "--prefix", "one_hop_"]) == 0
    assert (chromatic / "one_hop_decode_intens" / "rep_1776.yaml").is_file()


def _quizzes(seed: int, model: str):
    return {
        "intens": (
            Numeric(prompt=f"i1/{seed}", answer=1),
            Numeric(prompt=f"i2/{seed}", answer=2),
        ),
        "extens": (Numeric(prompt=f"e1/{seed}", answer=3),),
    }


@pytest.fixture
def s3_harness(fake_repo, s3_env, fake_s3):
    return replicates.ReplicateHarness(
        results_dir=fake_repo / "notebooks/periodic_moe/results",
        archetype_tags={"stub-model": "decode"},
        make_quizzes=_quizzes,
        seeds=(1, 2),
        info_types=("intens", "extens"),
    )


@pytest.fixture
def fake_evaluate(monkeypatch):
    calls: list = []

    def _evaluate(quiz, model, seed, **kwargs):
        calls.append({"n": len(quiz), "model": model, "seed": seed})
        return Marks(
            model=model,
            marks=tuple(
                Mark(query=q.prompt, answer=q.answer, response=str(q.answer), score=1)
                for q in quiz
            ),
        )

    monkeypatch.setattr(provider, "evaluate", _evaluate)
    return calls


def _log(fake_s3, seed, info, ts, body=None):
    fake_s3.objects[log_key("stub-model", seed, info, ts, experiment="periodic_moe")] = (
        body if body is not None else Marks(model="stub-model", marks=()).dumps().encode()
    )


def test_harness_run_writes_the_log_then_syncs_down(
    s3_harness, fake_evaluate, fake_s3, freeze_ts
):
    """The harness store is the cached log store; a run logs only to S3, sync_down lands it."""
    assert isinstance(s3_harness.store, S3ResultsStore)
    assert s3_harness.store.experiment == "periodic_moe"
    assert s3_harness.store is s3_harness.store  # cached_property
    freeze_ts(TS1)
    s3_harness.run_replicates("stub-model")
    ts = format_run_ts(TS1)
    assert sorted(fake_s3.objects) == [
        f"periodic_moe/stub-model/seed=1/extens--{ts}.yaml",
        f"periodic_moe/stub-model/seed=1/intens--{ts}.yaml",
        f"periodic_moe/stub-model/seed=2/extens--{ts}.yaml",
        f"periodic_moe/stub-model/seed=2/intens--{ts}.yaml",
    ]
    assert not s3_harness.results_dir.exists()
    body = sample_marks().dumps().encode()
    _log(fake_s3, 1776, "extens", TS1, body)
    assert s3_harness.sync_down() == 5
    synced = s3_harness.results_dir / "decode_extens" / "rep_1776.yaml"
    assert synced.read_bytes() == body


def test_harness_pooled_infos_of_one_seed_share_a_timestamp(
    s3_harness, fake_evaluate, fake_s3, monkeypatch
):
    """Both infos of a seed come from ONE pooled evaluate() call, so one timestamp."""
    stamps = iter([TS1, TS2, TS1, TS2])  # one per call, so a per-dump call would differ
    monkeypatch.setattr(rs, "utcnow", lambda: next(stamps))
    monkeypatch.setattr(replicates, "utcnow", lambda: next(stamps))
    s3_harness.run_replicates("stub-model")
    for seed in (1, 2):
        seed_keys = [k for k in fake_s3.objects if f"seed={seed}/" in k]
        assert len(seed_keys) == 2
        assert len({k.rsplit("--", 1)[1] for k in seed_keys}) == 1, seed_keys


def test_harness_resume_and_outstanding_read_the_log(
    s3_harness, fake_evaluate, fake_s3, freeze_ts
):
    """Any logged run counts as done, whatever its timestamp."""
    freeze_ts(TS1)
    assert s3_harness.has_outstanding("stub-model")
    for info in ("intens", "extens"):
        _log(fake_s3, 1, info, TS1)
    s3_harness.run_replicates("stub-model")
    assert [(c["seed"], c["n"]) for c in fake_evaluate] == [(2, 3)]
    assert not s3_harness.has_outstanding("stub-model")
    assert not s3_harness.results_dir.exists()


def test_harness_summarize_uses_the_earliest_run(s3_harness, fake_s3, capsys):
    for seed in (1, 2):
        _log(fake_s3, seed, "intens", TS1, sample_marks(n=2, score=1).dumps().encode())
        _log(fake_s3, seed, "intens", TS2, sample_marks(n=2, score=0).dumps().encode())
    s3_harness.summarize("stub-model")
    out = capsys.readouterr().out
    # Earliest run scored 1 -> 4 correct, not 4 incorrect.
    assert "decode/intens: 2/2 replicates -- correct=4 incorrect=0 invalid=0 acc=1.000" in out
    assert "decode/extens: 0/2 replicates -- correct=0 incorrect=0 invalid=0 acc=n/a" in out
