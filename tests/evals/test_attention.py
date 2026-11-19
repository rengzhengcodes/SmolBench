"""The store-agnostic capture client: key classes, mass jobs, verification and the batch runner.

Offline: a dict-backed S3 fake whose presigned URLs encode the key, and a fake box that
"uploads" through those URLs exactly as the on-box plugin would, then scripts ``/status``.
"""
from __future__ import annotations

import io
import json
from typing import Any

import numpy as np
import pytest
from botocore.exceptions import ClientError

from smolbench.evals import attention


class FakeS3:
    """Dict-backed S3 client: the calls the capture client makes, nothing more."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.presigned: list[str] = []
        self.puts: list[str] = []
        self.if_none_match: list[Any] = []  # the IfNoneMatch of each put, None when absent
        self.page_size: int | None = None  # keys per list_objects_v2 page; None = a single page
        self.list_calls = 0

    def put_object(self, Bucket: str, Key: str, Body: bytes, IfNoneMatch: Any = None, **_: Any) -> None:
        self.if_none_match.append(IfNoneMatch)
        # S3's conditional write: "*" refuses to replace an existing key.
        if IfNoneMatch == "*" and Key in self.objects:
            raise ClientError({"Error": {"Code": "PreconditionFailed"},
                               "ResponseMetadata": {"HTTPStatusCode": 412}}, "PutObject")
        self.puts.append(Key)
        self.objects[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> dict:
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def head_object(self, Bucket: str, Key: str) -> dict:
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {"ContentLength": len(self.objects[Key])}

    def list_objects_v2(self, Bucket: str, Prefix: str = "", ContinuationToken: Any = None,
                        **_: Any) -> dict:
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        self.list_calls += 1
        # One page holding everything, unless a test sets ``page_size``; then the token is
        # the index of the first key of the next page, as an opaque string.
        start = int(ContinuationToken) if ContinuationToken is not None else 0
        stop = len(keys) if self.page_size is None else start + self.page_size
        page = {"Contents": [{"Key": k, "Size": len(self.objects[k])} for k in keys[start:stop]],
                "IsTruncated": stop < len(keys)}
        if stop < len(keys):
            page["NextContinuationToken"] = str(stop)
        return page

    def generate_presigned_url(self, op: str, Params: dict, ExpiresIn: int) -> str:
        assert op == "put_object"
        self.presigned.append(Params["Key"])
        # Mirror a SigV4 URL: the signed-headers list names If-None-Match only when the
        # condition was passed, as boto3 does under signature_version="s3v4".
        signed = "content-type%3Bhost" + ("%3Bif-none-match" if Params.get("IfNoneMatch") == "*" else "")
        return f"https://signed/{Params['Key']}?ttl={ExpiresIn}&X-Amz-SignedHeaders={signed}"


def mass_npz(n_tokens: int, query_start: int, classes: list[int], *, heads: int = 2,
             broken: bool = False) -> bytes:
    """One rank's mass-mode upload: mass ``[L, P, H, 4]``, entropy/sink ``[L, P, H]``, classes ``[T]``."""
    rows = n_tokens - query_start - (1 if broken else 0)
    mass = np.zeros((2, rows, heads, 4), np.float16)
    mass[..., 1], mass[..., 3] = 0.25, 0.75
    buf = io.BytesIO()
    np.savez(buf, mass=mass, entropy=np.zeros((2, rows, heads), np.float16),
             sink=np.zeros((2, rows, heads), np.float16),
             classes=np.asarray(classes, np.uint8), query_start=np.asarray(query_start, np.int32),
             layers=np.arange(2, dtype=np.int32), positions=np.asarray([n_tokens - 1], np.int32))
    return buf.getvalue()


class FakeBox:
    """Stand-in for ``ec2``'s ``attn_start``/``attn_status``: uploads through the minted URLs."""

    def __init__(self, s3: FakeS3) -> None:
        self.s3 = s3
        self.batches: list[dict] = []
        self.gate_failures: set[str] = set()
        self.missing: set[str] = set()
        self.bad_shape: set[str] = set()
        self._status: list[dict] = []

    def attn_start(self, state: dict, payload: dict) -> dict:
        self.batches.append(payload)
        results: dict[str, dict] = {}
        for line in payload["jobs"]:
            jid = line["job_id"]
            if jid in self.missing:
                continue
            n = len(line["prompt_token_ids"]) + len(line["completion_token_ids"])
            ranks = {}
            for rank in range(payload["tp"]):
                blob = mass_npz(n, line["query_start"], line["classes"], broken=jid in self.bad_shape)
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.objects[key] = blob
                self.s3.objects[meta_key] = json.dumps(
                    {"n_tokens": n, "bytes": len(blob), "mode": "mass",
                     "query_start": line["query_start"], "rank": rank}).encode()
                ok = not (rank == 0 and jid in self.gate_failures)
                ranks[str(rank)] = {"ok": ok, "error": None if ok else "gate 0.4 > 0.03",
                                    "gate_max_rel": 0.001 if ok else 0.4}
            results[jid] = ranks
        self._status = [{"running": True, "results": {}},
                        {"running": False, "results": results, "error": None}]
        return {"ok": True}

    def attn_status(self, state: dict) -> dict:
        return self._status.pop(0) if len(self._status) > 1 else self._status[0]


def job(job_id: str, n_prompt: int, n_completion: int, prefix: str = "p/run/") -> attention.Job:
    prompt, completion = tuple(range(n_prompt)), tuple(range(n_completion))
    classes = [0] * n_prompt + [3] * n_completion
    return attention.mass_job(job_id, prompt, completion, classes, f"{prefix}{job_id}.npz")


def run(box: FakeBox, s3: FakeS3, jobs, *, tp: int = 2, batch_size: int = 16, factory=None):
    return attention.run_capture_batches(
        box, {"public_ip": "x"}, "served", jobs, tp, factory or (lambda: s3), "bucket",
        batch_size=batch_size, url_ttl_s=99, batch_timeout_s=10, poll_s=0)


# ------------------------------------------------------------------ key classes

