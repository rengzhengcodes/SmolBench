"""The replicate results store: local tree, S3 append-only log, env resolution.

Everything here is OFFLINE. No boto3 ``Session`` is ever constructed: the S3
tests monkeypatch ``smolbench.evals._aws.fresh_client`` with a fake client, so
a test that accidentally reached the network would fail on the missing patch
rather than silently spending credentials or touching the real bucket (which
now exists, and is deliberately empty).

Two layouts are under test and they are deliberately different:

* LOCAL is the analysis layout, unchanged and byte-identical to what every
  notebook and ``power_analysis.py`` already reads:
  ``{prefix}{tag}_{info}/rep_{seed}.yaml``. One file per replicate; a re-run
  overwrites it.
* S3 is an append-only experiment LOG keyed by model, seed and run time:
  ``<base>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml``. A re-run
  ADDS an object; reads resolve the latest ``run_ts``.

The fake client raises REAL ``botocore.exceptions.ClientError`` objects,
because the store reads ``Error.Code`` through ``smolbench.evals._aws.
error_code`` -- a hand-rolled exception with the wrong shape would let a
broken error branch pass.
"""

import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from smolbench.evals import Mark, Marks
from smolbench.evals import _aws
from smolbench.evals import results_store as rs
from smolbench.evals.results_store import (
    LocalResultsStore,
    ReplicateAddress,
    S3ResultsStore,
    experiment_name,
    format_run_ts,
    parse_s3_uri,
    repo_root,
    resolve_store,
    sync_down,
)

BUCKET = "smolbench-results-414266451290"
URI = f"s3://{BUCKET}"

TS1 = datetime(2026, 8, 10, 19, 30, 0, tzinfo=timezone.utc)  # 20260810T193000Z
TS2 = datetime(2026, 8, 11, 4, 5, 6, tzinfo=timezone.utc)  # 20260811T040506Z

#: Sentinel for "this listing entry carries no ETag at all".
_NO_ETAG = object()


