"""Summary-mode captures in the rebuttal replay: audit, storage estimate, replay, post-hoc audit, reader.

Offline: S3 is the dict fake of ``tests/evals/test_attention.py``; captures are built from real
softmax rows by ``tests/evals/test_attention_analysis.synthetic_capture`` (the summary of the
unrounded rows, as the plugin stores it, and the float16 mass-mode rows of the same sequence).
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

import numpy as np
import pytest

from smolbench.evals import attention
from smolbench.evals.quiz import COMPLIANT, Mark, Marks
from tests._paths import REPO_ROOT, load_by_path
from tests.evals.test_attention import FakeS3
from tests.evals.test_attention_analysis import capture_npz, synthetic_capture

ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_summary_under_test")

GEMMA = "gemma-4-31b"
LAYERS = ((0, False), (5, False), (0, True), (9, True))
CONFIG = {"num_hidden_layers": 4, "num_attention_heads": 4}


def _job_for(cap: dict, job_id: str = "q0", prefix: str = "p/run/", mode: str = "summary") -> attention.Job:
    qs, t = cap["query_start"], cap["n_tokens"]
    return attention.mass_job(job_id, tuple(range(qs)), tuple(range(t - qs)), cap["classes"].tolist(),
                              f"{prefix}{job_id}.npz", mode=mode)


def _meta(job: attention.Job, rank: int, tp: int, blob: bytes, *, mode: str, version: int,
          layers: int, heads_local: int, model: str = GEMMA) -> dict:
    p = job.n_tokens - job.query_start
    return {"job_id": job.job_id, "rank": rank, "tp": tp, "model": model, "n_tokens": job.n_tokens,
            "bytes": len(blob), "mode": mode, "capture_version": version, "query_start": job.query_start,
            "layers": list(range(layers)), "num_heads_local": heads_local,
            "rows_shape": [layers, p, heads_local, 4], "gate_max_rel": 0.001, "gate_tol": 0.03}


def _edit(blob: bytes, **changes) -> bytes:
    """Rewrite one npz: each change is a new array, a callable of the old one, or None (drop)."""
    arrays = dict(np.load(io.BytesIO(blob)))
    for name, change in changes.items():
        if change is None:
            arrays.pop(name)
        elif callable(change):
            arrays[name] = change(arrays[name].copy())
        else:
            arrays[name] = change
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


def _store(s3: FakeS3, job: attention.Job, cap: dict, *, tp: int = 2, kind: str = "summary",
           version: int | None = None, meta_mode: str | None = None, corrupt=None) -> None:
    layers, heads = cap["entropy"].shape[0], cap["entropy"].shape[2]
    for rank in range(tp):
        npz_key, meta_key = attention.rank_keys(job.key, rank)
        blob = capture_npz(cap, rank, tp, kind)
        if corrupt is not None:
            blob = corrupt(rank, blob)
        s3.objects[npz_key] = blob
        s3.objects[meta_key] = json.dumps(_meta(
            job, rank, tp, blob, mode=meta_mode or kind,
            version=version if version is not None else (3 if kind == "summary" else 2),
            layers=layers, heads_local=heads // tp)).encode()


def _audit(s3: FakeS3, jobs, config=CONFIG, **kw):
    return ar.audit_captures(s3, "b", jobs, 2, model=GEMMA, config=config, arrays="all", **kw)


# ------------------------------------------------------------------ the summary audit

@pytest.mark.parametrize("seed, boost", [(11, 0.0), (12, 2.0), (13, -1.0)])
def test_the_audit_passes_a_consistent_summary_capture(seed, boost) -> None:
    cap = synthetic_capture(seed, layers=LAYERS, boost=boost)
    job = _job_for(cap)
    s3 = FakeS3()
    _store(s3, job, cap)
    assert _audit(s3, [job]) == {"q0": None}
    assert _audit(s3, [job], mode="summary", capture_version=ar.SUMMARY_CAPTURE_VERSION) == {"q0": None}


def test_the_versions_tell_the_three_kinds_apart() -> None:
    assert ar.CAPTURE_VERSION == 2 and ar.SUMMARY_CAPTURE_VERSION == 3


def test_summary_and_mass_captures_never_certify_each_other() -> None:
    cap = synthetic_capture(14, layers=LAYERS)
    s3 = FakeS3()
    summary_job, mass_job = _job_for(cap, "s"), _job_for(cap, "m", mode="mass")
    _store(s3, summary_job, cap, kind="summary")
    _store(s3, mass_job, cap, kind="mass")
    assert _audit(s3, [summary_job, mass_job]) == {"s": None, "m": None}   # each by its own meta
    assert "mode" in _audit(s3, [summary_job], mode="mass")["s"]
    assert "mode" in _audit(s3, [mass_job], mode="summary")["m"]


@pytest.mark.parametrize("kind, version", [("summary", 2), ("summary", 1), ("mass", 3)])
def test_the_mode_and_the_capture_version_must_agree(kind, version) -> None:
    cap = synthetic_capture(15, layers=LAYERS)
    job = _job_for(cap, mode=kind)
    s3 = FakeS3()
    _store(s3, job, cap, kind=kind, version=version)
    reason = _audit(s3, [job])["q0"]
    assert reason is not None and "capture_version" in reason, reason


#: Selects cell (layer 0, head 0) of a rank's [L=4, H_local=2] array, and nothing else: a bound
#: derived for one cell must not be written into a cell of another layer.
_CELL_00 = np.zeros((4, 2), bool)
_CELL_00[0, 0] = True


def _p(cap):
    return cap["n_tokens"] - cap["query_start"]


def _negative_class_0(a):
    """Class-0 sums of -0.5 with the difference moved to class 3: totals still P, a sum negative."""
    a[..., 3] += a[..., 0] + 0.5
    a[..., 0] = -0.5
    return a


#: name -> (corruption of rank 0's npz given the capture, word the failure must contain).
_CORRUPTIONS = {
    "rows": (lambda cap: dict(rows=lambda a: a + 1), "rows"),
    "missing-array": (lambda cap: dict(sum_chain_lo=None), "sum_chain_lo"),
    "shape": (lambda cap: dict(sum_entropy=lambda a: np.concatenate([a, a[:, :1]], axis=1)), "sum_entropy"),
    "non-finite": (lambda cap: dict(sum_sink=lambda a: np.where(np.arange(a.size).reshape(a.shape) == 0,
                                                                  np.nan, a)), "finite"),
    "window-count": (lambda cap: dict(n_prompt_entropy=lambda a: a + np.eye(4, 2, k=-1, dtype=np.int64)),
                     "n_prompt_entropy"),
    "global-count": (lambda cap: dict(n_prompt_entropy=lambda a: a - np.eye(4, 2, dtype=np.int64)),
                     "n_prompt_entropy"),
    "pad-count": (lambda cap: dict(n_pad_ratio=lambda a: a - np.eye(4, 2, dtype=np.int64)), "n_pad_ratio"),
    "mass-halved": (lambda cap: dict(sum_mass=lambda a: a * 0.5), "sum_mass"),
    "negative-mass": (lambda cap: dict(sum_mass=_negative_class_0), "sum_mass"),
    "entropy-above-ceiling": (
        lambda cap: dict(sum_entropy=lambda a: a + _p(cap) * (math.log(cap["n_tokens"] + 2) + 1.0)), "entropy"),
    "prompt-entropy-above-ceiling": (
        lambda cap: dict(sum_prompt_entropy=lambda a: a * 0 + (math.log(cap["query_start"]) + 1.0) * 11),
        "prompt_entropy"),
    "chain-above": (lambda cap: dict(sum_m_hp=lambda a: a + 50.0), "sum_m_hp"),
    "chain-below": (lambda cap: dict(sum_m_hp=lambda a: a - 50.0), "sum_m_hp"),
}


@pytest.mark.parametrize("name", sorted(_CORRUPTIONS))
def test_the_summary_audit_rejects_a_corrupt_capture(name) -> None:
    """Each failure names the array it found wrong (and the job fails, it does not crash)."""
    make, word = _CORRUPTIONS[name]
    cap = synthetic_capture(16, layers=LAYERS, boost=1.0)
    job = _job_for(cap)
    s3 = FakeS3()
    _store(s3, job, cap, corrupt=lambda rank, blob: _edit(blob, **make(cap)) if rank == 0 else blob)
    reason = _audit(s3, [job])["q0"]
    assert reason is not None and reason.startswith("rank 0: "), reason
    assert word in reason, reason


def test_the_summary_audit_rejects_a_prompt_entropy_sum_where_none_is_defined() -> None:
    """Window 1: no row ever sees a prompt key, so the count is 0 and every prompt sum must be 0."""
    cap = synthetic_capture(17, layers=((0, False), (1, False)))
    assert (cap["summary"]["n_prompt_entropy"][1] == 0).all()
    job = _job_for(cap)
    s3 = FakeS3()
    _store(s3, job, cap)
    config = {"num_hidden_layers": 2, "num_attention_heads": 4}
    assert _audit(s3, [job], config=config) == {"q0": None}
    _store(s3, job, cap, corrupt=lambda rank, blob: _edit(
        blob, sum_prompt_entropy=lambda a: a + np.array([[0.0, 0.0], [0.5, 0.0]])) if rank == 0 else blob)
    reason = _audit(s3, [job], config=config)["q0"]
    assert reason is not None and "prompt_entropy" in reason, reason


def test_the_summary_audit_rejects_identical_ranks() -> None:
    cap = synthetic_capture(18, layers=LAYERS)
    job = _job_for(cap)
    s3 = FakeS3()
    _store(s3, job, cap)
    rank0 = s3.objects[attention.rank_keys(job.key, 0)[0]]
    _store(s3, job, cap, corrupt=lambda rank, blob: rank0)
    reason = _audit(s3, [job])["q0"]
    assert reason is not None and "duplicates" in reason, reason


def test_the_mass_sum_tolerance_is_the_mass_audits_per_row_allowance_times_p() -> None:
    """sum_mass + sum_sink may deviate from P by _ROW_SUM_TOL per row, as the mass audit allows."""
    cap = synthetic_capture(19, layers=LAYERS)
    job = _job_for(cap)
    p = _p(cap)
    s3 = FakeS3()
    for per_row, ok in ((0.5 * ar._ROW_SUM_TOL, True), (1.5 * ar._ROW_SUM_TOL, False)):
        _store(s3, job, cap, corrupt=lambda rank, blob: _edit(
            blob, sum_mass=lambda a: a + np.array([0.0, 0.0, 0.0, per_row * p])))
        reason = _audit(s3, [job])["q0"]
        assert (reason is None) == ok, (per_row, reason)


def _chain_tol(cap, layer, head):
    s = cap["summary"]
    n = int(s["n_prompt_entropy"][layer, head])
    return n * (ar._PE_CHAIN_ABS_TOL + ar._PE_CHAIN_REL_TOL) + ar._PE_CHAIN_REL_TOL * float(s["sum_entropy"][layer, head])


@pytest.mark.parametrize("side", ["above", "below"])
def test_the_chain_tolerance_is_the_per_row_tolerance_summed_over_the_defined_rows(side) -> None:
    """tol = n * (abs + rel) + rel * sum_entropy, the mass audit's per-row tolerance summed."""
    cap = synthetic_capture(20, layers=LAYERS)
    job = _job_for(cap)
    s = cap["summary"]
    tol = _chain_tol(cap, 0, 0)
    s3 = FakeS3()
    for factor, ok in ((0.5, True), (1.5, False)):
        bound = s["sum_chain_hi"][0, 0] + factor * tol if side == "above" else s["sum_chain_lo"][0, 0] - factor * tol

        def corrupt(rank, blob, bound=bound):
            if rank:
                return blob
            return _edit(blob, sum_m_hp=lambda a: np.where(_CELL_00, bound, a))

        _store(s3, job, cap, corrupt=corrupt)
        reason = _audit(s3, [job])["q0"]
        assert (reason is None) == ok, (factor, reason)


