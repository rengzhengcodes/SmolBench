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