#: A 4-char whitespace pad unit, a newline, an empty special, and two text tokens (one
#: CONTAINS a space, so whitespace-only must not be confused with contains-whitespace).
CLASS_TABLE = {1: "The", 2: " answer", 3: "\n", 4: " \t  ", 5: "", 6: "."}


def decode(ids):
    return [CLASS_TABLE[int(i)] for i in ids]


def test_token_classes_labels_only_the_prompts_long_whitespace_run() -> None:
    """Class 1 is the noise arm's pad run; short runs, specials and text are 2/0, completions 3."""
    prompt = (5, 1, 2, 3, 6) + (4,) * 10  # one 40-char whitespace run at the end
    assert attention.token_classes(prompt, (1, 2), decode) == [2, 0, 0, 2, 0] + [1] * 10 + [3, 3]
    # 20 chars is below the 32-char floor: nothing is class 1.
    assert attention.token_classes((1, 6) + (4,) * 5, (2,), decode) == [0, 0] + [2] * 5 + [3]
    # Two equal 32-char runs: the FIRST wins, the second is ordinary whitespace.
    two_runs = (4,) * 8 + (6,) + (4,) * 8
    assert attention.token_classes(two_runs, (1,), decode) == [1] * 8 + [0] + [2] * 8 + [3]
    with pytest.raises(ValueError, match="one piece per token"):
        attention.token_classes((1, 2), (), lambda ids: ["x"])


#: Pieces for the ``pad_span`` tests; the prompt text of ``SPAN_PROMPT`` is ``"The.ab..\nThe"``
#: with token spans The 0-3, "." 3-4, "ab." 4-7, "." 7-8, "\n" 8-9, The 9-12.
SPAN_TABLE = {**CLASS_TABLE, 7: "ab."}
SPAN_PROMPT = (1, 6, 7, 6, 3, 1)


def span_decode(ids):
    return [SPAN_TABLE[int(i)] for i in ids]


def test_pad_span_labels_exactly_the_tokens_inside_it() -> None:
    """Non-whitespace tokens inside the span are class 1; the rest keep their class 0/2."""
    got = attention.token_classes(SPAN_PROMPT, (1,), span_decode, pad_span=(4, 8))
    assert got == [0, 0, 1, 1, 2, 0, 3]
    # The "\n" right after the span is whitespace outside it: class 2, not 1.
    assert attention.token_classes(SPAN_PROMPT, (), span_decode, pad_span=(0, 12)) == [1] * 6
    # An empty piece inside the span is a template token, not a pad token.
    assert attention.token_classes((1, 5, 6), (), span_decode, pad_span=(0, 4)) == [1, 2, 1]
    # An empty span is valid and labels nothing.
    assert attention.token_classes(SPAN_PROMPT, (), span_decode, pad_span=(4, 4)) == [0, 0, 0, 0, 2, 0]


def test_pad_span_never_labels_a_token_that_straddles_an_edge() -> None:
    # Left edge at 5 cuts "ab." (4-7): that token is text, the "." after it is pad.
    assert attention.token_classes(SPAN_PROMPT, (), span_decode, pad_span=(5, 8)) == [0, 0, 0, 1, 2, 0]
    # Right edge at 6 cuts the same token from the other side.
    assert attention.token_classes(SPAN_PROMPT, (), span_decode, pad_span=(4, 6)) == [0, 0, 0, 0, 2, 0]
    # A straddling whitespace token takes class 2, as any whitespace outside the pad.
    assert attention.token_classes((1, 4), (), span_decode, pad_span=(2, 5)) == [0, 2]


def test_pad_span_replaces_the_whitespace_run_rule() -> None:
    """With a span, a long whitespace run elsewhere is NOT class 1; without one it still is."""
    prompt = (1,) + (4,) * 10 + (6,)  # "The", a 40-char whitespace run, "."
    by_rule = [0] + [1] * 10 + [0]
    assert attention.token_classes(prompt, (), span_decode) == by_rule
    assert attention.token_classes(prompt, (), span_decode, pad_span=None) == by_rule
    assert attention.token_classes(prompt, (), span_decode, pad_span=(0, 3)) == [1] + [2] * 10 + [0]
    assert attention.token_classes(prompt, (), span_decode, pad_span=(3, 43)) == [0] + [1] * 10 + [0]


@pytest.mark.parametrize("span", [(-1, 2), (3, 2), (0, 13), (13, 13)])
def test_pad_span_outside_the_prompt_text_is_refused(span) -> None:
    with pytest.raises(ValueError, match="pad_span"):
        attention.token_classes(SPAN_PROMPT, (), span_decode, pad_span=span)


def test_mass_job_gates_inside_the_completion_and_refuses_malformed_jobs() -> None:
    j = job("s0.intens.ts.q0", 10, 9)
    assert j.mode == "mass" and j.query_start == 10 and j.n_tokens == 19
    assert j.positions == (13, 16, 18)  # one third, two thirds, last
    assert attention.mass_gate_positions(5, 1) == (5,)
    assert j.mass_keys()["classes"] == [0] * 10 + [3] * 9
    good = dict(job_id="q0", prompt_token_ids=(1, 2), completion_token_ids=(3,),
                classes=[0, 0, 3], key="p/q0.npz")
    for bad, match in [({"completion_token_ids": ()}, "empty|completion"),
                       ({"classes": [0, 0]}, "classes"),
                       ({"classes": [0, 3, 3]}, "class"),
                       ({"classes": [0, 0, 0]}, "class"),
                       ({"classes": [0, 7, 3]}, "class"),
                       ({"key": "p/q0.json"}, "npz"),
                       ({"job_id": "a:b"}, "job_id|id")]:
        with pytest.raises(ValueError, match=match):
            attention.mass_job(**{**good, **bad})


def test_rank_keys_name_one_object_pair_per_tensor_parallel_rank() -> None:
    assert attention.rank_keys("p/attn/q3.npz", 1) == ("p/attn/q3.r1.npz", "p/attn/q3.r1.json")


# ----------------------------------------------------------------- verification