# ---------------------------------------------------------------------------
# Fixtures and fakes
# ---------------------------------------------------------------------------


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
    """In-memory stand-in for a boto3 S3 client.

    Implements the four calls the store makes -- ``put_object``,
    ``get_object``, ``list_objects_v2`` (used directly for the ``MaxKeys=1``
    existence probe) and ``get_paginator("list_objects_v2")`` -- over one
    ``{key: bytes}`` dict, so a listing and a fetch can never disagree.
    """

    def __init__(self, objects=None):
        self.objects: dict = dict(objects or {})
        #: key -> ETag override. Unset means a correct single-part quoted MD5.
        self.etags: dict = {}
        self.calls: list = []

    def _entry(self, key):
        body = self.objects[key]
        entry = {"Key": key, "Size": len(body)}
        etag = self.etags.get(key, f'"{hashlib.md5(body).hexdigest()}"')
        if etag is not _NO_ETAG:
            entry["ETag"] = etag
        return entry

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
        return {"Body": _Body(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix="", MaxKeys=None, ContinuationToken=None):
        self.calls.append(("list_objects_v2", Prefix, MaxKeys))
        keys = self._matching(Prefix)
        start = int(ContinuationToken or 0)
        keys = keys[start:]
        if MaxKeys is not None:
            keys = keys[:MaxKeys]
        return {
            "Contents": [self._entry(k) for k in keys],
            "KeyCount": len(keys),
            "IsTruncated": False,
        }

    def get_paginator(self, operation_name):
        assert operation_name == "list_objects_v2"
        return _FakePaginator(self)


class _Body:
    """The ``StreamingBody`` shape the store reads: ``.read() -> bytes``."""

    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakePaginator:
    """Pages an in-memory key space ONE KEY PER PAGE.

    One key per page forces the pagination loop to be exercised for real on
    every listing, so a page-boundary bug shows up on a two-object fixture
    instead of needing a 1000-object one. A trailing page with no
    ``Contents`` is always emitted -- what S3 returns for an empty prefix,
    and what a loop indexing ``page["Contents"]`` directly would crash on.
    """

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
    """Autouse: a developer shell exporting the store env vars must not change
    what these tests measure."""
    for var in ("SMOLBENCH_RESULTS_S3", "SMOLBENCH_RESULTS_S3_REGION", "AWS_REGION"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_repo(monkeypatch, tmp_path):
    """Makes ``tmp_path/repo`` the repo root as far as the store is concerned.

    Lets the S3-path tests use a genuinely repo-anchored results directory
    without ever touching the real checkout: a bug that wrote locally
    instead of to S3 litters /tmp, not ``notebooks/``.
    """
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(rs, "repo_root", lambda: root)
    return root


@pytest.fixture
def freeze_ts(monkeypatch):
    """Freezes the ``utcnow`` seam, wherever the caller bound it.

    ``replicates.py`` may reference ``results_store.utcnow`` through the
    module or have imported the name directly; patching both spellings keeps
    this fixture correct either way rather than silently freezing nothing
    (which would leave a real wall-clock timestamp in the assertions and
    make them flaky instead of failing honestly).
    """

    def _set(when):
        monkeypatch.setattr(rs, "utcnow", lambda: when)
        from smolbench.evals import replicates

        if hasattr(replicates, "utcnow"):
            monkeypatch.setattr(replicates, "utcnow", lambda: when, raising=False)

    return _set


# ---------------------------------------------------------------------------
# repo_root / lazy import
# ---------------------------------------------------------------------------


def test_repo_root_is_the_checkout_containing_notebooks():
    root = repo_root()
    assert (root / "smolbench" / "evals" / "results_store.py").is_file()
    assert (root / "notebooks").is_dir()


def test_experiment_reexports_the_same_repo_root_object():
    from smolbench.induction import experiment

    assert experiment.repo_root is rs.repo_root


def test_importing_results_store_does_not_import_boto3():
    """boto3 stays lazily imported (the house rule from ``_aws.py``)."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, smolbench.evals.results_store; "
            "sys.exit(1 if 'boto3' in sys.modules else 0)",
        ],
        cwd=str(repo_root()),
    )
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Experiment derivation and timestamps
# ---------------------------------------------------------------------------


def test_experiment_name_from_a_notebook_results_dir(fake_repo):
    assert experiment_name(fake_repo / "notebooks" / "periodic_moe" / "results") == (
        "periodic_moe"
    )


def test_experiment_name_makes_the_harness_prefix_a_sub_level(fake_repo):
    """``prefix="one_hop_"`` is a sub-level with the trailing underscore
    stripped, so the one-hop experiment logs alongside its sibling rather
    than colliding with it -- the same role the prefix plays in the local
    directory name."""
    assert experiment_name(
        fake_repo / "notebooks" / "chromatic" / "results", "one_hop_"
    ) == "chromatic/one_hop"


def test_experiment_name_falls_back_to_the_repo_relative_path(fake_repo):
    """A results dir that is not ``notebooks/<nb>/results`` still gets a
    deterministic, collision-free experiment name."""
    assert experiment_name(fake_repo / "somewhere" / "else") == "somewhere/else"


def test_format_run_ts_is_fixed_width_utc():
    """Fixed-width UTC is load-bearing: every "latest" lookup is a plain
    string max over listed keys, so lexicographic order MUST equal
    chronological order. A non-padded format (e.g. month 8 as "8") would
    sort 20261110 before 2026810 and silently return the wrong run."""
    assert format_run_ts(TS1) == "20260810T193000Z"
    assert format_run_ts(TS2) == "20260811T040506Z"
    assert len(format_run_ts(TS1)) == len(format_run_ts(TS2))
    assert format_run_ts(TS1) < format_run_ts(TS2)


def test_utcnow_is_timezone_aware_utc():
    now = rs.utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0


# ---------------------------------------------------------------------------
# LocalResultsStore -- byte-identical to the pre-store layout
# ---------------------------------------------------------------------------


def addr(tag="decode", info="intens", seed=1776, model="stub-model"):
    return ReplicateAddress(tag=tag, info=info, seed=seed, model=model)


def test_local_dump_writes_the_unchanged_analysis_layout(tmp_path):
    store = LocalResultsStore(tmp_path)
    marks = sample_marks()
    store.dump_marks(marks, addr(), TS1)

    written = tmp_path / "decode_intens" / "rep_1776.yaml"
    assert written.is_file()
    reference = tmp_path / "reference.yaml"
    marks.dump(reference)
    assert written.read_bytes() == reference.read_bytes()


def test_local_layout_honours_the_prefix(tmp_path):
    LocalResultsStore(tmp_path, "one_hop_").dump_marks(sample_marks(), addr(), TS1)
    assert (tmp_path / "one_hop_decode_intens" / "rep_1776.yaml").is_file()


def test_local_ignores_model_and_run_ts(tmp_path):
    """The local layout is keyed by tag/info/seed ONLY. Two runs of the same
    replicate overwrite one file -- the append-only log is an S3 property,
    and the analysis scripts require exactly one file per replicate."""
    store = LocalResultsStore(tmp_path)
    store.dump_marks(sample_marks(score=1), addr(model="model-a"), TS1)
    store.dump_marks(sample_marks(score=0), addr(model="model-b"), TS2)

    files = sorted(p.name for p in (tmp_path / "decode_intens").glob("*"))
    assert files == ["rep_1776.yaml"]
    assert store.load_marks(addr()).marks[0].score == 0  # last write wins


def test_local_exists_and_load_round_trip(tmp_path):
    store = LocalResultsStore(tmp_path)
    assert not store.exists(addr())
    store.dump_marks(sample_marks(), addr(), TS1)
    assert store.exists(addr())
    assert store.load_marks(addr()) == sample_marks()


def test_local_list_seeds_parses_sorted_distinct_ints(tmp_path):
    d = tmp_path / "decode_intens"
    (d / "nested").mkdir(parents=True)
    for name in ("rep_2.yaml", "rep_1.yaml", "rep_10.yaml"):
        (d / name).write_text("x")
    (d / "summary.yaml").write_text("x")  # not a replicate
    (d / "rep_abc.yaml").write_text("x")  # seed does not parse
    (d / "nested" / "rep_9.yaml").write_text("x")  # not a direct child

    assert LocalResultsStore(tmp_path).list_seeds(None, "decode", "intens") == [1, 2, 10]


def test_local_list_seeds_of_a_missing_directory_is_empty(tmp_path):
    assert LocalResultsStore(tmp_path).list_seeds(None, "never_ran", "intens") == []


def test_local_describe_is_the_path(tmp_path):
    assert LocalResultsStore(tmp_path).describe() == str(tmp_path)


# ---------------------------------------------------------------------------
# S3ResultsStore -- the append-only log
# ---------------------------------------------------------------------------


def s3_store(experiment="periodic_moe", base_prefix=""):
    return S3ResultsStore(
        bucket=BUCKET, base_prefix=base_prefix, experiment=experiment, region="us-west-2"
    )


def test_s3_key_scheme_matches_the_worked_example(fake_s3):
    """The exact key from the directive's worked example."""
    store = s3_store()
    store.dump_marks(
        sample_marks(),
        ReplicateAddress(tag="moe", info="extens", seed=1776, model="gpt-oss-120b"),
        TS1,
    )
    assert list(fake_s3.objects) == [
        "periodic_moe/gpt-oss-120b/seed=1776/extens--20260810T193000Z.yaml"
    ]


def test_s3_key_nests_under_the_uri_base_prefix(fake_s3):
    s3_store(base_prefix="archive/2026-08").dump_marks(sample_marks(), addr(), TS1)
    assert list(fake_s3.objects) == [
        "archive/2026-08/periodic_moe/stub-model/seed=1776/intens--20260810T193000Z.yaml"
    ]


def test_s3_dump_is_append_only(fake_s3):
    """THE LOG PROPERTY. A second run of the same (model, seed, info) ADDS an
    object; it must never overwrite the first. Losing the earlier run would
    make the bucket a mirror again rather than a log."""
    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    store.dump_marks(sample_marks(score=0), addr(), TS2)

    assert sorted(fake_s3.objects) == [
        "periodic_moe/stub-model/seed=1776/intens--20260810T193000Z.yaml",
        "periodic_moe/stub-model/seed=1776/intens--20260811T040506Z.yaml",
    ]


def test_s3_load_marks_returns_the_latest_run(fake_s3):
    store = s3_store()
    store.dump_marks(sample_marks(score=1), addr(), TS1)
    store.dump_marks(sample_marks(score=0), addr(), TS2)
    assert store.load_marks(addr()).marks[0].score == 0  # TS2 wins


def test_s3_load_marks_latest_is_independent_of_write_order(fake_s3):
    """Latest means latest TIMESTAMP, not last written. A late-arriving
    backfill of an older run must not displace a newer one."""
    store = s3_store()
    store.dump_marks(sample_marks(score=0), addr(), TS2)  # newer, written first
    store.dump_marks(sample_marks(score=1), addr(), TS1)  # older, written second
    assert store.load_marks(addr()).marks[0].score == 0


def test_s3_load_marks_raises_when_nothing_is_logged(fake_s3):
    with pytest.raises(FileNotFoundError):
        s3_store().load_marks(addr())


def test_s3_exists_uses_a_bounded_prefix_probe(fake_s3):
    """Resume-skip asks "has ANY run been logged", so it must be a prefix
    listing capped at one key -- not a fetch, and not an unbounded listing
    that pages through an experiment's whole history."""
    store = s3_store()
    assert not store.exists(addr())
    store.dump_marks(sample_marks(), addr(), TS1)
    assert store.exists(addr())

    probes = [c for c in fake_s3.calls if c[0] == "list_objects_v2"]
    assert probes, "exists must probe via list_objects_v2"
    prefix, max_keys = probes[-1][1], probes[-1][2]
    assert prefix == "periodic_moe/stub-model/seed=1776/intens--"
    assert max_keys == 1


def test_s3_exists_does_not_confuse_sibling_info_types(fake_s3):
    """The ``--`` separator is what stops ``intens`` from matching
    ``intens_extra``; a prefix of ``intens`` alone would."""
    store = s3_store()
    store.dump_marks(sample_marks(), addr(info="noise_intens"), TS1)
    assert store.exists(addr(info="noise_intens"))
    assert not store.exists(addr(info="intens"))


def test_s3_dump_refuses_a_model_less_address(fake_s3):
    """A model-less address is a READ shape; writing one must not silently
    create a literal ``None/`` model directory.

    Measured against the first implementation, it wrote
    ``periodic_moe/None/seed=1776/intens--<ts>.yaml``. In an APPEND-ONLY log
    that object is permanent -- no later correct write can supersede it, and
    only a manual delete removes it -- in a bucket whose whole point is to
    be a clean, browsable experiment log. Every other mistake in this design
    self-heals on the next run; this one does not.
    """
    with pytest.raises(ValueError):
        s3_store().dump_marks(sample_marks(), addr(model=None), TS1)
    assert fake_s3.objects == {}, "a refused write must leave no object behind"


def test_s3_exists_without_a_model_is_false(fake_s3):
    """A tag-keyed read (cot_chain_lengths) with no model behind the tag
    cannot address the log at all -- see ReplicateAddress.model."""
    assert not s3_store().exists(addr(model=None))


def test_s3_list_seeds_parses_the_log(fake_s3):
    store = s3_store()
    for seed in (1778, 1776):
        store.dump_marks(sample_marks(), addr(seed=seed), TS1)
    store.dump_marks(sample_marks(), addr(seed=1776), TS2)  # 2nd run, same seed
    store.dump_marks(sample_marks(), addr(seed=1777, info="extens"), TS1)  # other info

    assert store.list_seeds("stub-model", "decode", "intens") == [1776, 1778]
    assert store.list_seeds("stub-model", "decode", "extens") == [1777]


def test_s3_list_seeds_of_an_unlogged_model_is_empty(fake_s3):
    assert s3_store().list_seeds("never-served", "decode", "intens") == []


def test_s3_describe_is_the_log_uri(fake_s3):
    assert s3_store().describe() == f"s3://{BUCKET}/periodic_moe"
    assert (
        s3_store(base_prefix="archive").describe() == f"s3://{BUCKET}/archive/periodic_moe"
    )


def test_s3_client_is_built_with_the_configured_region(fake_s3):
    s3_store().exists(addr())
    assert fake_s3.requested == [("s3", "us-west-2")]


# ---------------------------------------------------------------------------
# resolve_store -- the env contract
# ---------------------------------------------------------------------------


def test_resolve_store_unset_env_is_local(tmp_path):
    store = resolve_store(tmp_path)
    assert isinstance(store, LocalResultsStore)
    assert store.root == tmp_path


def test_resolve_store_passes_the_prefix_to_the_local_store(tmp_path):
    assert resolve_store(tmp_path, "one_hop_").prefix == "one_hop_"


def test_resolve_store_non_repo_anchored_falls_back_to_local(s3_env, tmp_path):
    """THE HERMETICITY PROPERTY: tmp_path fixtures are outside the repo, so
    the offline suite keeps using the local store even when a developer's
    shell exports SMOLBENCH_RESULTS_S3."""
    assert isinstance(resolve_store(tmp_path / "results"), LocalResultsStore)


def test_resolve_store_repo_anchored_builds_the_log_store(s3_env):
    store = resolve_store(repo_root() / "notebooks" / "periodic_moe" / "results")
    assert isinstance(store, S3ResultsStore)
    assert store.bucket == BUCKET
    assert store.base_prefix == ""
    assert store.experiment == "periodic_moe"
    assert store.region == "us-west-2"


def test_resolve_store_carries_prefix_into_the_experiment(s3_env, fake_repo):
    store = resolve_store(fake_repo / "notebooks" / "chromatic" / "results", "one_hop_")
    assert store.experiment == "chromatic/one_hop"


def test_resolve_store_honours_a_base_prefix_in_the_uri(monkeypatch, fake_repo):
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", f"s3://{BUCKET}/archive/2026-08")
    store = resolve_store(fake_repo / "notebooks" / "periodic" / "results")
    assert (store.base_prefix, store.experiment) == ("archive/2026-08", "periodic")


def test_resolve_store_maps_a_directory_that_does_not_exist_locally(s3_env, fake_repo):
    """An S3-first run never creates the local tree, so the mapping must not
    depend on the directory existing."""
    store = resolve_store(fake_repo / "notebooks" / "brand_new" / "results")
    assert store.experiment == "brand_new"


def test_resolve_store_region_precedence(monkeypatch, fake_repo):
    results = fake_repo / "notebooks" / "periodic" / "results"
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3_REGION", "us-west-2")
    assert resolve_store(results).region == "us-west-2"
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3_REGION")
    assert resolve_store(results).region == "eu-central-1"
    monkeypatch.delenv("AWS_REGION")
    assert resolve_store(results).region is None


@pytest.mark.parametrize(
    "bad",
    [
        f"{BUCKET}",
        f"https://{BUCKET}/x",
        "s3://",
        "s3:///notebooks",
        "s3:/bucket/x",
        "s3://buck//archive",
        "s3://buck/arch//ive",
        "s3:// buck/archive",
        "s3://bu ck",
        "s3://buck/arch ive",
    ],
)
def test_resolve_store_malformed_uri_raises_value_error(monkeypatch, fake_repo, bad):
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", bad)
    with pytest.raises(ValueError):
        resolve_store(fake_repo / "notebooks" / "periodic" / "results")


def test_resolve_store_malformed_uri_raises_even_for_a_non_repo_path(
    monkeypatch, tmp_path
):
    """Validation happens BEFORE the repo-anchor check: a typo'd env var must
    always fail loudly rather than resolving local for every non-repo
    directory while the operator believes results are going to S3."""
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://")
    with pytest.raises(ValueError):
        resolve_store(tmp_path / "somewhere-else")


def test_parse_s3_uri_returns_bucket_and_base_prefix():
    assert parse_s3_uri(f"s3://{BUCKET}") == (BUCKET, "")
    assert parse_s3_uri(f"s3://{BUCKET}/") == (BUCKET, "")
    assert parse_s3_uri(f"s3://{BUCKET}/archive/2026-08/") == (BUCKET, "archive/2026-08")


# ---------------------------------------------------------------------------
# sync_down -- log to analysis-layout translation
# ---------------------------------------------------------------------------

TAGS = {"gpt-oss-120b": "moe", "stub-model": "decode"}


def log_key(model, seed, info, ts, experiment="periodic", base=""):
    head = f"{base}/" if base else ""
    return f"{head}{experiment}/{model}/seed={seed}/{info}--{format_run_ts(ts)}.yaml"


def test_sync_down_translates_the_log_into_the_analysis_layout(
    s3_env, fake_repo, fake_s3
):
    """The whole point of sync_down now: model -> TAG, timestamped log object
    -> ``{tag}_{info}/rep_{seed}.yaml``. The log cannot supply the tag, which
    is why the mapping is passed in."""
    results = fake_repo / "notebooks" / "periodic" / "results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = body

    assert sync_down(results, TAGS) == 2
    assert (results / "moe_extens" / "rep_1776.yaml").read_bytes() == body
    assert (results / "decode_intens" / "rep_1777.yaml").read_bytes() == body


def test_sync_down_writes_only_the_latest_run_per_replicate(s3_env, fake_repo, fake_s3):
    """Two logged runs, one local file, carrying the LATER run."""
    results = fake_repo / "notebooks" / "periodic" / "results"
    old = sample_marks(score=1).dumps().encode()
    new = sample_marks(score=0).dumps().encode()
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1)] = old
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS2)] = new

    assert sync_down(results, TAGS) == 1
    assert (results / "decode_intens" / "rep_1776.yaml").read_bytes() == new