def test_the_mean_entropy_ceiling_is_the_mean_of_the_row_ceilings() -> None:
    """sum_entropy / P <= mean_i ln(query_start + i + 1 + s_l) + _ENTROPY_CEIL_TOL."""
    cap = synthetic_capture(21, layers=LAYERS)
    job = _job_for(cap)
    qs, p = cap["query_start"], _p(cap)
    ceiling = np.mean(np.log(qs + np.arange(p) + 1 + 0.0)) + ar._ENTROPY_CEIL_TOL   # layer 0: no sink
    s3 = FakeS3()
    for excess, ok in ((-1e-3, True), (5e-3, False)):
        value = (ceiling + excess) * p
        _store(s3, job, cap, corrupt=lambda rank, blob, value=value: _edit(
            blob, sum_entropy=lambda a: np.where(_CELL_00, value, a)) if rank == 0 else blob)
        reason = _audit(s3, [job])["q0"]
        assert (reason is None) == ok, (excess, reason)


# ------------------------------------------------------------------ replay in summary mode

GEMMA_TEMPLATE = ("{{ bos_token }}{% if enable_thinking %}<|turn>system\n<|think|><turn|>\n{% endif %}"
                  "{% for m in messages %}<|turn>user\n{{ m['content'] | trim }}<turn|>\n{% endfor %}"
                  "{% if add_generation_prompt %}<|turn>model\n{% endif %}")