def _upload(s3: FakeS3, j: attention.Job, tp: int = 2, **kw: Any) -> None:
    for rank in range(tp):
        npz, meta = attention.rank_keys(j.key, rank)
        blob = mass_npz(j.n_tokens, j.query_start, list(j.classes), **kw)
        s3.objects[npz] = blob
        s3.objects[meta] = json.dumps({"n_tokens": j.n_tokens, "bytes": len(blob)}).encode()


def test_verify_capture_uploads_checks_every_rank_and_the_mass_arrays() -> None:
    s3 = FakeS3()
    jobs = [job("q0", 5, 3), job("q1", 6, 2)]
    for j in jobs:
        _upload(s3, j)
    assert attention.verify_capture_uploads(s3, "b", jobs, 2, sample=2, mode="mass") == (["q0", "q1"], [])
    # The same objects checked as rows fail: the two modes never certify each other.
    assert attention.verify_capture_uploads(s3, "b", jobs[:1], 2, mode="rows") == ([], ["q0"])
    # A missing rank fails the job even though rank 0 is perfect.
    del s3.objects["p/run/q1.r1.npz"]
    assert attention.verify_capture_uploads(s3, "b", jobs, 2, sample=2, mode="mass") == (["q0"], ["q1"])
    # Wrong P is a content failure, not an existence one.
    _upload(s3, jobs[0], broken=True)
    assert attention.verify_capture_uploads(s3, "b", jobs[:1], 2, mode="mass") == ([], ["q0"])


# ------------------------------------------------------------------ batch runner

def test_run_capture_batches_sends_longest_first_and_verifies_every_rank() -> None:
    s3, jobs = FakeS3(), [job("short", 3, 2), job("long", 30, 10), job("mid", 10, 5)]
    box = FakeBox(s3)
    result = run(box, s3, jobs, batch_size=2)
    assert [[line["job_id"] for line in b["jobs"]] for b in box.batches] == [["long", "mid"], ["short"]]
    assert sorted(result.verified) == ["long", "mid", "short"] and result.failed == {}
    assert result.gates["long"] == {"0": 0.001, "1": 0.001}
    line = box.batches[0]["jobs"][0]
    assert line["mode"] == "mass" and line["query_start"] == 30 and len(line["classes"]) == 40
    assert len(line["put_urls"]) == len(line["meta_put_urls"]) == 2
    assert box.batches[0]["served_model_name"] == "served" and box.batches[0]["tp"] == 2


def test_a_failed_rank_a_missing_job_or_a_bad_shape_fails_the_job() -> None:
    s3 = FakeS3()
    box = FakeBox(s3)
    box.gate_failures, box.missing, box.bad_shape = {"a"}, {"b"}, {"c"}
    result = run(box, s3, [job("a", 4, 2), job("b", 5, 2), job("c", 6, 2), job("d", 3, 2)], batch_size=1)
    assert result.verified == ["d"]
    assert set(result.failed) == {"a", "b", "c"}
    assert "ok=false" in result.failed["a"] and "never reported" in result.failed["b"]
    assert result.gates["a"]["0"] == 0.4  # the failing rank's gate is still on record


def test_an_existing_capture_is_skipped_and_never_overwritten() -> None:
    """Append-only: no presigned PUT is ever minted for a key that already exists."""
    s3 = FakeS3()
    done, partial, fresh = job("done", 5, 3), job("partial", 6, 3), job("fresh", 4, 2)
    _upload(s3, done)
    s3.objects["p/run/partial.r0.json"] = b"{}"
    before = dict(s3.objects)
    box = FakeBox(s3)
    result = run(box, s3, [done, partial, fresh])
    assert set(result.skipped_existing) == {"done", "partial"}
    assert result.skipped_existing["partial"] == ["p/run/partial.r0.json"]
    assert [line["job_id"] for b in box.batches for line in b["jobs"]] == ["fresh"]
    assert not any(k in before for k in s3.presigned), "a URL was minted for an existing key"
    assert {k: s3.objects[k] for k in before} == before
    # A second invocation finds everything present and starts no batch at all.
    box2 = FakeBox(s3)
    again = run(box2, s3, [done, partial, fresh])
    assert box2.batches == [] and set(again.skipped_existing) == {"done", "partial", "fresh"}


def test_bad_arguments_raise_before_the_box_or_the_bucket_is_touched() -> None:
    def never():
        raise AssertionError("S3 client built")

    box = FakeBox(FakeS3())
    for jobs, kw, match in [([job("x", 3, 2), job("x", 4, 2)], {}, "x"),
                            ([job("x", 3, 2)], {"tp": 0}, "tp"),
                            ([job("x", 3, 2)], {"batch_size": 0}, "batch")]:
        with pytest.raises(ValueError, match=match):
            run(box, None, jobs, factory=never, **kw)
    with pytest.raises(ValueError, match="must exceed"):
        attention.run_capture_batches(box, {}, "s", [job("x", 3, 2)], 1, never, "b",
                                      url_ttl_s=10, batch_timeout_s=10)
    assert box.batches == []


def test_a_fresh_client_is_built_for_every_batch() -> None:
    s3, built = FakeS3(), []

    def factory():
        built.append(1)
        return s3

    run(FakeBox(s3), s3, [job("a", 3, 2), job("b", 4, 2), job("c", 5, 2)], batch_size=1, factory=factory)
    assert len(built) >= 3


# ------------------------------------------------------------ no-overwrite presigned PUT

def _offline_boto3_s3(monkeypatch, config=None):
    """A real boto3 S3 client with static fake credentials and no user config (presigning is offline)."""
    import boto3

    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/dev/null")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/dev/null")
    return boto3.session.Session().client(
        "s3", region_name="us-west-2", aws_access_key_id="AKIDEXAMPLE",
        aws_secret_access_key="x" * 40, config=config)


def _signed_headers(url: str) -> list[str]:
    from urllib.parse import parse_qs, urlsplit

    values = parse_qs(urlsplit(url).query).get("X-Amz-SignedHeaders", [""])
    return values[0].split(";") if values[0] else []