def test_sync_down_honours_the_prefix_in_both_directions(monkeypatch, fake_repo, fake_s3):
    """A prefixed experiment reads from ``<nb>/one_hop`` and writes to
    ``one_hop_{tag}_{info}``."""
    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", URI)
    results = fake_repo / "notebooks" / "chromatic" / "results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[
        log_key("stub-model", 1776, "intens", TS1, experiment="chromatic/one_hop")
    ] = body

    assert sync_down(results, TAGS, "one_hop_") == 1
    assert (results / "one_hop_decode_intens" / "rep_1776.yaml").read_bytes() == body


def test_sync_down_skips_only_on_an_etag_md5_match(s3_env, fake_repo, fake_s3):
    results = fake_repo / "notebooks" / "periodic" / "results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1)] = body
    (results / "decode_intens").mkdir(parents=True)
    (results / "decode_intens" / "rep_1776.yaml").write_bytes(body)

    assert sync_down(results, TAGS) == 0  # verified identical, not refetched


def test_sync_down_redownloads_a_same_size_but_different_file(
    s3_env, fake_repo, fake_s3
):
    """THE REGRADE BUG, retained across the rework.

    ``scripts/regrade.py --write`` rewrites replicate YAMLs in place, and a
    score 1 -> 0 flip is byte-length preserving (147 bytes either way,
    different MD5). A size-only skip therefore left a stale local verdict in
    place. These two bodies are byte-length-equal by construction, so this
    fails against any size-based implementation.
    """
    results = fake_repo / "notebooks" / "periodic" / "results"
    remote = sample_marks(n=1, score=1).dumps().encode()
    local = sample_marks(n=1, score=0).dumps().encode()
    assert len(remote) == len(local) and remote != local, "premise"

    fake_s3.objects[log_key("stub-model", 1776, "intens", TS1)] = remote
    (results / "decode_intens").mkdir(parents=True)
    (results / "decode_intens" / "rep_1776.yaml").write_bytes(local)

    assert sync_down(results, TAGS) == 1
    assert (results / "decode_intens" / "rep_1776.yaml").read_bytes() == remote


