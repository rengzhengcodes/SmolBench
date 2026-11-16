"""Replay of the deduction (Horn) transcripts through the attention capture, offline.

The Horn rows are cells of ``rebuttal/results/horn/<model>.jsonl``; each was produced by a
system message (the cell's ``system.md``) and a user message (its ``prompt.md``). These
tests build a tiny rung and rows file, rebuild the sequences with a stub tokenizer and a
system-aware stub template (and the real cached templates where present), and drive the
plan, the replay (fake box, dict S3), the post-hoc audit, the pull and the reader.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import pytest

from smolbench.evals import attention
from tests._paths import REPO_ROOT, load_by_path
from tests.evals.test_attention import FakeS3
from tests.evals.test_attention_analysis import capture_npz, synthetic_capture

ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_horn_under_test")

GEMMA, NEMO, DSV31 = "gemma-4-31b", "nemotron-3-super-120b-a12b", "deepseek-v3.1"
S3_URI = "s3://bucket/bedrock-trio/attention"
SYSTEM = "You are a careful prover. Answer in the format."
PROMPTS = {
    "lem": "Facts: a(x).\nRules: b(x) from a(x).\nGoal: b(x).\n",
    "pad": "Facts: a(x).\nRules: b(x) from a(x).\nLorem ipsum dolor sit amet.\nGoal: b(x).\n",
}
CONFIG = {"num_hidden_layers": 2, "num_attention_heads": 4}

GEMMA_SPECIALS = ("<bos>", "<|turn>", "<turn|>", "<|think|>", "<|channel>", "<channel|>")
#: Renders the system message inside the system turn, after the thinking marker, as the real
#: Gemma-4 template does.
SYS_TEMPLATE = (
    "{{ bos_token }}<|turn>system\n{% if enable_thinking %}<|think|>\n{% endif %}"
    "{% for m in messages %}{% if m['role'] == 'system' %}{{ m['content'] | trim }}{% endif %}{% endfor %}"
    "<turn|>\n{% for m in messages %}{% if m['role'] == 'user' %}<|turn>user\n{{ m['content'] | trim }}"
    "<turn|>\n{% endif %}{% endfor %}{% if add_generation_prompt %}<|turn>model\n{% endif %}")
#: A template that silently drops any system message.
NO_SYS_TEMPLATE = (
    "{{ bos_token }}{% for m in messages %}{% if m['role'] == 'user' %}<|turn>user\n{{ m['content'] }}"
    "<turn|>\n{% endif %}{% endfor %}{% if add_generation_prompt %}<|turn>model\n{% endif %}")


class CharTokenizer:
    """Each listed special string is one token, every other character one token."""

    def __init__(self, specials=GEMMA_SPECIALS):
        self.specials = tuple(sorted(specials, key=len, reverse=True))
        self.vocab: dict = {}
        self._re = re.compile("|".join(re.escape(s) for s in self.specials) + "|.", re.S)

    def encode_offsets(self, text):
        return [(m.start(), m.end()) for m in self._re.finditer(text)]

    def encode_ids(self, text):
        return [self.vocab.setdefault(text[s:e], len(self.vocab)) for s, e in self.encode_offsets(text)]

    def decode_tokens(self, ids):
        inv = {v: k for k, v in self.vocab.items()}
        return [inv[int(i)] for i in ids]

    def token_to_id(self, token):
        return self.vocab.setdefault(token, len(self.vocab)) if token in self.specials else None


def template():
    return ar.ChatTemplate(SYS_TEMPLATE, bos_token="<bos>")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _write_rung(root: Path, rung: str = "m20", seeds=(100, 101), arms=("lem", "pad")) -> Path:
    for seed in seeds:
        for arm in arms:
            d = root / rung / f"s{seed:04d}" / arm
            d.mkdir(parents=True, exist_ok=True)
            (d / "prompt.md").write_text(PROMPTS[arm] + f"Seed {seed}.\n", encoding="utf-8")
            (d / "system.md").write_text(SYSTEM, encoding="utf-8")
    return root


def _row(seed, arm, rep, *, rung="m20", model=GEMMA, verdict="success", ts="2026-11-16T07:00:00Z",
         content="derive b(x) from a(x)", reasoning="I see a(x).", completion_tokens=11, **over) -> dict:
    row = {"model": "google.gemma-4-31b", "spec_key": model, "rung": rung, "arm": arm, "seed": seed,
           "rep": rep, "prompt_sha256": _sha(PROMPTS[arm] + f"Seed {seed}.\n"), "provider_system_prompt": False,
           "ts": ts, "verdict": verdict, "finish_reason": "stop", "content": content, "reasoning": reasoning,
           "completion_tokens": completion_tokens, "prompt_tokens": 50, "provider": "bedrock-mantle:us-east-1"}
    if verdict == "exception":
        for key in ("content", "reasoning", "finish_reason", "completion_tokens", "prompt_tokens"):
            row.pop(key)
        row["reason"] = "ReadTimeout"
    row.update(over)
    return row


def _write_rows(path: Path, rows, *, torn: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r) + "\n" for r in rows)
    if torn is not None:
        text += torn  # a last line without its newline: a writer was cut off mid-row
    path.write_text(text, encoding="utf-8")
    return path


def _basic(tmp_path: Path, rows=None):
    rungs = _write_rung(tmp_path / "rungs")
    rows = rows if rows is not None else [_row(s, a, 0) for s in (100, 101) for a in ("lem", "pad")]
    return rungs, _write_rows(tmp_path / "horn" / f"{GEMMA}.jsonl", rows)


def _build(rungs, rows_path, **kw):
    tok = kw.pop("tok", CharTokenizer())
    return ar.build_jobs(GEMMA, Path("unused"), "bedrock-trio/attention", tokenizer=tok, template=template(),
                         study="horn", horn_rows=rows_path, rungs_dir=rungs, **kw)


def _plan(rungs, rows_path, **kw):
    tok = CharTokenizer()
    return ar.plan_replay(models=[GEMMA], study="horn", horn_rows=rows_path, rungs_dir=rungs,
                          s3_uri=S3_URI, tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                          config_for=lambda m: CONFIG, **kw)[GEMMA]


# ------------------------------------------------------------------ sequence rebuild

def test_the_rebuild_renders_the_system_turn_before_the_user_turn() -> None:
    tok = CharTokenizer()
    query = PROMPTS["lem"]
    r = ar.rebuild_sequence(query, "think", "answer", tokenizer=tok, template=template(),
                            fmt=ar.REASONING_FORMATS[GEMMA], system=SYSTEM, pad_query_span=(0, 0))
    assert r.prompt_text.index(SYSTEM) < r.prompt_text.index(query.strip())
    assert r.completion_text == "<|channel>thought\nthink<channel|>answer<turn|>"
    n = len(r.prompt_ids)
    assert r.classes.index(3) == n and set(r.classes[n:]) == {3}
    assert 1 not in r.classes                                           # no pad class in the deduction study
    offsets = tok.encode_offsets(r.prompt_text)
    s0 = r.prompt_text.index(SYSTEM)
    in_system = [c for (s, e), c in zip(offsets, r.classes) if s >= s0 and e <= s0 + len(SYSTEM)]
    assert in_system and set(in_system) == {2}                          # system text: class 2, like the template
    q0 = r.prompt_text.index(query.strip())
    in_query = [c for (s, e), c in zip(offsets, r.classes) if s >= q0 and e <= q0 + len(query.strip())]
    assert set(in_query) == {0, 2} and in_query.count(0) > in_query.count(2)


def test_a_template_that_drops_the_system_message_is_refused() -> None:
    with pytest.raises(ar.TemplateMismatch, match="system"):
        ar.rebuild_sequence(PROMPTS["lem"], "t", "a", tokenizer=CharTokenizer(),
                            template=ar.ChatTemplate(NO_SYS_TEMPLATE, bos_token="<bos>"),
                            fmt=ar.REASONING_FORMATS[GEMMA], system=SYSTEM, pad_query_span=(0, 0))


def test_the_induction_rebuild_is_unchanged_without_a_system_message() -> None:
    r = ar.rebuild_sequence("ab", "r", "1", tokenizer=CharTokenizer(), template=template(),
                            fmt=ar.REASONING_FORMATS[GEMMA])
    assert "<|turn>system\n<|think|>\n<turn|>" in r.prompt_text


def test_the_approximations_list_what_a_system_message_adds() -> None:
    text = " ".join(ar.APPROXIMATIONS).lower()
    assert "system.md" in text and "deduction" in text


def _cached_tokenizer(model):
    from huggingface_hub import try_to_load_from_cache

    from smolbench.evals.providers import ec2
    from smolbench.evals.tokenization import HFTokenizer, _pinned_revision

    spec = ec2.EC2_DEPLOY_SPECS[model]
    rev = _pinned_revision(spec)
    path = try_to_load_from_cache(spec["hf_model_id"], "tokenizer.json", revision=rev)
    if not isinstance(path, str):
        pytest.skip(f"{model} tokenizer.json not in the local HF cache")
    return HFTokenizer.from_repo(spec["hf_model_id"], rev)


@pytest.mark.parametrize("model", [DSV31, NEMO, GEMMA])
def test_the_real_templates_render_the_system_turn(model, monkeypatch) -> None:
    from smolbench.deduction.horn.render import SYSTEM as HORN_SYSTEM

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    tok = _cached_tokenizer(model)
    try:
        real = ar.load_chat_template(model, local_files_only=True)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"{model} chat template not cached: {type(exc).__name__}")
    fmt = ar.REASONING_FORMATS[model]
    # The real rungs write conjunctions as U+2227; some byte-level tokenizers split it into
    # tokens whose character offsets overlap, which must not stop the deduction rebuild.
    query = PROMPTS["pad"] + "Rule: c(x) from a(x) \u2227 b(x).\n"
    r = ar.rebuild_sequence(query, "Step by step.", "derive b(x) from a(x)", tokenizer=tok, template=real,
                            fmt=fmt, system=HORN_SYSTEM, pad_query_span=(0, 0))
    ar.check_reasoning_format(model, tok, r.prompt_text)
    assert r.prompt_text.index(HORN_SYSTEM) < r.prompt_text.index(query.strip())
    assert 1 not in r.classes and r.classes.index(3) == len(r.prompt_ids)
    assert r.completion_ids[-1] == tok.token_to_id(fmt.end_of_turn)


# ------------------------------------------------------------------ selection and plan

def test_one_job_per_cell_with_the_earliest_generation(tmp_path: Path) -> None:
    rows = [
        # Cell (lem, 100, 0): a later row first in the file, then the earliest, then an
        # exception row earlier than both (it holds no generation and never counts).
        _row(100, "lem", 0, ts="2026-11-16T09:00:00Z", completion_tokens=999),
        _row(100, "lem", 0, ts="2026-11-16T08:00:00Z", completion_tokens=111),
        _row(100, "lem", 0, verdict="exception", ts="2026-11-16T07:00:00Z"),
        # Cell (pad, 100, 0): only an exception row: not planned, counted.
        _row(100, "pad", 0, verdict="exception"),
        _row(101, "lem", 0, completion_tokens=7),
        _row(101, "lem", 1, completion_tokens=8),
        _row(101, "pad", 2, completion_tokens=9),
    ]
    rungs, rows_path = _basic(tmp_path, rows)
    planned, errors = _build(rungs, rows_path)
    assert errors == []
    cells = {(p.run.arm, p.seed, p.rep): p for p in planned}
    assert sorted(cells) == [("lem", 100, 0), ("lem", 101, 0), ("lem", 101, 1), ("pad", 101, 2)]
    assert cells[("lem", 100, 0)].bedrock_token_counts == {"prompt_tokens": 50, "completion_tokens": 111}
    plan = _plan(rungs, rows_path)
    assert plan.per_arm["lem"]["marks"] == 3 and plan.per_arm["pad"]["marks"] == 1
    assert plan.per_arm["pad"]["exception_rows"] == 1 and plan.per_arm["lem"]["exception_rows"] == 1
    assert plan.jobs == 4 and plan.errors == []


def test_the_filters_select_arms_seeds_and_replicates(tmp_path: Path) -> None:
    rows = [_row(s, a, r) for s in (100, 101) for a in ("lem", "pad") for r in (0, 1)]
    rungs, rows_path = _basic(tmp_path, rows)
    planned, _ = _build(rungs, rows_path, arms=["pad"], seeds=[101], reps=[1])
    assert [(p.run.arm, p.seed, p.rep) for p in planned] == [("pad", 101, 1)]
    plan = _plan(rungs, rows_path, arms=["lem"], reps=[0])
    assert plan.jobs == 2 and list(plan.per_arm) == ["lem"]
    assert _plan(rungs, rows_path, seeds=[]).jobs == 0


@pytest.mark.parametrize("bad, word", [
    (dict(prompt_sha256="0" * 16), "prompt_sha256"),
    (dict(seed=150), "prompt.md"),                      # no rendered rung folder for this seed
    (dict(provider_system_prompt=True), "provider_system_prompt"),
    (dict(spec_key=NEMO), "spec_key"),
    (dict(reasoning="a â\u0086\u0092 b"), "mis-decoded"),
])
def test_a_cell_that_cannot_be_rebuilt_faithfully_is_a_plan_error(tmp_path: Path, bad, word) -> None:
    broken = _row(100, "lem", 0)
    broken.update(bad)   # after construction: ``seed`` is also a positional of _row
    rows = [broken, _row(101, "lem", 0)]
    rungs, rows_path = _basic(tmp_path, rows)
    planned, errors = _build(rungs, rows_path)
    assert [(p.seed, p.rep) for p in planned] == [(101, 0)]
    assert len(errors) == 1 and word in errors[0], errors
    plan = _plan(rungs, rows_path)
    assert plan.per_arm["lem"]["errors"] == 1 and plan.jobs == 1


def test_a_torn_last_line_is_reported_and_the_rest_still_plans(tmp_path: Path) -> None:
    rungs = _write_rung(tmp_path / "rungs")
    rows_path = _write_rows(tmp_path / "horn" / f"{GEMMA}.jsonl", [_row(100, "lem", 0)],
                            torn='{"model": "google.gemma-4-31b", "spec_key": "gem')
    planned, errors = _build(rungs, rows_path)
    assert len(planned) == 1 and len(errors) == 1 and "torn" in errors[0], errors


def test_a_missing_rows_file_is_a_plan_error_not_a_crash(tmp_path: Path) -> None:
    rungs = _write_rung(tmp_path / "rungs")
    plan = _plan(rungs, tmp_path / "horn" / "absent.jsonl")
    assert plan.jobs == 0 and plan.errors and "absent.jsonl" in plan.errors[0]


def test_the_deduction_keys_and_ids_never_collide_with_the_induction_layout(tmp_path: Path) -> None:
    rungs, rows_path = _basic(tmp_path)
    planned, _ = _build(rungs, rows_path)
    by_cell = {(p.run.arm, p.seed, p.rep): p.job for p in planned}
    job = by_cell[("lem", 100, 0)]
    assert job.key == f"bedrock-trio/attention/deduction/horn/{GEMMA}/m20/lem/s100.rep0.npz"
    assert job.job_id == "horn.m20.lem.s100.rep0"
    npz, meta = attention.rank_keys(job.key, 3)
    assert npz.endswith("/m20/lem/s100.rep0.r3.npz") and meta.endswith("/m20/lem/s100.rep0.r3.json")
    assert len({j.job_id for j in by_cell.values()}) == len(by_cell) == 4
    assert not ar._CAPTURE_FILE_RE.match("s100.rep0.r3.npz")
    assert "/induction/" not in job.key and job.mode == "summary"


def test_horn_jobs_default_to_summary_and_the_plan_estimates_both_modes(tmp_path: Path) -> None:
    rungs, rows_path = _basic(tmp_path)
    summary = _plan(rungs, rows_path)
    mass = _plan(rungs, rows_path, mode="mass")
    assert summary.mode == "summary" and mass.mode == "mass"
    tp = summary.tp_estimate
    planned, _ = _build(rungs, rows_path)
    assert summary.est_capture_bytes == sum(2 * 4 * 13 * 8 + tp * p.job.n_tokens for p in planned)
    assert mass.est_capture_bytes == sum(
        2 * (p.job.n_tokens - p.job.query_start) * 4 * 7 * 2 + tp * p.job.n_tokens for p in planned)
    assert summary.per_arm["lem"]["est_capture_bytes"] + summary.per_arm["pad"]["est_capture_bytes"] == \
        summary.est_capture_bytes
    lem_prompt = [p.job.query_start for p in planned if p.run.arm == "lem"]
    assert summary.per_arm["lem"]["prompt_tokens"] == sum(lem_prompt)
    assert summary.per_arm["lem"]["bedrock_prompt_tokens"] == 100
    assert summary.per_arm["lem"]["bedrock_completion_tokens"] == 22


def test_the_capture_context_override_moves_the_over_context_line(tmp_path: Path) -> None:
    rungs, rows_path = _basic(tmp_path)
    planned, _ = _build(rungs, rows_path)
    lem = max(p.job.n_tokens for p in planned if p.run.arm == "lem")
    pad = min(p.job.n_tokens for p in planned if p.run.arm == "pad")
    assert lem < pad
    plan = _plan(rungs, rows_path, capture_max_model_len=lem)
    assert plan.capture_max_model_len == lem
    assert plan.per_arm["lem"]["over_context"] == 0 and plan.per_arm["pad"]["over_context"] == 2
    assert plan.over_context == 2
    with pytest.raises(ValueError, match="capture_max_model_len"):
        _plan(rungs, rows_path, capture_max_model_len=131072 + 1)
    with pytest.raises(ValueError, match="capture_max_model_len"):
        _plan(rungs, rows_path, capture_max_model_len=0)


# ------------------------------------------------------------------ replay

class HornBox:
    """Fake ec2 module: records the instance tag and state file; /attn uploads consistent captures."""

    EC2_REGIONS = ("us-east-1",)

    def __init__(self, s3: FakeS3, tp: int = 2, skip_rank: int | None = None) -> None:
        self.s3, self.tp, self.skip_rank = s3, tp, skip_rank
        self.calls: list = []
        self.batches: list = []
        self.env: dict = {}
        self._status: dict = {}

    def provision_spot_instance(self, instance_types=None, **kw):
        self.calls.append("provision")
        self.env = {k: os.environ.get(k) for k in ("EC2_EXPERIMENT_TAG", "EC2_STATE_FILE")}
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
            cap = synthetic_capture(400 + n_line, n_prompt=line["query_start"], classes=line["classes"],
                                    layers=((0, False), (0, True)), heads=4)
            ranks = {}
            for rank in range(payload["tp"]):
                blob = capture_npz(cap, rank, payload["tp"], kind)
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.put_object(Bucket="b", Key=key, Body=blob)
                n = len(line["prompt_token_ids"]) + len(line["completion_token_ids"])
                p = n - line["query_start"]
                meta = {"job_id": line["job_id"], "rank": rank, "tp": payload["tp"],
                        "model": payload["served_model_name"], "n_tokens": n, "bytes": len(blob), "mode": kind,
                        "capture_version": 3 if kind == "summary" else 2, "query_start": line["query_start"],
                        "layers": [0, 1], "num_heads_local": 2, "rows_shape": [2, p, 2, 4],
                        "gate_max_rel": 0.001, "gate_tol": 0.03}
                self.s3.put_object(Bucket="b", Key=meta_key, Body=json.dumps(meta).encode())
                ranks[str(rank)] = {"ok": True, "gate_max_rel": 0.001}
            results[line["job_id"]] = ranks
        self._status = {"running": False, "results": results, "error": None}
        return {"ok": True}

    def attn_status(self, state):
        return self._status

    def shutdown_instance(self, wait=True):
        self.calls.append("shutdown")


def _replay(tmp_path, rungs, rows_path, box, s3, monkeypatch, **kw):
    from smolbench.evals.providers import ec2 as real_ec2

    monkeypatch.setattr(ar, "STATE_DIR", tmp_path / "state")
    # The resume check expects every rank of the plan's tp (derived from the real provider
    # before any box exists); align it with the fake box's tp so a complete job is complete.
    monkeypatch.setattr(real_ec2, "derive_tp", lambda *a, **k: box.tp)
    tok = CharTokenizer()
    return ar.replay_model(
        GEMMA, Path("unused"), S3_URI, approved=kw.pop("approved", True), study="horn",
        horn_rows=rows_path, rungs_dir=rungs, tokenizer_for=lambda m: tok, template_for=lambda m: template(),
        config_for=lambda m: CONFIG, ec2=box, s3_client_factory=kw.pop("s3_client_factory", lambda: s3),
        poll_s=0, batch_timeout_s=10, url_ttl_s=99, **kw)


def test_the_replay_captures_summaries_under_the_deduction_layout(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)
    s3 = FakeS3()
    box = HornBox(s3)
    report = _replay(tmp_path, rungs, rows_path, box, s3, monkeypatch)
    assert sorted(report.verified) == sorted(f"horn.m20.{a}.s{s}.rep0" for s in (100, 101) for a in ("lem", "pad"))
    assert report.audit_failures == {} and report.failed == {}
    assert {line["mode"] for b in box.batches for line in b["jobs"]} == {"summary"}
    prefix = f"bedrock-trio/attention/deduction/horn/{GEMMA}/m20/"
    assert all(k.startswith(prefix) for k in s3.objects)
    assert sorted(re.sub(r"manifest--.*", "manifest", k[len(prefix):]) for k in report.manifests) == [
        "lem/manifest", "pad/manifest"]
    manifest = json.loads(s3.objects[[k for k in report.manifests if "/lem/" in k][0]])
    assert manifest["mode"] == "summary" and manifest["run"]["rung"] == "m20" and manifest["run"]["arm"] == "lem"
    entries = {e["job_id"]: e for e in manifest["jobs"]}
    assert set(entries) == {"horn.m20.lem.s100.rep0", "horn.m20.lem.s101.rep0"}
    entry = entries["horn.m20.lem.s100.rep0"]
    assert entry["status"] == "verified" and entry["seed"] == 100 and entry["rep"] == 0
    # The instance tag names the study, so a concurrent induction run of the model gets its own box.
    assert box.env["EC2_EXPERIMENT_TAG"] == ar.run_tag(GEMMA, study="horn") != ar.run_tag(GEMMA)
    assert ar.run_tag(GEMMA) == f"{ar.EC2_TAG}-{GEMMA}"
    assert box.env["EC2_EXPERIMENT_TAG"] in box.env["EC2_STATE_FILE"]
    assert box.calls[0] == "provision" and box.calls[-1] == "shutdown"
    # Resume: everything is stored, nothing is sent and no box is provisioned.
    box2 = HornBox(s3)
    again = _replay(tmp_path, rungs, rows_path, box2, s3, monkeypatch)
    assert box2.calls == [] and len(again.skipped_existing) == 4 and again.partial == []


def test_a_horn_job_missing_a_rank_is_partial(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)
    s3 = FakeS3()
    planned, _ = _build(rungs, rows_path)
    job = planned[0].job
    s3.objects[attention.rank_keys(job.key, 0)[0]] = b"x"
    s3.objects[attention.rank_keys(job.key, 0)[1]] = b"{}"
    report = _replay(tmp_path, rungs, rows_path, HornBox(s3), s3, monkeypatch)
    assert report.partial == [job.job_id] and job.job_id in report.skipped_existing
    assert len(report.verified) == 3


def test_the_approval_gate_comes_first_for_the_deduction_replay_too(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)

    def never():
        raise AssertionError("an S3 client was built")

    box = HornBox(FakeS3())
    with pytest.raises(ar.ApprovalRequired):
        _replay(tmp_path, rungs, rows_path, box, None, monkeypatch, approved=False, s3_client_factory=never)
    assert box.calls == []


def test_mass_mode_is_refused_for_the_deduction_replay_with_its_size(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)

    def never():
        raise AssertionError("an S3 client was built")

    from smolbench.evals.providers import ec2 as real_ec2

    box = HornBox(FakeS3())
    monkeypatch.setattr(real_ec2, "derive_tp", lambda *a, **k: box.tp)   # as _replay sets it
    mass_bytes = _plan(rungs, rows_path, mode="mass").est_capture_bytes
    with pytest.raises(ValueError) as info:
        _replay(tmp_path, rungs, rows_path, box, None, monkeypatch, mode="mass", s3_client_factory=never)
    assert f"{mass_bytes} bytes" in str(info.value) and box.calls == []
    # With the explicit override the mass capture runs.
    s3 = FakeS3()
    box = HornBox(s3)
    report = _replay(tmp_path, rungs, rows_path, box, s3, monkeypatch, mode="mass", allow_horn_mass=True)
    assert {line["mode"] for b in box.batches for line in b["jobs"]} == {"mass"} and len(report.verified) == 4


def test_the_capture_context_override_reaches_the_serve(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)
    planned, _ = _build(rungs, rows_path)
    longest = max(p.job.n_tokens for p in planned)
    s3 = FakeS3()
    box = HornBox(s3)
    report = _replay(tmp_path, rungs, rows_path, box, s3, monkeypatch, capture_max_model_len=longest - 1)
    assert ("serve", longest - 1) in box.calls
    assert len(report.over_context) >= 1 and len(report.verified) == 4 - len(report.over_context)
    with pytest.raises(ValueError, match="capture_max_model_len"):
        _replay(tmp_path, rungs, rows_path, HornBox(FakeS3()), FakeS3(), monkeypatch,
                capture_max_model_len=10 ** 7)


def test_audit_existing_works_for_the_deduction_layout(tmp_path) -> None:
    rungs, rows_path = _basic(tmp_path)
    planned, _ = _build(rungs, rows_path)
    s3 = FakeS3()
    for i, item in enumerate(planned):
        job = item.job
        cap = synthetic_capture(500 + i, n_prompt=job.query_start, classes=list(job.classes),
                                layers=((0, False), (0, True)), heads=4)
        for rank in range(2):
            npz_key, meta_key = attention.rank_keys(job.key, rank)
            blob = capture_npz(cap, rank, 2, "summary")
            s3.objects[npz_key] = blob
            p = job.n_tokens - job.query_start
            s3.objects[meta_key] = json.dumps({
                "job_id": job.job_id, "rank": rank, "tp": 2, "model": GEMMA, "n_tokens": job.n_tokens,
                "bytes": len(blob), "mode": "summary", "capture_version": 3, "query_start": job.query_start,
                "layers": [0, 1], "num_heads_local": 2, "rows_shape": [2, p, 2, 4], "gate_max_rel": 0.001,
                "gate_tol": 0.03}).encode()
    tok = CharTokenizer()
    report = ar.audit_existing(GEMMA, Path("unused"), S3_URI, study="horn", horn_rows=rows_path, rungs_dir=rungs,
                               tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                               config_for=lambda m: CONFIG, s3_client_factory=lambda: s3)
    assert len(report.verified) == 4 and not report.audit_failures and report.not_captured == 0
    assert len(report.manifests) == 2 and all("/deduction/horn/" in k for k in report.manifests)
    assert json.loads(s3.objects[report.manifests[0]])["post_hoc_audit"] is True
    # A second call finds every job recorded.
    again = ar.audit_existing(GEMMA, Path("unused"), S3_URI, study="horn", horn_rows=rows_path, rungs_dir=rungs,
                              tokenizer_for=lambda m: tok, template_for=lambda m: template(),
                              config_for=lambda m: CONFIG, s3_client_factory=lambda: s3)
    assert again.verified == [] and len(again.skipped_existing) == 4


# ------------------------------------------------------------------ pull and read

def test_pull_and_read_the_deduction_captures_and_the_two_study_table(tmp_path, monkeypatch) -> None:
    rungs, rows_path = _basic(tmp_path)
    s3 = FakeS3()
    report = _replay(tmp_path, rungs, rows_path, HornBox(s3), s3, monkeypatch)
    assert len(report.verified) == 4
    # Objects that must not be pulled into the deduction tree.
    s3.objects["bedrock-trio/attention/deduction/horn/_probe/x.npz"] = b"x"
    s3.objects[f"bedrock-trio/attention/deduction/horn/{GEMMA}/m20/lem/stray.txt"] = b"x"
    mirror = tmp_path / "mirror"
    written = ar.pull_captures(S3_URI, mirror, [GEMMA], study="horn", s3_client_factory=lambda: s3)
    assert written == 4 * 2 * 2 + 2                                     # npz + json per rank, two manifests
    files = sorted(p.relative_to(mirror).as_posix() for p in mirror.rglob("*") if p.is_file())
    assert all(f.startswith(f"deduction/horn/{GEMMA}/m20/") for f in files) and not any("stray" in f for f in files)
    out = ar.read_captures(GEMMA, mirror, study="horn", config=CONFIG)
    assert sorted(out) == ["lem", "pad"]
    lem = out["lem"]
    assert lem["jobs"] == 2 and lem["summary_jobs"] == 2 and lem["pad_tokens_mean"] == 0
    assert np.isnan(lem["ratio_mean"])                                  # no class-1 token anywhere
    assert np.isfinite(lem["prompt_entropy_mean"]) and lem["prompt_entropy_jobs"] == 2
    # Mean per response, then over responses, from each job's stored sums.
    per_job = []
    for seed in (100, 101):
        sums = [np.load(mirror / f"deduction/horn/{GEMMA}/m20/lem/s{seed}.rep0.r{r}.npz") for r in range(2)]
        per_job.append(sum(float(z["sum_prompt_entropy"].sum()) for z in sums)
                       / sum(int(z["n_prompt_entropy"].sum()) for z in sums))
    assert lem["prompt_entropy_mean"] == pytest.approx(np.mean(per_job), rel=1e-12)
    # The induction tree beside it: one mass capture of one arm.
    run_dir = mirror / "induction" / GEMMA / "seed=0" / "intens--2026-11-13T01:00:00.000001Z"
    run_dir.mkdir(parents=True)
    cap = synthetic_capture(600, layers=((0, False), (0, True)))
    for rank in range(2):
        (run_dir / f"q0.r{rank}.npz").write_bytes(capture_npz(cap, rank, 2, "mass"))
    (run_dir / "manifest--x.json").write_text(json.dumps({"jobs": [
        {"job_id": "j", "mark_index": 0, "status": "verified"}]}))
    table = ar.read_entropy_table(GEMMA, mirror, config=CONFIG)
    assert sorted(table) == [("horn", "lem"), ("horn", "pad"), ("induction", "intens")]
    assert table[("horn", "lem")]["prompt_entropy_mean"] == pytest.approx(lem["prompt_entropy_mean"])
    assert table[("induction", "intens")]["jobs"] == 1


def test_the_horn_reader_refuses_an_ambiguous_rung(tmp_path) -> None:
    for rung in ("m20", "m64"):
        (tmp_path / "deduction" / "horn" / GEMMA / rung / "lem").mkdir(parents=True)
    with pytest.raises(ValueError, match="rung"):
        ar.read_captures(GEMMA, tmp_path, study="horn", config=CONFIG)


def test_every_planned_deduction_job_carries_its_cells_system_turn(tmp_path: Path) -> None:
    """The planned token ids are the rendered system turn, then the user turn, then the response."""
    rungs, rows_path = _basic(tmp_path)
    tok = CharTokenizer()
    planned, errors = _build(rungs, rows_path, tok=tok)
    assert not errors and len(planned) == 4
    for item in planned:
        prompt = "".join(tok.decode_tokens(item.job.prompt_token_ids))
        query = PROMPTS[item.run.arm] + f"Seed {item.seed}.\n"
        assert prompt.index(SYSTEM) < prompt.index(query.strip()), item.job.job_id
        completion = "".join(tok.decode_tokens(item.job.completion_token_ids))
        assert completion == "<|channel>thought\nI see a(x).<channel|>derive b(x) from a(x)<turn|>"