def test_presign_put_signs_if_none_match_into_a_sigv4_url(monkeypatch) -> None:
    """The URL itself carries the no-overwrite condition: S3 then refuses a PUT onto an existing key."""
    from botocore.config import Config

    client = _offline_boto3_s3(monkeypatch, Config(signature_version="s3v4"))
    url = attention.presign_put(client, "smolbench-rebuttals-414266451290",
                                "bedrock-trio/attention/q0.r0.npz", "application/octet-stream", 60)
    headers = _signed_headers(url)
    assert "if-none-match" in headers and "content-type" in headers, url


def test_presign_put_refuses_a_client_that_drops_the_condition(monkeypatch) -> None:
    """A default boto3 client presigns S3 with SigV2, which silently drops IfNoneMatch: refuse it."""
    client = _offline_boto3_s3(monkeypatch)
    with pytest.raises(ValueError, match="(?i)if-none-match"):
        attention.presign_put(client, "smolbench-rebuttals-414266451290",
                              "bedrock-trio/attention/q0.r0.npz", "application/octet-stream", 60)


def test_presign_put_passes_the_condition_to_the_signer() -> None:
    s3 = FakeS3()
    url = attention.presign_put(s3, "b", "p/q0.r0.json", "application/json", 30)
    assert "if-none-match" in _signed_headers(url.replace("%3B", ";"))


# ------------------------------------------------------------------ summary mode

def summary_npz(n_tokens: int, query_start: int, classes: list[int], *, heads: int = 2,
                layers: int = 2, rows_delta: int = 0, sum_mass_heads: int | None = None) -> bytes:
    """One rank's summary-mode upload: ``rows`` scalar and per-(layer, head) float64 sums."""
    p = n_tokens - query_start
    shape = (layers, heads)
    arrays = {name: np.zeros(shape, np.float64) for name in (
        "sum_entropy", "sum_prompt_entropy", "sum_sink", "sum_pad_ratio", "sum_m_hp",
        "sum_chain_hi", "sum_chain_lo")}
    arrays["n_prompt_entropy"] = np.full(shape, p, np.int64)
    arrays["n_pad_ratio"] = np.zeros(shape, np.int64)
    arrays["sum_mass"] = np.zeros((layers, sum_mass_heads or heads, 4), np.float64)
    arrays["sum_mass"][..., 3] = p
    buf = io.BytesIO()
    np.savez(buf, rows=np.asarray(p + rows_delta, np.int64), capture_version=np.asarray(3, np.int32),
             classes=np.asarray(classes, np.uint8), query_start=np.asarray(query_start, np.int32),
             layers=np.arange(layers, dtype=np.int32), positions=np.asarray([n_tokens - 1], np.int32),
             **arrays)
    return buf.getvalue()


def summary_job(job_id: str, n_prompt: int, n_completion: int, prefix: str = "p/run/") -> attention.Job:
    prompt, completion = tuple(range(n_prompt)), tuple(range(n_completion))
    classes = [0] * n_prompt + [3] * n_completion
    return attention.mass_job(job_id, prompt, completion, classes, f"{prefix}{job_id}.npz", mode="summary")


def test_summary_is_a_capture_mode_and_the_job_carries_its_mode() -> None:
    assert attention.CAPTURE_MODES == ("rows", "mass", "summary")
    j = summary_job("s100.rep0", 10, 9)
    assert j.mode == "summary" and j.query_start == 10 and j.positions == (13, 16, 18)
    keys = j.mass_keys()
    assert keys == {"mode": "summary", "query_start": 10, "classes": [0] * 10 + [3] * 9}
    # The default stays mass, and a rows job cannot be built by the class-labelled builder.
    assert job("q0", 3, 2).mass_keys()["mode"] == "mass"
    with pytest.raises(ValueError, match="mode"):
        attention.mass_job("q0", (1,), (2,), [0, 3], "p/q0.npz", mode="rows")
    with pytest.raises(ValueError, match="mode"):
        attention.mass_job("q0", (1,), (2,), [0, 3], "p/q0.npz", mode="sum")
    # The summary job is validated exactly like a mass job.
    with pytest.raises(ValueError, match="class"):
        attention.mass_job("q0", (1,), (2,), [3, 3], "p/q0.npz", mode="summary")


def test_summary_arrays_constant_names_every_summed_array() -> None:
    assert set(attention.SUMMARY_ARRAYS) == {
        "rows", "sum_entropy", "sum_prompt_entropy", "n_prompt_entropy", "sum_mass", "sum_sink",
        "sum_pad_ratio", "n_pad_ratio", "sum_m_hp", "sum_chain_hi", "sum_chain_lo"}


def _upload_summary(s3: FakeS3, j: attention.Job, tp: int = 2, **kw: Any) -> None:
    for rank in range(tp):
        npz, meta = attention.rank_keys(j.key, rank)
        blob = summary_npz(j.n_tokens, j.query_start, list(j.classes), **kw)
        s3.objects[npz] = blob
        s3.objects[meta] = json.dumps({"n_tokens": j.n_tokens, "bytes": len(blob)}).encode()


def test_verify_capture_uploads_checks_the_summary_arrays_and_never_crosses_modes() -> None:
    s3 = FakeS3()
    jobs = [summary_job("a", 5, 3), summary_job("b", 6, 2)]
    for j in jobs:
        _upload_summary(s3, j)
    assert attention.verify_capture_uploads(s3, "b", jobs, 2, sample=2, mode="summary") == (["a", "b"], [])
    # A summary upload is not a mass upload, and a mass upload is not a summary upload.
    assert attention.verify_capture_uploads(s3, "b", jobs[:1], 2, mode="mass") == ([], ["a"])
    m = job("m", 5, 3)
    _upload(s3, m)
    assert attention.verify_capture_uploads(s3, "b", [m], 2, mode="summary") == ([], ["m"])
    # rows must be P, the sums must share their [L, H] shape, and classes must cover every token.
    for kw in ({"rows_delta": 1}, {"sum_mass_heads": 3}):
        _upload_summary(s3, jobs[0], **kw)
        assert attention.verify_capture_uploads(s3, "b", jobs[:1], 2, mode="summary") == ([], ["a"]), kw
    short = summary_job("c", 5, 3)
    for rank in range(2):
        npz, meta = attention.rank_keys(short.key, rank)
        blob = summary_npz(short.n_tokens, short.query_start, list(short.classes)[:-1])
        s3.objects[npz] = blob
        s3.objects[meta] = json.dumps({"n_tokens": short.n_tokens, "bytes": len(blob)}).encode()
    assert attention.verify_capture_uploads(s3, "b", [short], 2, mode="summary") == ([], ["c"])