def test_sync_down_redownloads_when_the_etag_is_multipart(s3_env, fake_repo, fake_s3):
    results = fake_repo / "notebooks" / "periodic" / "results"
    body = sample_marks().dumps().encode()
    key = log_key("stub-model", 1776, "intens", TS1)
    fake_s3.objects[key] = body
    fake_s3.etags[key] = f'"{hashlib.md5(body).hexdigest()}-2"'
    (results / "decode_intens").mkdir(parents=True)
    (results / "decode_intens" / "rep_1776.yaml").write_bytes(body)

    assert sync_down(results, TAGS) == 1  # cannot verify -> refetch


def test_sync_down_refuses_a_key_that_escapes_results_dir(s3_env, fake_repo, fake_s3):
    """A tag containing path syntax must not walk out of the results tree."""
    results = fake_repo / "notebooks" / "periodic" / "results"
    fake_s3.objects[log_key("evil-model", 1776, "intens", TS1)] = b"pwned"

    with pytest.raises(ValueError):
        sync_down(results, {"evil-model": "../../ESCAPED"})
    assert not (fake_repo / "ESCAPED_intens").exists()


def test_sync_down_without_the_env_var_raises_a_clear_error(fake_repo):
    with pytest.raises(RuntimeError) as err:
        sync_down(fake_repo / "notebooks" / "periodic" / "results", TAGS)
    assert "SMOLBENCH_RESULTS_S3" in str(err.value)