GEMMA_SPECIALS = ("<bos>", "<|turn>", "<turn|>", "<|think|>", "<|channel>", "<channel|>")
STAMP = "2026-11-13T01:00:00.000001Z"
REPLAY_CONFIG = {"num_hidden_layers": 2, "num_attention_heads": 4}


class CharTokenizer:
    """Each listed special string is one token, every other character one token."""

    def __init__(self, specials):
        self.specials = tuple(sorted(specials, key=len, reverse=True))
        self.vocab: dict = {}
        self._re = re.compile("|".join(re.escape(s) for s in self.specials) + "|.", re.S)

    def encode_offsets(self, text):
        return [(m.start(), m.end()) for m in self._re.finditer(text)]

    def encode_ids(self, text):
        return [self.vocab.setdefault(text[s:e], len(self.vocab)) for s, e in self.encode_offsets(text)]

    def token_to_id(self, token):
        return self.vocab.setdefault(token, len(self.vocab)) if token in self.specials else None


def _write_results(root: Path, model: str = GEMMA) -> None:
    seed_dir = root / "induction" / model / "seed=0"
    seed_dir.mkdir(parents=True)
    marks = Marks(model=model, marks=tuple(
        Mark(query=q, answer=1, response="1", score=1, compliance=COMPLIANT, reasoning="r")
        for q in ("ab", "abcd ef")))
    (seed_dir / f"intens--{STAMP}.yaml").write_text(marks.dumps())