class SummaryBox(FakeBox):
    """FakeBox that uploads summary arrays, as the plugin does for a summary job."""

    def attn_start(self, state: dict, payload: dict) -> dict:
        self.batches.append(payload)
        results: dict[str, dict] = {}
        for line in payload["jobs"]:
            assert line["mode"] == "summary"
            n = len(line["prompt_token_ids"]) + len(line["completion_token_ids"])
            ranks = {}
            for rank in range(payload["tp"]):
                blob = summary_npz(n, line["query_start"], line["classes"])
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.objects[key] = blob
                self.s3.objects[meta_key] = json.dumps({"n_tokens": n, "bytes": len(blob)}).encode()
                ranks[str(rank)] = {"ok": True, "error": None, "gate_max_rel": 0.001}
            results[line["job_id"]] = ranks
        self._status = [{"running": False, "results": results, "error": None}]
        return {"ok": True}


def test_run_capture_batches_sends_summary_jobs_and_verifies_their_arrays() -> None:
    s3 = FakeS3()
    box = SummaryBox(s3)
    jobs = [summary_job("x", 4, 3), summary_job("y", 6, 2)]
    result = attention.run_capture_batches(
        box, {"public_ip": "x"}, "served", jobs, 2, lambda: s3, "bucket", mode="summary",
        url_ttl_s=99, batch_timeout_s=10, poll_s=0)
    assert sorted(result.verified) == ["x", "y"] and result.failed == {}
    line = box.batches[0]["jobs"][0]
    assert line["mode"] == "summary" and line["query_start"] == 6 and len(line["classes"]) == 8
    # A mass job in a summary run is refused before anything is touched.
    with pytest.raises(ValueError, match="mode"):
        attention.run_capture_batches(box, {}, "s", [job("z", 3, 2)], 1, lambda: s3, "b",
                                      mode="summary", url_ttl_s=99, batch_timeout_s=10)


# ------------------------------------------------------------------ engine death

#: The agent's ``{"error": str(exc)}`` wording for each way a dead vLLM answers (copied from
#: a real run's log): the in-flight request gets a 500, later ones a reset, a broken pipe or
#: a refused connection once the server is gone.
ENGINE_500 = "HTTP Error 500: Internal Server Error"
ENGINE_RESET = "[Errno 104] Connection reset by peer"
ENGINE_PIPE = "<urlopen error [Errno 32] Broken pipe>"
ENGINE_REFUSED = "<urlopen error [Errno 111] Connection refused>"


class ScriptedBox(FakeBox):
    """FakeBox whose jobs can report an agent-level error instead of ranks, plus a full /status.

    ``agent_errors`` maps job id -> the agent's error string. A job without one uploads and
    reports success like ``FakeBox``. ``full_status`` is what ``attn_full_status`` returns (or
    raises, when it is an exception); every call is recorded in ``full_status_calls``.
    """

    def __init__(self, s3: FakeS3, agent_errors: dict, full_status: Any = None) -> None:
        super().__init__(s3)
        self.agent_errors = agent_errors
        self.full_status = full_status if full_status is not None else {
            "healthy": False, "container": "exited", "log_tail": "EngineDeadError: step timed out"}
        self.full_status_calls = 0

    def attn_start(self, state: dict, payload: dict) -> dict:
        erroring = [line for line in payload["jobs"] if line["job_id"] in self.agent_errors]
        rest = dict(payload, jobs=[line for line in payload["jobs"] if line not in erroring])
        super().attn_start(state, rest)
        self.batches[-1] = payload  # record the batch as it was sent
        final = self._status[-1]
        # Rebuild results in SEND order, as the agent's dict insertion order is.
        merged = {}
        for line in payload["jobs"]:
            jid = line["job_id"]
            if jid in self.agent_errors:
                merged[jid] = {"error": self.agent_errors[jid]}
            elif jid in final["results"]:
                merged[jid] = final["results"][jid]
        final["results"] = merged
        return {"ok": True}

    def attn_full_status(self, state: dict) -> dict:
        self.full_status_calls += 1
        if isinstance(self.full_status, BaseException):
            raise self.full_status
        return self.full_status


def _sent_ids(box: FakeBox) -> list:
    return [line["job_id"] for b in box.batches for line in b["jobs"]]


def _death_run(box, s3, jobs, *, batch_size, hook=None):
    return attention.run_capture_batches(
        box, {"public_ip": "x"}, "served", jobs, 2, lambda: s3, "bucket",
        batch_size=batch_size, url_ttl_s=99, batch_timeout_s=10, poll_s=0,
        on_engine_death=hook)


def _five_jobs():
    # Longest first: j1 > j2 > ... > j5, so batches of 3 are [j1, j2, j3], [j4, j5].
    return [job(f"j{i}", 40 - 5 * i, 3) for i in range(1, 6)]


def test_engine_death_stops_further_batches_and_marks_the_rest_not_sent() -> None:
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j2": ENGINE_500, "j3": ENGINE_REFUSED})
    seen = []
    result = _death_run(box, s3, _five_jobs(), batch_size=3, hook=seen.append)
    # One batch only: nothing is sent once the engine is gone.
    assert len(box.batches) == 1 and _sent_ids(box) == ["j1", "j2", "j3"]
    assert result.verified == ["j1"]
    # The job in flight when the engine died, and the job the agent still attempted after it,
    # were sent: they are failures, each saying which.
    assert set(result.failed) == {"j2", "j3"}
    assert "engine died" in result.failed["j2"] and ENGINE_500 in result.failed["j2"]
    assert "engine" in result.failed["j3"] and ENGINE_REFUSED in result.failed["j3"]
    # The later batch was never handed to the agent: not sent, not failed, no URL minted.
    assert result.not_sent == ["j4", "j5"]
    assert not any(k.startswith("p/run/j4.") or k.startswith("p/run/j5.") for k in s3.presigned)
    assert result.engine_died is not None and "j2" in result.engine_died
    # The hook got the full /status reply once, log tail included.
    assert box.full_status_calls == 1
    assert seen == [box.full_status] and seen[0]["log_tail"].startswith("EngineDeadError")
    # Every job id lands in exactly one group.
    groups = [set(result.verified), set(result.failed), set(result.skipped_existing), set(result.not_sent)]
    assert sum(len(g) for g in groups) == 5 and set().union(*groups) == {f"j{i}" for i in range(1, 6)}