def test_sync_down_of_a_non_repo_directory_names_both_paths(s3_env, tmp_path):
    outside = tmp_path / "elsewhere"
    with pytest.raises(RuntimeError) as err:
        sync_down(outside, TAGS)
    message = str(err.value)
    assert str(outside) in message and str(repo_root()) in message


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_parses_repeatable_tag_arguments(s3_env, fake_repo, fake_s3, capsys):
    results = fake_repo / "notebooks" / "periodic" / "results"
    body = sample_marks().dumps().encode()
    fake_s3.objects[log_key("gpt-oss-120b", 1776, "extens", TS1)] = body
    fake_s3.objects[log_key("stub-model", 1777, "intens", TS1)] = body

    rc = rs.main([str(results), "--tag", "gpt-oss-120b=moe", "--tag", "stub-model=decode"])
    out = capsys.readouterr().out

    assert rc == 0
    assert (results / "moe_extens" / "rep_1776.yaml").is_file()
    assert (results / "decode_intens" / "rep_1777.yaml").is_file()
    assert str(results) in out


def test_cli_rejects_a_tag_argument_without_an_equals(s3_env, fake_repo, fake_s3):
    results = fake_repo / "notebooks" / "periodic" / "results"
    with pytest.raises(SystemExit):
        rs.main([str(results), "--tag", "no-equals-sign"])