class SummaryBox:
    """Fake ec2 module whose /attn uploads consistent summary captures (or mass, by the job's mode)."""

    EC2_REGIONS = ("us-east-1",)

    def __init__(self, s3: FakeS3, tp: int = 2, meta_version: int | None = None) -> None:
        self.s3, self.tp, self.meta_version = s3, tp, meta_version
        self.calls: list = []
        self.batches: list = []
        self._status: dict = {}

    def provision_spot_instance(self, instance_types=None, **kw):
        self.calls.append("provision")
        return {"instance_type": "p5.48xlarge", "public_ip": "x"}

    def derive_tp(self, model, instance_type, spec):
        return self.tp

    def serve_model(self, model, capture=False, **kw):
        box = self

        class Ctx:
            def __enter__(self):
                box.calls.append(("serve", kw.get("max_model_len")))
                return model

            def __exit__(self, *exc):
                return False

        return Ctx()

    def attn_start(self, state, payload):
        self.batches.append(payload)
        results = {}
        for n_line, line in enumerate(payload["jobs"]):
            kind = line["mode"]
            cap = synthetic_capture(100 + n_line, n_prompt=line["query_start"], classes=line["classes"],
                                    layers=((0, False), (0, True)), heads=4)
            job = attention.mass_job(line["job_id"], line["prompt_token_ids"], line["completion_token_ids"],
                                     line["classes"], "x/q.npz", mode=kind)
            ranks = {}
            for rank in range(payload["tp"]):
                blob = capture_npz(cap, rank, payload["tp"], kind)
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.put_object(Bucket="b", Key=key, Body=blob)
                version = self.meta_version or (3 if kind == "summary" else 2)
                meta = _meta(job, rank, payload["tp"], blob, mode=kind, version=version, layers=2,
                             heads_local=4 // payload["tp"], model=payload["served_model_name"])
                self.s3.put_object(Bucket="b", Key=meta_key, Body=json.dumps(meta).encode())
                ranks[str(rank)] = {"ok": True, "gate_max_rel": 0.001}
            results[line["job_id"]] = ranks
        self._status = {"running": False, "results": results, "error": None}
        return {"ok": True}

    def attn_status(self, state):
        return self._status

    def shutdown_instance(self, wait=True):
        self.calls.append("shutdown")


def _replay(tmp_path: Path, box, s3, **kw):
    tok = CharTokenizer(GEMMA_SPECIALS)
    return ar.replay_model(
        GEMMA, tmp_path, "s3://bucket/bedrock-trio/attention", approved=True,
        tokenizer_for=lambda m: tok, template_for=lambda m: ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>"),
        config_for=lambda m: REPLAY_CONFIG, ec2=box, s3_client_factory=lambda: s3, poll_s=0,
        batch_timeout_s=10, url_ttl_s=99, **kw)


def test_replay_in_summary_mode_sends_summary_jobs_audits_them_and_records_the_mode(tmp_path: Path) -> None:
    _write_results(tmp_path)
    s3 = FakeS3()
    box = SummaryBox(s3)
    report = _replay(tmp_path, box, s3, mode="summary")
    assert sorted(report.verified) == sorted(report.plan and [
        f"s0.intens.{STAMP.replace(':', '-')}.q0", f"s0.intens.{STAMP.replace(':', '-')}.q1"])
    assert report.audit_failures == {} and report.failed == {}
    assert {line["mode"] for batch in box.batches for line in batch["jobs"]} == {"summary"}
    assert report.plan.mode == "summary"
    manifests = [json.loads(s3.objects[k]) for k in report.manifests]
    assert manifests and all(m["mode"] == "summary" for m in manifests)
    assert box.calls[0] == "provision" and box.calls[-1] == "shutdown"


def test_a_summary_run_requires_version_3_metas(tmp_path: Path) -> None:
    _write_results(tmp_path)
    s3 = FakeS3()
    report = _replay(tmp_path, SummaryBox(s3, meta_version=2), s3, mode="summary")
    assert report.verified == [] and len(report.audit_failures) == 2
    assert all("capture_version" in why for why in report.audit_failures.values())


def test_the_default_induction_mode_is_still_mass(tmp_path: Path) -> None:
    _write_results(tmp_path)
    s3 = FakeS3()
    box = SummaryBox(s3)
    report = _replay(tmp_path, box, s3)
    assert {line["mode"] for batch in box.batches for line in batch["jobs"]} == {"mass"}
    assert report.plan.mode == "mass" and len(report.verified) == 2


def test_replay_refuses_an_unknown_mode_before_any_aws_call(tmp_path: Path) -> None:
    _write_results(tmp_path)

    def never():
        raise AssertionError("S3 client built")

    with pytest.raises(ValueError, match="mode"):
        ar.replay_model(GEMMA, tmp_path, "s3://bucket/x", approved=True, mode="rows",
                        tokenizer_for=lambda m: CharTokenizer(GEMMA_SPECIALS),
                        template_for=lambda m: ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>"),
                        config_for=lambda m: REPLAY_CONFIG, ec2=SummaryBox(FakeS3()), s3_client_factory=never)


def test_the_plan_estimates_summary_storage_from_the_summed_arrays(tmp_path: Path) -> None:
    """Per job and over ranks: L x H x 13 eight-byte values (float64 sums, int64 counts) + tp x T."""
    _write_results(tmp_path)
    tok = CharTokenizer(GEMMA_SPECIALS)
    kw = dict(tokenizer_for=lambda m: tok,
              template_for=lambda m: ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>"),
              config_for=lambda m: {"num_hidden_layers": 60, "num_attention_heads": 32})
    summary = ar.plan_replay(tmp_path, [GEMMA], mode="summary", **kw)[GEMMA]
    mass = ar.plan_replay(tmp_path, [GEMMA], **kw)[GEMMA]
    tp = summary.tp_estimate
    assert summary.mode == "summary" and mass.mode == "mass" and summary.jobs == mass.jobs == 2
    sizes = [stats for stats in [summary.per_arm["intens"]]][0]
    assert sizes["marks"] == 2
    lengths = [summary.max_tokens, summary.total_tokens - summary.max_tokens]
    assert summary.est_capture_bytes == sum(60 * 32 * 13 * 8 + tp * n for n in lengths)
    assert summary.est_basis.startswith("ESTIMATE:") and "summary" in summary.est_basis
    assert mass.est_capture_bytes == sum(60 * (n - q) * 32 * 7 * 2 + tp * n
                                         for n, q in zip(lengths, _prompt_lengths(tmp_path, tok)))


def _prompt_lengths(root: Path, tok) -> list:
    """query_start of the two planned jobs, longest sequence first (as ``lengths`` above)."""
    planned, _errors = ar.build_jobs(GEMMA, root, "x", tokenizer=tok,
                                     template=ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>"))
    return [p.job.query_start for p in sorted(planned, key=lambda p: -p.job.n_tokens)]


def test_audit_existing_audits_summary_captures_by_their_meta(tmp_path: Path) -> None:
    _write_results(tmp_path)
    tok = CharTokenizer(GEMMA_SPECIALS)
    template = ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>")
    planned, errors = ar.build_jobs(GEMMA, tmp_path, "bedrock-trio/attention", tokenizer=tok, template=template)
    assert not errors and len(planned) == 2
    s3 = FakeS3()
    for i, item in enumerate(planned):
        job = item.job
        cap = synthetic_capture(200 + i, n_prompt=job.query_start, classes=list(job.classes),
                                layers=((0, False), (0, True)), heads=4)
        _store(s3, job, cap)
    report = ar.audit_existing(GEMMA, tmp_path, "s3://bucket/bedrock-trio/attention",
                               tokenizer_for=lambda m: tok, template_for=lambda m: template,
                               config_for=lambda m: REPLAY_CONFIG, s3_client_factory=lambda: s3)
    assert sorted(report.verified) == sorted(p.job.job_id for p in planned) and not report.audit_failures
    manifest = json.loads(s3.objects[report.manifests[0]])
    assert manifest["mode"] == "summary" and manifest["post_hoc_audit"] is True


# ------------------------------------------------------------------ the reader

def _mirror(root: Path, jobs: dict, *, model: str = GEMMA, arm: str = "intens") -> None:
    """Write ``{idx: (capture, kind, summary source)}`` as one verified run directory."""
    run_dir = root / "induction" / model / "seed=0" / f"{arm}--{STAMP}"
    run_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for idx, (cap, kind, source) in jobs.items():
        for rank in range(2):
            (run_dir / f"q{idx}.r{rank}.npz").write_bytes(capture_npz(cap, rank, 2, kind, summary=source))
        entries.append({"job_id": f"j{idx}", "mark_index": idx, "status": "verified"})
    (run_dir / "manifest--20261116T000000.000000Z.json").write_text(json.dumps({"jobs": entries}))


_STATS = ("prompt_entropy", "entropy")


def _assert_same_stats(a: dict, b: dict, rtol: float) -> None:
    assert a["jobs"] == b["jobs"]
    for stat in _STATS:
        for suffix in ("_mean", "_global_mean", "_window_mean", "_sd"):
            assert a[stat + suffix] == pytest.approx(b[stat + suffix], rel=rtol, nan_ok=True), stat + suffix
        assert a[stat + "_jobs"] == b[stat + "_jobs"]
        np.testing.assert_allclose(a[stat + "_layer"], b[stat + "_layer"], rtol=rtol)
    assert a["ratio_mean"] == pytest.approx(b["ratio_mean"], rel=max(rtol, 1e-6))
    np.testing.assert_allclose(a["ratio_layer_head"], b["ratio_layer_head"], rtol=max(rtol, 1e-6))
    assert a["pad_tokens_mean"] == b["pad_tokens_mean"]


def test_read_captures_gives_the_same_statistics_for_mass_summary_and_mixed_arms(tmp_path: Path) -> None:
    caps = [synthetic_capture(300, layers=LAYERS), synthetic_capture(301, layers=LAYERS, n_completion=17, boost=1.0)]
    for name, kinds in (("mass", ("mass", "mass")), ("summary", ("summary", "summary")),
                        ("mixed", ("mass", "summary"))):
        _mirror(tmp_path / name, {i: (cap, kind, "summary_f16") for i, (cap, kind) in enumerate(zip(caps, kinds))})
    out = {name: ar.read_captures(GEMMA, tmp_path / name, arms=("intens",), config=CONFIG)["intens"]
           for name in ("mass", "summary", "mixed")}
    _assert_same_stats(out["summary"], out["mass"], rtol=1e-9)
    _assert_same_stats(out["mixed"], out["mass"], rtol=1e-9)
    assert out["summary"]["summary_jobs"] == 2 and out["mixed"]["summary_jobs"] == 1
    assert out["mass"]["summary_jobs"] == 0
    assert out["summary"]["prompt_entropy_v1_jobs"] == 0


def test_the_plugins_unrounded_summary_reads_within_float16_precision_of_mass(tmp_path: Path) -> None:
    caps = [synthetic_capture(310, layers=LAYERS), synthetic_capture(311, layers=LAYERS, boost=1.0)]
    _mirror(tmp_path / "m", {i: (cap, "mass", "summary") for i, cap in enumerate(caps)})
    _mirror(tmp_path / "s", {i: (cap, "summary", "summary") for i, cap in enumerate(caps)})
    a = ar.read_captures(GEMMA, tmp_path / "m", arms=("intens",), config=CONFIG)["intens"]
    b = ar.read_captures(GEMMA, tmp_path / "s", arms=("intens",), config=CONFIG)["intens"]
    for stat in _STATS:
        assert a[stat + "_mean"] == pytest.approx(b[stat + "_mean"], rel=1e-3)


def test_read_captures_weights_every_summary_job_equally(tmp_path: Path) -> None:
    """Mean per response first, then over responses: a long response does not outweigh a short one."""
    short = synthetic_capture(320, layers=LAYERS, n_completion=3, boost=-2.0)
    long = synthetic_capture(321, layers=LAYERS, n_completion=40, boost=2.0)
    _mirror(tmp_path, {0: (short, "summary", "summary"), 1: (long, "summary", "summary")})
    out = ar.read_captures(GEMMA, tmp_path, arms=("intens",), config=CONFIG)["intens"]
    per_job = [cap["summary"]["sum_prompt_entropy"].sum() / cap["summary"]["n_prompt_entropy"].sum()
               for cap in (short, long)]
    pooled = (sum(cap["summary"]["sum_prompt_entropy"].sum() for cap in (short, long))
              / sum(cap["summary"]["n_prompt_entropy"].sum() for cap in (short, long)))
    assert abs(np.mean(per_job) - pooled) > 1e-2   # the two readings differ on this data
    assert out["prompt_entropy_mean"] == pytest.approx(np.mean(per_job), rel=1e-12)
    ent_per_job = [cap["summary"]["sum_entropy"].sum() / (_p(cap) * 4 * 4) for cap in (short, long)]
    assert out["entropy_mean"] == pytest.approx(np.mean(ent_per_job), rel=1e-12)
    assert out["prompt_entropy_jobs"] == 2
    assert out["prompt_entropy_sd"] == pytest.approx(np.std(per_job, ddof=1), rel=1e-9)