@pytest.mark.parametrize("error", [ENGINE_500, ENGINE_RESET, ENGINE_PIPE, ENGINE_REFUSED])
def test_each_engine_gone_wording_ending_a_batch_is_a_death(error) -> None:
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": error})
    result = _death_run(box, s3, _five_jobs(), batch_size=3)
    assert len(box.batches) == 1 and result.not_sent == ["j4", "j5"]
    assert result.engine_died is not None and set(result.failed) == {"j3"}


def test_one_engine_error_followed_by_a_healthy_job_is_not_a_death() -> None:
    """A 500 that a later job of the same batch survived cannot be read as a dead engine."""
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j1": ENGINE_500})
    result = _death_run(box, s3, _five_jobs(), batch_size=3)
    assert len(box.batches) == 2 and _sent_ids(box) == ["j1", "j2", "j3", "j4", "j5"]
    assert set(result.failed) == {"j1"} and "engine died" not in result.failed["j1"]
    assert sorted(result.verified) == ["j2", "j3", "j4", "j5"]
    assert result.not_sent == [] and result.engine_died is None
    assert box.full_status_calls == 0  # no trailing engine error: health is not even asked


def test_a_batch_ending_in_engine_errors_on_a_healthy_engine_is_not_a_death() -> None:
    """The pattern alone is not enough: /status must corroborate that vLLM is down."""
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": ENGINE_RESET},
                      full_status={"healthy": True, "container": "running", "log_tail": ""})
    seen = []
    result = _death_run(box, s3, _five_jobs(), batch_size=3, hook=seen.append)
    assert len(box.batches) == 2 and result.not_sent == [] and result.engine_died is None
    assert set(result.failed) == {"j3"} and sorted(result.verified) == ["j1", "j2", "j4", "j5"]
    assert box.full_status_calls == 1 and seen == []


@pytest.mark.parametrize("status", [
    {"healthy": False, "container": "running", "log_tail": "x"},
    {"healthy": True, "container": "exited", "log_tail": "x"},
])
def test_either_unhealthy_signal_corroborates_a_death(status) -> None:
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": ENGINE_REFUSED}, full_status=status)
    result = _death_run(box, s3, _five_jobs(), batch_size=3)
    assert len(box.batches) == 1 and result.not_sent == ["j4", "j5"]


def test_an_unreadable_status_after_engine_errors_counts_as_a_death() -> None:
    """Stopping is the cheap mistake (the unsent jobs are recorded and re-runnable)."""
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": ENGINE_REFUSED}, full_status=RuntimeError("agent unreachable"))
    seen = []
    result = _death_run(box, s3, _five_jobs(), batch_size=3, hook=seen.append)
    assert len(box.batches) == 1 and result.not_sent == ["j4", "j5"] and result.engine_died
    assert len(seen) == 1  # the hook still hears about it


def test_a_rank_collection_timeout_is_not_an_engine_death() -> None:
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": "j3: 7/8 ranks done"})
    result = _death_run(box, s3, _five_jobs(), batch_size=3)
    assert len(box.batches) == 2 and result.not_sent == [] and result.engine_died is None
    assert box.full_status_calls == 0


def test_a_hook_that_raises_does_not_lose_the_result() -> None:
    s3 = FakeS3()
    box = ScriptedBox(s3, {"j3": ENGINE_REFUSED})

    def hook(status):
        raise OSError("disk full")

    result = _death_run(box, s3, _five_jobs(), batch_size=3, hook=hook)
    assert result.not_sent == ["j4", "j5"] and result.verified == ["j1", "j2"]


def test_without_engine_errors_the_full_status_is_never_asked() -> None:
    """Fakes without attn_full_status keep working: it is called on the death path only."""
    s3 = FakeS3()
    box = FakeBox(s3)
    box.gate_failures = {"j3"}
    result = _death_run(box, s3, _five_jobs(), batch_size=3)
    assert len(box.batches) == 2 and result.not_sent == [] and result.engine_died is None


# ------------------------------------------------------------------ fill mode

class FillBox(FakeBox):
    """Fake box honouring the plugin's fill contract: a key that exists is answered 412 ("exists")
    and left untouched; a rank whose npz existed uploads its meta with ``npz_put: "existing"``."""

    def attn_start(self, state: dict, payload: dict) -> dict:
        self.batches.append(payload)
        results: dict[str, dict] = {}
        for line in payload["jobs"]:
            n = len(line["prompt_token_ids"]) + len(line["completion_token_ids"])
            ranks = {}
            for rank in range(payload["tp"]):
                blob = mass_npz(n, line["query_start"], line["classes"])
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                npz_existed = key in self.s3.objects
                if not npz_existed:
                    self.s3.objects[key] = blob
                if meta_key not in self.s3.objects:
                    meta = {"n_tokens": n, "bytes": len(blob), "mode": "mass", "capture_version": 2,
                            "tp": payload["tp"], "rank": rank}
                    if npz_existed:
                        meta["npz_put"] = "existing"
                    self.s3.objects[meta_key] = json.dumps(meta).encode()
                ranks[str(rank)] = {"ok": True, "error": None, "gate_max_rel": 0.001}
            results[line["job_id"]] = ranks
        self._status = [{"running": False, "results": results, "error": None}]
        return {"ok": True}