def test_cli_accepts_a_prefix(s3_env, fake_repo, fake_s3):
    results = fake_repo / "notebooks" / "chromatic" / "results"
    fake_s3.objects[
        log_key("stub-model", 1776, "intens", TS1, experiment="chromatic/one_hop")
    ] = sample_marks().dumps().encode()

    assert rs.main([str(results), "--tag", "stub-model=decode", "--prefix", "one_hop_"]) == 0
    assert (results / "one_hop_decode_intens" / "rep_1776.yaml").is_file()


# ---------------------------------------------------------------------------
# ReplicateHarness on the S3 log (integration)
# ---------------------------------------------------------------------------


def _quizzes(seed: int, model: str):
    from smolbench.evals import Numeric

    return {
        "intens": (
            Numeric(prompt=f"i1/{seed}", answer=1),
            Numeric(prompt=f"i2/{seed}", answer=2),
        ),
        "extens": (Numeric(prompt=f"e1/{seed}", answer=3),),
    }


@pytest.fixture
def s3_harness(fake_repo, s3_env, fake_s3):
    from smolbench.evals.replicates import ReplicateHarness

    return ReplicateHarness(
        results_dir=fake_repo / "notebooks" / "periodic_moe" / "results",
        archetype_tags={"stub-model": "decode"},
        make_quizzes=_quizzes,
        seeds=(1, 2),
        info_types=("intens", "extens"),
    )


@pytest.fixture
def fake_evaluate(monkeypatch):
    from smolbench.evals import provider

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


def test_harness_store_resolves_to_the_log_and_is_cached(s3_harness):
    assert isinstance(s3_harness.store, S3ResultsStore)
    assert s3_harness.store.experiment == "periodic_moe"
    assert s3_harness.store is s3_harness.store  # cached_property


def test_harness_run_writes_the_log_and_nothing_locally(
    s3_harness, fake_evaluate, fake_s3, freeze_ts
):
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


def test_harness_pooled_infos_of_one_seed_share_a_timestamp(
    s3_harness, fake_evaluate, fake_s3, monkeypatch
):
    """One collection event, one timestamp.

    Both info types of a seed come from a SINGLE pooled evaluate() call, so
    they are one event and must be attributable as such. A timestamp taken
    per-dump would split them by however long serialization happened to
    take, and could even straddle a second boundary.
    """
    stamps = iter([TS1, TS2, TS1, TS2])  # one per call, so a per-dump call would differ
    monkeypatch.setattr(rs, "utcnow", lambda: next(stamps))
    from smolbench.evals import replicates

    if hasattr(replicates, "utcnow"):
        monkeypatch.setattr(replicates, "utcnow", lambda: next(stamps), raising=False)

    s3_harness.run_replicates("stub-model")

    for seed in (1, 2):
        seed_keys = [k for k in fake_s3.objects if f"seed={seed}/" in k]
        assert len(seed_keys) == 2
        assert len({k.rsplit("--", 1)[1] for k in seed_keys}) == 1, seed_keys