def _store_rank(s3: FakeS3, j: attention.Job, rank: int, *, meta: dict | None = None,
                npz: bool = True, meta_obj: bool = True, tp: int = 2, **kw: Any) -> None:
    """Store one rank's objects as an earlier run would have (meta bytes match its npz)."""
    npz_key, meta_key = attention.rank_keys(j.key, rank)
    blob = mass_npz(j.n_tokens, j.query_start, list(j.classes), **kw)
    if npz:
        s3.objects[npz_key] = blob
    if meta_obj:
        body = {"n_tokens": j.n_tokens, "bytes": len(blob), "mode": "mass", "capture_version": 2,
                "tp": tp, "rank": rank}
        body.update(meta or {})
        s3.objects[meta_key] = json.dumps(body).encode()


def _fill_run(box, s3, jobs, *, fill=True, mode="mass", tp=2):
    return attention.run_capture_batches(
        box, {"public_ip": "x"}, "served", jobs, tp, lambda: s3, "bucket", mode=mode,
        url_ttl_s=99, batch_timeout_s=10, poll_s=0, fill=fill)


def test_fill_mode_sends_a_partial_stem_and_skips_a_complete_one() -> None:
    s3 = FakeS3()
    part, done, fresh = job("part", 6, 3), job("done", 5, 3), job("fresh", 4, 2)
    _store_rank(s3, part, 0)                    # rank 0 stored by an earlier run, rank 1 lost
    for rank in range(2):
        _store_rank(s3, done, rank)
    before = dict(s3.objects)
    box = FillBox(s3)
    result = _fill_run(box, s3, [part, done, fresh])
    assert sorted(_sent_ids(box)) == ["fresh", "part"]
    assert set(result.skipped_existing) == {"done"}
    sent = {line["job_id"]: line for b in box.batches for line in b["jobs"]}
    # URLs for EVERY rank, existing ones included: the box answers those with "exists".
    assert len(sent["part"]["put_urls"]) == len(sent["part"]["meta_put_urls"]) == 2
    assert sorted(result.verified) == ["fresh", "part"] and result.failed == {}
    # Nothing that existed was replaced.
    assert {k: s3.objects[k] for k in before} == before
    assert attention.rank_keys(part.key, 1)[0] in s3.objects


def test_without_fill_a_partial_stem_is_still_never_sent() -> None:
    s3 = FakeS3()
    part = job("part", 6, 3)
    _store_rank(s3, part, 0)
    box = FillBox(s3)
    result = _fill_run(box, s3, [part], fill=False)
    assert box.batches == [] and set(result.skipped_existing) == {"part"}


def test_fill_completes_a_rank_whose_npz_exists_and_meta_is_missing() -> None:
    """The npz of rank 1 landed earlier, its meta did not: the new meta says npz_put existing."""
    s3 = FakeS3()
    part = job("part", 6, 3)
    _store_rank(s3, part, 0)
    _store_rank(s3, part, 1, meta_obj=False)
    box = FillBox(s3)
    result = _fill_run(box, s3, [part])
    assert result.verified == ["part"]
    meta = json.loads(s3.objects[attention.rank_keys(part.key, 1)[1]])
    assert meta["npz_put"] == "existing"


@pytest.mark.parametrize("setup, needle", [
    # Existing meta in the other mode: a mass job must not be completed with summary objects.
    (lambda s3, j: _store_rank(s3, j, 0, meta={"mode": "summary", "capture_version": 3}), "mode"),
    # Same mode, but an older capture format.
    (lambda s3, j: _store_rank(s3, j, 0, meta={"capture_version": 1}), "capture_version"),
    # A meta without a version is version 1.
    (lambda s3, j: s3.objects.__setitem__(attention.rank_keys(j.key, 0)[1], b"{}"), "capture_version"),
    # Captured with another tensor-parallel degree.
    (lambda s3, j: _store_rank(s3, j, 0, meta={"tp": 4}), "tp"),
    # Only an npz: there is no meta to read the mode from.
    (lambda s3, j: _store_rank(s3, j, 0, meta_obj=False), "meta"),
    # A key outside ranks 0..tp-1.
    (lambda s3, j: (_store_rank(s3, j, 0), _store_rank(s3, j, 2)), "unexpected"),
])
def test_fill_refuses_a_stem_it_cannot_safely_complete(setup, needle) -> None:
    s3 = FakeS3()
    part, fresh = job("part", 6, 3), job("fresh", 4, 2)
    setup(s3, part)
    box = FillBox(s3)
    result = _fill_run(box, s3, [part, fresh])
    assert _sent_ids(box) == ["fresh"]
    assert "part" in result.failed and needle in result.failed["part"]
    assert "fill" in result.failed["part"]
    assert not any(k.startswith("p/run/part.") for k in s3.presigned)


def test_fill_accepts_a_meta_without_mode_as_a_mass_capture() -> None:
    s3 = FakeS3()
    part = job("part", 6, 3)
    npz_key, meta_key = attention.rank_keys(part.key, 0)
    _store_rank(s3, part, 0)
    meta = json.loads(s3.objects[meta_key])
    del meta["mode"]
    s3.objects[meta_key] = json.dumps(meta).encode()
    result = _fill_run(FillBox(s3), s3, [part])
    assert result.verified == ["part"]


def test_capture_versions_match_the_plugin() -> None:
    from smolbench.evals import payloads

    source = payloads.attention_capture_plugin_py()
    assert "\nCAPTURE_VERSION = 2\n" in source and "\nSUMMARY_CAPTURE_VERSION = 4\n" in source
    assert "\nANSWER_CLASS = 4\n" in source and attention.ANSWER_CLASS == 4
    assert attention.CAPTURE_VERSIONS == {"rows": 2, "mass": 2, "summary": 4}
    # Every array the client requires of a version-4 summary is one the plugin stacks.
    for name in attention.SUMMARY_V4_ARRAYS:
        assert f'"{name}"' in source, name