def test_harness_rerun_appends_a_second_run(
    s3_harness, fake_evaluate, fake_s3, freeze_ts
):
    """Append-only end to end: a forced re-run logs alongside the first."""
    freeze_ts(TS1)
    s3_harness.run_replicates("stub-model")
    first = set(fake_s3.objects)

    # Resume-skip would normally stop a re-run; write directly to prove the
    # log accumulates rather than overwriting.
    freeze_ts(TS2)
    s3_harness.store.dump_marks(
        sample_marks(score=0),
        ReplicateAddress(tag="decode", info="intens", seed=1, model="stub-model"),
        TS2,
    )
    assert set(fake_s3.objects) > first
    assert len(fake_s3.objects) == len(first) + 1


def test_harness_resume_skips_anything_already_logged(
    s3_harness, fake_evaluate, fake_s3, freeze_ts
):
    """Any logged run counts as done, whatever its timestamp."""
    freeze_ts(TS1)
    for info in ("intens", "extens"):
        fake_s3.objects[
            log_key("stub-model", 1, info, TS1, experiment="periodic_moe")
        ] = Marks(model="stub-model", marks=()).dumps().encode()

    s3_harness.run_replicates("stub-model")
    assert [(c["seed"], c["n"]) for c in fake_evaluate] == [(2, 3)]


def test_harness_has_outstanding_reads_the_log(s3_harness, fake_s3, freeze_ts):
    assert s3_harness.has_outstanding("stub-model")
    for seed in (1, 2):
        for info in ("intens", "extens"):
            fake_s3.objects[
                log_key("stub-model", seed, info, TS1, experiment="periodic_moe")
            ] = Marks(model="stub-model", marks=()).dumps().encode()
    assert not s3_harness.has_outstanding("stub-model")
    assert not s3_harness.results_dir.exists()


def test_harness_summarize_uses_the_latest_run(s3_harness, fake_s3, capsys):
    """Printed format is byte-identical, the count is distinct seeds, and the
    tallies come from the LATEST logged run of each replicate."""
    for seed in (1, 2):
        fake_s3.objects[
            log_key("stub-model", seed, "intens", TS1, experiment="periodic_moe")
        ] = sample_marks(n=2, score=1).dumps().encode()
        fake_s3.objects[
            log_key("stub-model", seed, "intens", TS2, experiment="periodic_moe")
        ] = sample_marks(n=2, score=0).dumps().encode()

    s3_harness.summarize("stub-model")
    out = capsys.readouterr().out
    # Latest run scored 0 -> 4 incorrect, not 4 correct.
    assert "decode/intens: 2/2 replicates -- correct=0 incorrect=4 invalid=0 acc=0.000" in out
    assert "decode/extens: 0/2 replicates -- correct=0 incorrect=0 invalid=0 acc=n/a" in out


def test_harness_sync_down_translates_without_being_told_the_tags(
    s3_harness, fake_s3, freeze_ts
):
    """``ReplicateHarness.sync_down()`` is the primary entry point precisely
    because it already knows archetype_tags and prefix."""
    body = sample_marks().dumps().encode()
    fake_s3.objects[
        log_key("stub-model", 1776, "extens", TS1, experiment="periodic_moe")
    ] = body

    assert s3_harness.sync_down() == 1
    assert (
        s3_harness.results_dir / "decode_extens" / "rep_1776.yaml"
    ).read_bytes() == body


def test_run_replicates_logs_the_store_target(
    s3_harness, fake_evaluate, caplog, freeze_ts
):
    import logging

    freeze_ts(TS1)
    with caplog.at_level(logging.INFO):
        s3_harness.run_replicates("stub-model")
    assert f"s3://{BUCKET}/periodic_moe" in caplog.text