# ------------------------------------------------------------------ version 4 (class split, answer rows)
def _summary_v4_npz(j: attention.Job, *, drop: tuple = (), by_class_heads: int | None = None,
                    rows_answer: int | None = None) -> bytes:
    """A version-4 summary upload of `j`: the version-3 arrays plus the class split and answer sums."""
    arrays = dict(np.load(io.BytesIO(summary_npz(j.n_tokens, j.query_start, list(j.classes)))))
    arrays["capture_version"] = np.asarray(4, np.int32)
    layers, heads = arrays["sum_entropy"].shape
    for name, tail in attention.SUMMARY_V4_ARRAYS.items():
        h = by_class_heads if (by_class_heads and name == attention.SUMMARY_BY_CLASS_ARRAY) else heads
        dtype = np.int64 if name.startswith("n_") else np.float64
        arrays[name] = np.zeros((layers, h) + tail, dtype)
    arrays["rows_answer"] = np.asarray(0 if rows_answer is None else rows_answer, np.int64)
    for name in drop:
        arrays.pop(name)
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


def _put_v4(s3: FakeS3, j: attention.Job, tp: int = 2, **kw: Any) -> None:
    for rank in range(tp):
        npz, meta = attention.rank_keys(j.key, rank)
        blob = _summary_v4_npz(j, **kw)
        s3.objects[npz] = blob
        s3.objects[meta] = json.dumps({"n_tokens": j.n_tokens, "bytes": len(blob)}).encode()


def test_verify_requires_the_version_4_arrays_of_a_version_4_summary() -> None:
    s3 = FakeS3()
    j = summary_job("v4", 5, 3)
    _put_v4(s3, j)
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="summary") == (["v4"], [])
    for kw in ({"drop": (attention.SUMMARY_BY_CLASS_ARRAY,)}, {"drop": ("sum_mass_answer",)},
               {"drop": ("rows_answer",)}, {"by_class_heads": 3}, {"rows_answer": 4}):
        _put_v4(s3, j, **kw)
        assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="summary") == ([], ["v4"]), kw
    # A version-3 upload (no class split) still verifies: the stored captures are of that kind.
    _upload_summary(s3, j)
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="summary") == (["v4"], [])


@pytest.mark.parametrize("stored_version, refused", [(3, True), (4, False)])
def test_fill_never_completes_a_version_3_summary_stem_with_version_4_objects(stored_version, refused) -> None:
    s3 = FakeS3()
    j = summary_job("s7", 6, 3)
    npz_key, meta_key = attention.rank_keys(j.key, 0)
    s3.objects[npz_key] = b"npz"
    s3.objects[meta_key] = json.dumps({"mode": "summary", "capture_version": stored_version, "tp": 2}).encode()
    reason = attention.fill_refusal(s3, "b", j, 2, "summary", [npz_key, meta_key])
    if refused:
        assert reason is not None and "capture_version" in reason and "this run writes 4" in reason, reason
    else:
        assert reason is None


def test_token_classes_marks_the_answer_tokens_class_4_only_when_asked() -> None:
    table = {0: "", 1: "Hi", 2: " " * 40}
    decode = lambda ids: [table[i] for i in ids]  # noqa: E731
    plain = attention.token_classes([0, 1, 2], [7, 8, 9], decode)
    assert plain == [2, 0, 1, 3, 3, 3]
    assert attention.token_classes([0, 1, 2], [7, 8, 9], decode, answer_start=None) == plain
    assert attention.token_classes([0, 1, 2], [7, 8, 9], decode, answer_start=1) == [2, 0, 1, 3, 4, 4]
    assert attention.token_classes([0, 1, 2], [7, 8, 9], decode, answer_start=0)[3:] == [4, 4, 4]
    assert attention.token_classes([0, 1, 2], [7, 8, 9], decode, answer_start=3) == plain
    for bad in (-1, 4):
        with pytest.raises(ValueError, match="answer_start"):
            attention.token_classes([0, 1, 2], [7, 8, 9], decode, answer_start=bad)


def test_mass_job_accepts_an_answer_suffix_and_refuses_misplaced_class_4() -> None:
    ok = attention.mass_job("q0", (1, 2), (3, 4, 5), [0, 2, 3, 4, 4], "p/q0.npz", mode="summary")
    assert ok.classes == (0, 2, 3, 4, 4)
    assert attention.mass_job("q0", (1,), (3, 4), [0, 4, 4], "p/q0.npz").classes == (0, 4, 4)
    for classes, needle in (([4, 3, 3], "prompt token"), ([0, 4, 3], "follows"),
                            ([0, 3, 5], "outside"), ([0, 3, 2], "other than 3 or 4")):
        with pytest.raises(ValueError, match=needle):
            attention.mass_job("q0", (1,), (3, 4), classes, "p/q0.npz")


# ------------------------------------------------------------------ npz_put: existing

def test_verification_skips_only_the_size_check_for_an_existing_npz() -> None:
    s3 = FakeS3()
    j = job("q0", 5, 3)
    _store_rank(s3, j, 0)
    _store_rank(s3, j, 1)
    npz0, meta0 = attention.rank_keys(j.key, 0)
    meta = json.loads(s3.objects[meta0])
    meta["bytes"] += 17                              # the new run's npz would have been larger
    s3.objects[meta0] = json.dumps(meta).encode()
    # Without the marker the size mismatch fails the job ...
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == ([], ["q0"])
    # ... with it, the stored npz is an earlier run's and only its size is not compared.
    meta["npz_put"] = "existing"
    s3.objects[meta0] = json.dumps(meta).encode()
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == (["q0"], [])
    # Every other check still applies to that rank: n_tokens ...
    bad = dict(meta, n_tokens=j.n_tokens + 1)
    s3.objects[meta0] = json.dumps(bad).encode()
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == ([], ["q0"])
    # ... the array content of the sampled rank ...
    s3.objects[meta0] = json.dumps(meta).encode()
    s3.objects[npz0] = mass_npz(j.n_tokens, j.query_start, list(j.classes), broken=True)
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == ([], ["q0"])
    # ... and the npz must still exist.
    del s3.objects[npz0]
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == ([], ["q0"])
    # A different marker value is not the exemption.
    _store_rank(s3, j, 0, meta={"npz_put": "new"})
    meta = json.loads(s3.objects[meta0])
    meta["bytes"] += 1
    s3.objects[meta0] = json.dumps(meta).encode()
    assert attention.verify_capture_uploads(s3, "b", [j], 2, mode="mass") == ([], ["q0"])
