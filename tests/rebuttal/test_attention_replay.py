"""Offline tests of the Bedrock-transcript attention replay driver (``rebuttal/attention_replay.py``).

No AWS, no GPU, no network: S3 is a dict fake, the box is a fake that uploads through the
minted presigned URLs, tokenizers are the real cached ``tokenizer.json`` files when present
(``HF_HUB_OFFLINE``) and a character-level stub otherwise. Chat templates are not cached for
any of the three checkpoints, so the real-template tests skip unless they are.
"""
from __future__ import annotations

import io
import json
import logging
import math
import re
import signal
from pathlib import Path

import numpy as np
import pytest

from smolbench.evals import attention
from smolbench.evals.quiz import COMPLIANT, Mark, Marks
from tests._paths import REPO_ROOT, load_by_path
from tests.evals.test_attention import FakeS3

ar = load_by_path(REPO_ROOT / "rebuttal" / "attention_replay.py", "attention_replay_under_test")

GEMMA, NEMO, DSV31 = "gemma-4-31b", "nemotron-3-super-120b-a12b", "deepseek-v3.1"
PAD = " \t" * 40  # an 80-character whitespace run, like the noise arm's pad


class CharTokenizer:
    """Deterministic stub: each listed special string is one token, every other char one token."""

    def __init__(self, specials: tuple[str, ...]) -> None:
        self.name = "char-stub"
        self.specials = tuple(sorted(specials, key=len, reverse=True))
        self.vocab: dict[str, int] = {}
        self._re = re.compile("|".join(re.escape(s) for s in self.specials) + "|." if specials else ".",
                              re.S)

    def _id(self, piece: str) -> int:
        return self.vocab.setdefault(piece, len(self.vocab))

    def encode_offsets(self, text: str):
        return [(m.start(), m.end()) for m in self._re.finditer(text)]

    def encode_ids(self, text: str):
        return [self._id(text[s:e]) for s, e in self.encode_offsets(text)]

    def decode_tokens(self, ids):
        inv = {v: k for k, v in self.vocab.items()}
        return [inv[int(i)] for i in ids]

    def token_to_id(self, token: str):
        return self._id(token) if token in self.specials else None

    def count(self, text: str) -> int:
        return len(self.encode_ids(text))


DS_TEMPLATE = ("{{ bos_token }}{% for m in messages %}<｜User｜>{{ m['content'] }}{% endfor %}"
               "{% if add_generation_prompt %}<｜Assistant｜>{% if thinking %}<think>{% endif %}{% endif %}")
DS_SPECIALS = ("<｜begin▁of▁sentence｜>", "<｜User｜>", "<｜Assistant｜>", "<think>", "</think>",
               "<｜end▁of▁sentence｜>")
GEMMA_TEMPLATE = ("{{ bos_token }}{% if enable_thinking %}<|turn>system\n<|think|><turn|>\n{% endif %}"
                  "{% for m in messages %}<|turn>user\n{{ m['content'] | trim }}<turn|>\n{% endfor %}"
                  "{% if add_generation_prompt %}<|turn>model\n{% endif %}")
GEMMA_SPECIALS = ("<bos>", "<|turn>", "<turn|>", "<|think|>", "<|channel>", "<channel|>")


def ds_template():
    return ar.ChatTemplate(DS_TEMPLATE, bos_token="<｜begin▁of▁sentence｜>")


def gemma_template():
    return ar.ChatTemplate(GEMMA_TEMPLATE, bos_token="<bos>")


def runs_of(classes):
    out: list[list[int]] = []
    for c in classes:
        if out and out[-1][0] == c:
            out[-1][1] += 1
        else:
            out.append([c, 1])
    return [tuple(r) for r in out]


# ------------------------------------------------------------ sequence rebuild

def test_rebuild_labels_template_query_pad_and_completion_tokens() -> None:
    tok = CharTokenizer(DS_SPECIALS)
    query = "Rule: x" + PAD + "Q?"
    r = ar.rebuild_sequence(query, "think", "42", tokenizer=tok, template=ds_template(),
                            fmt=ar.REASONING_FORMATS[DSV31])
    assert r.prompt_text == "<｜begin▁of▁sentence｜><｜User｜>" + query + "<｜Assistant｜><think>"
    # The template opened the thinking block, so the completion does not repeat it.
    assert r.completion_text == "think</think>42<｜end▁of▁sentence｜>"
    assert len(r.classes) == len(r.prompt_ids) + len(r.completion_ids)
    # BOS + <｜User｜> are template (2); "Rule: x" informative (0) except its one space (2);
    # the 80-char run is pad (1); "Q?" informative; <｜Assistant｜><think> template; completion 3.
    assert runs_of(r.classes) == [(2, 2), (0, 5), (2, 1), (0, 1), (1, 80), (0, 2), (2, 2),
                                  (3, len(r.completion_ids))]
    assert r.classes.index(3) == len(r.prompt_ids)
    assert len(r.completion_ids) == 5 + 1 + 2 + 1


def test_rebuild_supplies_the_thinking_open_when_the_template_does_not() -> None:
    tok = CharTokenizer(GEMMA_SPECIALS)
    r = ar.rebuild_sequence("  hi  ", "plan", "7", tokenizer=tok, template=gemma_template(),
                            fmt=ar.REASONING_FORMATS[GEMMA])
    assert r.completion_text == "<|channel>thought\nplan<channel|>7<turn|>"
    assert r.prompt_text.endswith("<|turn>model\n")
    assert any("strip" in n for n in r.notes), r.notes  # the template trimmed the query
    assert set(r.classes[: len(r.prompt_ids)]) <= {0, 2} and r.classes.index(3) == len(r.prompt_ids)


def test_rebuild_refuses_a_template_that_drops_the_query() -> None:
    tok = CharTokenizer(DS_SPECIALS)
    with pytest.raises(ValueError):
        ar.rebuild_sequence("hello", "", "1", tokenizer=tok, template=ar.ChatTemplate("nothing"),
                            fmt=ar.REASONING_FORMATS[DSV31])


def test_reasoning_format_check_fails_loudly_on_a_wrong_guess() -> None:
    tok = CharTokenizer(("<|turn>",))  # no <|channel> / <channel|> / <turn|> specials
    with pytest.raises(ar.ReasoningFormatError):
        ar.check_reasoning_format(GEMMA, tok, "<|turn>model\n")


def _cached_tokenizer(model: str):
    from huggingface_hub import try_to_load_from_cache

    from smolbench.evals.providers import ec2
    from smolbench.evals.tokenization import HFTokenizer, _pinned_revision

    spec = ec2.EC2_DEPLOY_SPECS[model]
    rev = _pinned_revision(spec)
    path = try_to_load_from_cache(spec["hf_model_id"], "tokenizer.json", revision=rev)
    if not isinstance(path, str):
        pytest.skip(f"{model} tokenizer.json not in the local HF cache")
    return HFTokenizer.from_repo(spec["hf_model_id"], rev)


#: Minimal stand-ins that use each checkpoint's REAL special-token strings, so the real
#: tokenizer decides how they split; the real chat templates are exercised separately below.
STAND_IN_TEMPLATES = {
    DSV31: (DS_TEMPLATE, "<｜begin▁of▁sentence｜>"),
    NEMO: ("{% for m in messages %}<|im_start|>user\n{{ m['content'] }}<|im_end|>\n{% endfor %}"
           "{% if add_generation_prompt %}<|im_start|>assistant\n<think>\n{% endif %}", ""),
    GEMMA: (GEMMA_TEMPLATE, "<bos>"),
}


@pytest.mark.parametrize("model", [DSV31, NEMO, GEMMA])
def test_real_tokenizer_delimiters_and_class_boundaries(model: str, monkeypatch) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    tok = _cached_tokenizer(model)
    source, bos = STAND_IN_TEMPLATES[model]
    template = ar.ChatTemplate(source, bos_token=bos)
    fmt = ar.REASONING_FORMATS[model]
    query = "Sequence: 3 6 9" + PAD + "What comes next?"
    r = ar.rebuild_sequence(query, "Step by step.", "12", tokenizer=tok, template=template, fmt=fmt)
    # The guessed thinking delimiters exist as single special tokens in the real vocabulary.
    ar.check_reasoning_format(model, tok, r.prompt_text)
    for special in (fmt.think_close, fmt.end_of_turn):
        assert tok.token_to_id(special) is not None
        assert tok.encode_ids(special) == [tok.token_to_id(special)]
    assert r.completion_ids[-1] == tok.token_to_id(fmt.end_of_turn)
    assert tok.token_to_id(fmt.think_close) in r.completion_ids
    # Query rows start at the first completion token; nothing before it is class 3.
    q = len(r.prompt_ids)
    assert r.classes.index(3) == q and set(r.classes[q:]) == {3}
    # The pad class covers exactly the 80 pad characters, under the real merges.
    pieces = tok.decode_tokens([i for i, c in zip(r.prompt_ids, r.classes) if c == 1])
    assert "".join(pieces) == PAD
    # Template tokens before the query are class 2.
    first_query_char = r.prompt_text.index(query)
    offsets = tok.encode_offsets(r.prompt_text)
    assert all(c == 2 for (s, e), c in zip(offsets, r.classes) if e <= first_query_char)


@pytest.mark.parametrize("model", [DSV31, NEMO, GEMMA])
def test_real_chat_template_when_cached(model: str, monkeypatch) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    tok = _cached_tokenizer(model)
    try:
        template = ar.load_chat_template(model, local_files_only=True)
    except Exception as exc:  # noqa: BLE001 -- any load failure means "not cached here"
        pytest.skip(f"{model} chat template not cached: {type(exc).__name__}")
    fmt = ar.REASONING_FORMATS[model]
    query = "Sequence: 3 6 9" + PAD + "What comes next?"
    r = ar.rebuild_sequence(query, "Step by step.", "12", tokenizer=tok, template=template, fmt=fmt)
    ar.check_reasoning_format(model, tok, r.prompt_text)
    assert r.classes.index(3) == len(r.prompt_ids)
    assert "".join(tok.decode_tokens([i for i, c in zip(r.prompt_ids, r.classes) if c == 1])) == PAD


# ----------------------------------------------------------- results and plan

STAMP_A, STAMP_B = "2026-11-13T01:00:00.000001Z", "2026-11-13T02:00:00.000001Z"


def _write_results(root: Path, model: str) -> None:
    def marks(queries, reasoning="r"):
        return Marks(model=model, marks=tuple(
            Mark(query=q, answer=1, response="1", score=1, compliance=COMPLIANT, reasoning=reasoning)
            for q in queries))

    seed_dir = root / "induction" / model / "seed=0"
    seed_dir.mkdir(parents=True)
    (seed_dir / f"intens--{STAMP_A}.yaml").write_text(marks(["ab", "abcd"]).dumps())
    # A later run of the same arm: the earliest one wins, this must be ignored.
    (seed_dir / f"intens--{STAMP_B}.yaml").write_text(marks(["zzzzzzzz"]).dumps())
    (seed_dir / f"noise_intens--{STAMP_A}.yaml").write_text(marks(["ab" + PAD + "c"], None).dumps())


def _plan_kwargs(tok):
    return dict(tokenizer_for=lambda m: tok, template_for=lambda m: ds_template(),
                config_for=lambda m: {"num_hidden_layers": 61, "num_attention_heads": 128})


def test_plan_replay_counts_marks_tokens_and_labels_its_estimate(tmp_path: Path) -> None:
    _write_results(tmp_path, DSV31)
    tok = CharTokenizer(DS_SPECIALS)
    plan = ar.plan_replay(tmp_path, [DSV31], **_plan_kwargs(tok))[DSV31]
    assert plan.runs == 2 and plan.marks == 3 and plan.jobs == 3 and plan.errors == []
    assert plan.unreasoned_marks == 1
    # Each sequence: BOS, <｜User｜>, query chars, <｜Assistant｜>, <think>, then
    # "r"(or "") + </think> + "1" + EOS.
    lengths = {"ab": 2 + 2 + 2 + 4, "abcd": 2 + 4 + 2 + 4, "noise": 2 + 83 + 2 + 3}
    assert plan.per_arm["intens"]["marks"] == 2
    assert plan.per_arm["intens"]["total_tokens"] == lengths["ab"] + lengths["abcd"]
    assert plan.per_arm["noise_intens"]["max_tokens"] == lengths["noise"]
    assert plan.total_tokens == sum(lengths.values()) and plan.max_tokens == lengths["noise"]
    assert plan.instance_types == ar.INSTANCE_TYPES[DSV31]
    # The plugin captures MLA layers now; serving the model is what is unverified.
    assert plan.capture_supported and plan.unsupported_reason is None
    assert not plan.serve_verified and plan.serve_unverified_reason == ar.SERVE_UNVERIFIED[DSV31]
    assert plan.est_basis.startswith("ESTIMATE:") and "prompt_entropy" in plan.est_basis
    expected = 0
    tp = plan.tp_estimate
    for n_tokens, n_completion in ((10, 4), (12, 4), (90, 3)):
        # 4 mass + entropy + prompt_entropy + sink, float16
        expected += 61 * n_completion * 128 * 7 * 2 + tp * n_tokens
    assert plan.est_capture_bytes == expected
    assert "not stored" in plan.bedrock_token_counts
    assert plan.approximations


def test_plan_replay_records_a_missing_template_instead_of_raising(tmp_path: Path) -> None:
    _write_results(tmp_path, GEMMA)

    def no_template(model):
        raise ar.TemplateUnavailable("not cached")

    tok = CharTokenizer(GEMMA_SPECIALS)
    plans = ar.plan_replay(tmp_path, [GEMMA, NEMO], tokenizer_for=lambda m: tok,
                           template_for=no_template, config_for=lambda m: {})
    assert plans[GEMMA].jobs == 0 and plans[GEMMA].errors
    assert plans[NEMO].marks == 0  # no results at all for this model


# --------------------------------------------------------------- replay_model

class AuditedBox:
    """Fake ec2 module: provision/serve/shutdown recorded, /attn uploads like the plugin."""

    EC2_REGIONS = ("us-east-1",)

    def __init__(self, s3: FakeS3, tp: int = 2, fail_attn: bool = False, capture_version: int = 2) -> None:
        self.s3, self.tp, self.fail_attn = s3, tp, fail_attn
        # 2 = the current plugin; 1 = an old plugin (no prompt_entropy, no meta field).
        self.capture_version = capture_version
        self.calls: list[str] = []
        self.batches: list[dict] = []
        self._status: dict = {}

    def provision_spot_instance(self, instance_types=None, **kw):
        self.calls.append(f"provision:{','.join(instance_types)}")
        return {"instance_type": "p5.48xlarge", "public_ip": "x"}

    def derive_tp(self, model, instance_type, spec):
        return self.tp

    def serve_model(self, model, capture=False, **kw):
        box = self

        class Ctx:
            def __enter__(self):
                box.calls.append(f"serve:{model}:capture={capture}")
                return model

            def __exit__(self, *exc):
                return False

        return Ctx()

    def attn_start(self, state, payload):
        if self.fail_attn:
            raise RuntimeError("box unreachable")
        self.batches.append(payload)
        results = {}
        for line in payload["jobs"]:
            n = len(line["prompt_token_ids"]) + len(line["completion_token_ids"])
            qs = line["query_start"]
            ranks = {}
            for rank in range(payload["tp"]):
                p = n - qs
                mass = np.zeros((2, p, 2, 4), np.float16)
                # A rank-dependent term keeps rows summing to 1 and makes the ranks differ,
                # as ranks holding different heads do (the audit refuses identical ranks).
                mass[..., 0], mass[..., 3] = 0.5 - 0.05 * rank, 0.5 + 0.05 * rank
                buf = io.BytesIO()
                arrays = dict(mass=mass, entropy=np.ones((2, p, 2), np.float16),
                              sink=np.zeros((2, p, 2), np.float16),
                              has_sink=np.zeros(2, bool), sliding_window=np.zeros(2, np.int32))
                if self.capture_version >= 2:
                    arrays["prompt_entropy"] = np.full((2, p, 2), 0.5, np.float16)
                np.savez(buf, **arrays,
                         classes=np.asarray(line["classes"], np.uint8),
                         query_start=np.asarray(qs, np.int32), layers=np.arange(2, dtype=np.int32),
                         positions=np.asarray(line["positions"], np.int32))
                blob = buf.getvalue()
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.put_object(Bucket="b", Key=key, Body=blob)
                # The meta json the plugin writes, with the fields the content audit checks.
                self.s3.put_object(Bucket="b", Key=meta_key, Body=json.dumps(
                    {"job_id": line["job_id"], "rank": rank, "tp": payload["tp"],
                     "model": payload["served_model_name"], "n_tokens": n, "bytes": len(blob),
                     "mode": "mass", "query_start": qs, "layers": [0, 1], "num_heads_local": 2,
                     "rows_shape": [2, p, 2, 4], "gate_max_rel": 0.001, "gate_tol": 0.03,
                     **({"capture_version": self.capture_version} if self.capture_version >= 2 else {}),
                     }).encode())
                ranks[str(rank)] = {"ok": True, "gate_max_rel": 0.001}
            results[line["job_id"]] = ranks
        self._status = {"running": False, "results": results, "error": None}
        return {"ok": True}

    def attn_status(self, state):
        return self._status

    def shutdown_instance(self, wait=True):
        self.calls.append("shutdown")


def _replay(tmp_path, box, s3, model=GEMMA, **kw):
    tok = CharTokenizer(GEMMA_SPECIALS)
    return ar.replay_model(
        model, tmp_path, "s3://bucket/bedrock-trio/attention", approved=kw.pop("approved", True),
        tokenizer_for=lambda m: tok, template_for=lambda m: gemma_template(),
        config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4},
        ec2=box, s3_client_factory=lambda: s3, poll_s=0, batch_timeout_s=10, url_ttl_s=99, **kw)


@pytest.mark.parametrize("approved", [False, None, 1, "yes", "True"])
def test_replay_refuses_to_provision_without_explicit_approval(tmp_path, approved, capsys) -> None:
    _write_results(tmp_path, GEMMA)
    box = AuditedBox(FakeS3())

    def never():
        raise AssertionError("an S3 client was built without approval")

    with pytest.raises(ar.ApprovalRequired):
        ar.replay_model(GEMMA, tmp_path, approved=approved, ec2=box, s3_client_factory=never,
                        tokenizer_for=lambda m: CharTokenizer(GEMMA_SPECIALS),
                        template_for=lambda m: gemma_template(),
                        config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4})
    assert box.calls == []
    out = capsys.readouterr().out
    assert "p5.48xlarge" in out and "us-east-1" in out  # it said what it would launch


def test_replay_refuses_deepseek_before_any_aws_call(tmp_path) -> None:
    """Capture is supported, serving on the pinned image is not verified: refused by default."""
    _write_results(tmp_path, DSV31)
    box = AuditedBox(FakeS3())
    assert DSV31 not in ar.CAPTURE_UNSUPPORTED
    with pytest.raises(ar.ServeUnverified, match="tokenizer"):
        ar.replay_model(DSV31, tmp_path, approved=True, ec2=box,
                        s3_client_factory=lambda: (_ for _ in ()).throw(AssertionError("S3")),
                        **_plan_kwargs(CharTokenizer(DS_SPECIALS)))
    assert box.calls == []


def test_the_serve_refusal_sits_after_the_approval_gate(tmp_path) -> None:
    _write_results(tmp_path, DSV31)
    box = AuditedBox(FakeS3())
    with pytest.raises(ar.ApprovalRequired):
        ar.replay_model(DSV31, tmp_path, approved=False, ec2=box,
                        s3_client_factory=lambda: (_ for _ in ()).throw(AssertionError("S3")),
                        **_plan_kwargs(CharTokenizer(DS_SPECIALS)))
    assert box.calls == []


class ServeRecordingBox(AuditedBox):
    """AuditedBox that also records the keyword arguments of every serve call."""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.serve_kwargs: list[dict] = []

    def serve_model(self, model, capture=False, **kw):
        self.serve_kwargs.append(dict(kw))
        return super().serve_model(model, capture=capture, **kw)


def _replay_ds(tmp_path, box, s3, **kw):
    tok = CharTokenizer(DS_SPECIALS)
    return ar.replay_model(
        DSV31, tmp_path, "s3://bucket/bedrock-trio/attention", approved=True,
        tokenizer_for=lambda m: tok, template_for=lambda m: ds_template(),
        config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4},
        ec2=box, s3_client_factory=lambda: s3, poll_s=0, batch_timeout_s=10, url_ttl_s=99, **kw)


def test_replay_runs_deepseek_with_the_explicit_serve_override(tmp_path) -> None:
    """With allow_unverified_serve=True the run proceeds against the fake box, and the
    shorter capture context reaches the serve call."""
    _write_results(tmp_path, DSV31)
    s3 = FakeS3()
    box = ServeRecordingBox(s3)
    report = _replay_ds(tmp_path, box, s3, allow_unverified_serve=True)
    assert box.calls[0] == f"provision:{','.join(ar.INSTANCE_TYPES[DSV31])}"
    assert f"serve:{DSV31}:capture=True" in box.calls and box.calls[-1] == "shutdown"
    assert box.serve_kwargs == [{"max_model_len": ar.CAPTURE_MAX_MODEL_LEN[DSV31]}]
    assert ar.CAPTURE_MAX_MODEL_LEN[DSV31] == 49152
    assert len(report.verified) == 3 and not report.audit_failures and not report.failed


def test_a_job_over_the_capture_context_is_excluded_though_under_the_spec_context(tmp_path) -> None:
    """A ~50k-token job fits the spec's 131072 but not the 49152-token capture context:
    the plan excludes it and the replay never sends it."""
    from smolbench.evals.providers import ec2 as real_ec2

    assert real_ec2.EC2_DEPLOY_SPECS[DSV31]["max_model_len"] == 131072
    seed_dir = tmp_path / "induction" / DSV31 / "seed=0"
    seed_dir.mkdir(parents=True)
    long_query = "x" * 50_000          # one CharTokenizer token per character
    (seed_dir / f"intens--{STAMP_A}.yaml").write_text(Marks(model=DSV31, marks=tuple(
        Mark(query=q, answer=1, response="1", score=1, compliance=COMPLIANT, reasoning="r")
        for q in ("ab", long_query))).dumps())
    tok = CharTokenizer(DS_SPECIALS)
    plan = ar.plan_replay(tmp_path, [DSV31], **_plan_kwargs(tok))[DSV31]
    assert plan.jobs == 2 and plan.over_context == 1
    assert 49152 < plan.max_tokens < 131072
    assert plan.capture_max_model_len == 49152
    s3 = FakeS3()
    box = ServeRecordingBox(s3)
    report = _replay_ds(tmp_path, box, s3, allow_unverified_serve=True)
    assert len(report.over_context) == 1 and len(report.verified) == 1
    sent = [line["job_id"] for batch in box.batches for line in batch["jobs"]]
    assert report.over_context[0] not in sent and len(sent) == 1


def test_plan_summary_shows_capture_supported_and_serving_unverified(tmp_path) -> None:
    _write_results(tmp_path, DSV31)
    plan = ar.plan_replay(tmp_path, [DSV31], **_plan_kwargs(CharTokenizer(DS_SPECIALS)))[DSV31]
    text = plan.summary()
    assert "capture: supported" in text
    assert f"serving: UNVERIFIED: {ar.SERVE_UNVERIFIED[DSV31]}" in text
    assert "49152" in text                       # the context the plan excluded jobs against
    _write_results(tmp_path, GEMMA)
    gplan = ar.plan_replay(tmp_path, [GEMMA], tokenizer_for=lambda m: CharTokenizer(GEMMA_SPECIALS),
                           template_for=lambda m: gemma_template(),
                           config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4})[GEMMA]
    assert gplan.serve_verified and gplan.serve_unverified_reason is None
    assert "UNVERIFIED" not in gplan.summary() and "capture: supported" in gplan.summary()


def test_the_launch_summary_printed_before_the_gate_names_the_serve_risk(tmp_path, capsys) -> None:
    _write_results(tmp_path, DSV31)
    with pytest.raises(ar.ApprovalRequired):
        ar.replay_model(DSV31, tmp_path, approved=False, ec2=AuditedBox(FakeS3()),
                        **_plan_kwargs(CharTokenizer(DS_SPECIALS)))
    assert "serving: UNVERIFIED" in capsys.readouterr().out


def test_capture_unsupported_still_refuses_a_listed_model_unless_overridden(tmp_path, monkeypatch) -> None:
    _write_results(tmp_path, GEMMA)
    monkeypatch.setitem(ar.CAPTURE_UNSUPPORTED, GEMMA, "a test reason")
    box = AuditedBox(FakeS3())
    with pytest.raises(ar.CaptureUnsupported, match="a test reason"):
        _replay(tmp_path, box, box.s3)
    assert box.calls == []
    assert _replay(tmp_path, box, box.s3, allow_unsupported_capture=True).verified


def test_the_storage_estimate_uses_the_vendored_deepseek_config(tmp_path, monkeypatch) -> None:
    """61 attention layers (the unloaded MTP layer excluded), 128 heads, tp 8 on a p5e."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    assert ar.attention_shape(ar.load_model_config(DSV31, local_files_only=True)) == (61, 128)
    _write_results(tmp_path, DSV31)
    tok = CharTokenizer(DS_SPECIALS)
    plan = ar.plan_replay(tmp_path, [DSV31], tokenizer_for=lambda m: tok,
                          template_for=lambda m: ds_template())[DSV31]
    assert plan.tp_estimate == 8
    assert "layers=61, heads=128, tp=8" in plan.est_basis
    expected = sum(61 * c * 128 * 7 * 2 + 8 * n for n, c in ((10, 4), (12, 4), (90, 3)))
    assert plan.est_capture_bytes == expected


@pytest.mark.parametrize("kw, expected", [({}, "all"), ({"audit_arrays": "sample"}, "sample")])
def test_replay_audits_every_jobs_arrays_unless_told_to_sample(tmp_path, monkeypatch, kw, expected) -> None:
    _write_results(tmp_path, GEMMA)
    s3, seen, real = FakeS3(), [], ar.audit_captures

    def audit(*args, **kwargs):
        seen.append((kwargs["arrays"], kwargs.get("capture_version")))
        return real(*args, **kwargs)

    monkeypatch.setattr(ar, "audit_captures", audit)
    report = _replay(tmp_path, AuditedBox(s3), s3, **kw)
    assert seen == [(expected, 2)]  # new captures are audited as version 2
    assert report.verified and not report.audit_failures


def test_replay_refuses_a_provider_without_a_weight_mirror(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    box = AuditedBox(FakeS3())
    box.EC2_S3_MODEL_CACHE = ""  # what the real provider holds when the variable is unset
    with pytest.raises(RuntimeError, match="EC2_S3_MODEL_CACHE"):
        _replay(tmp_path, box, box.s3)
    assert box.calls == []
    box.EC2_S3_MODEL_CACHE = "s3://mirror/hf"
    assert _replay(tmp_path, box, box.s3).verified


def test_replay_rejects_a_bad_audit_mode_before_the_box_is_provisioned(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    box = AuditedBox(FakeS3())
    with pytest.raises(ValueError, match="audit_arrays"):
        _replay(tmp_path, box, box.s3, audit_arrays="every")
    assert box.calls == []


def test_replay_resumes_and_never_writes_a_key_twice(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    # A capture from an earlier invocation already sits under the first intens mark.
    existing = (f"bedrock-trio/attention/induction/{GEMMA}/seed=0/intens--{STAMP_A}/q0.r0.npz")
    s3.objects[existing] = b"earlier"
    box = AuditedBox(s3)
    report = _replay(tmp_path, box, s3)
    assert box.calls == ["provision:" + ",".join(ar.INSTANCE_TYPES[GEMMA]),
                         f"serve:{GEMMA}:capture=True", "shutdown"]
    sent = [line["job_id"] for b in box.batches for line in b["jobs"]]
    assert len(sent) == 2 and not any(j.endswith(".q0") and ".intens." in j for j in sent)
    assert len(report.verified) == 2 and not report.failed and not report.audit_failures
    assert s3.objects[existing] == b"earlier"
    assert len(s3.puts) == len(set(s3.puts)), "a key was written twice"
    assert report.manifests and all("manifest--" in k for k in report.manifests)
    manifest = json.loads(s3.objects[report.manifests[0]])
    assert manifest["mode"] == "mass" and manifest["capture"] == attention.CAPTURE_MARKER
    # The captured classes are the rebuilt ones: query rows start at the first completion token.
    for key in s3.objects:
        if key.endswith(".r0.npz") and key != existing:
            arrays = np.load(io.BytesIO(s3.objects[key]))
            classes = arrays["classes"].tolist()
            assert classes.index(3) == int(arrays["query_start"])

    # Second invocation: everything exists, so nothing is provisioned and nothing is written.
    puts_before = list(s3.puts)
    box2 = AuditedBox(s3)
    again = _replay(tmp_path, box2, s3)
    assert box2.calls == [] and s3.puts == puts_before
    assert len(again.skipped_existing) == 3


def test_shutdown_runs_when_a_capture_job_raises(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    box = AuditedBox(s3, fail_attn=True)
    with pytest.raises(RuntimeError, match="box unreachable"):
        _replay(tmp_path, box, s3)
    assert box.calls[-1] == "shutdown" and box.calls.count("shutdown") == 1


def test_the_audit_rejects_classes_that_differ_from_the_job(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()

    class WrongClassesBox(AuditedBox):
        def attn_start(self, state, payload):
            for line in payload["jobs"]:
                line["classes"] = [0] * (len(line["classes"]) - 1) + [3]
            return super().attn_start(state, payload)

    box = WrongClassesBox(s3)
    report = _replay(tmp_path, box, s3)
    assert report.audit_failures, "content audit passed captures whose classes are wrong"
    assert box.calls[-1] == "shutdown"


# ---------------------------------------------------------------- offline read

#: Config of the mirror fixtures: 3 attention layers, 4 heads (2 ranks x 2 local heads).
_MIRROR_CONFIG = {"num_hidden_layers": 3, "num_attention_heads": 4}


def _write_manifest_file(run_dir: Path, idx: int, status: str) -> None:
    """Write the manifest entry ``_write_manifests`` would record for mark ``idx``."""
    run_dir.mkdir(parents=True, exist_ok=True)
    entry = {"job_id": f"s0.x.q{idx}", "mark_index": idx, "status": status}
    (run_dir / f"manifest--q{idx}.json").write_text(json.dumps({"jobs": [entry]}))


def test_read_captures_returns_the_per_arm_pad_ratio(tmp_path) -> None:
    root = tmp_path / "mirror"
    base = root / "induction" / GEMMA / "seed=0" / f"noise_intens--{STAMP_A}"
    base.mkdir(parents=True)
    classes = np.asarray([2, 0, 1, 1, 1, 1, 0, 3, 3], np.uint8)  # 4 pads, query_start 7
    for rank in range(2):
        mass = np.zeros((3, 2, 2, 4), np.float32)
        mass[..., 1] = [[4 / 8], [4 / 9]]  # observed pad mass == the uniform prediction
        mass[..., 0] = 1 - mass[..., 1]
        np.savez(base / f"q0.r{rank}.npz", mass=mass.astype(np.float16),
                 entropy=np.zeros((3, 2, 2), np.float16), sink=np.zeros((3, 2, 2), np.float16),
                 classes=classes, query_start=np.asarray(7, np.int32),
                 layers=np.arange(3, dtype=np.int32), positions=np.asarray([8], np.int32))
    _write_manifest_file(base, 0, "verified")
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)
    assert set(out) == {"noise_intens"}
    summary = out["noise_intens"]
    assert summary["jobs"] == 1
    assert summary["ratio_layer_head"].shape == (3, 4)
    assert summary["ratio_mean"] == pytest.approx(1.0, abs=2e-3)
    # A version-1 capture (no prompt_entropy array): NaN prompt-entropy fields and a count,
    # never an exception; the whole-row entropy is still read.
    assert summary["prompt_entropy_v1_jobs"] == 1 and summary["prompt_entropy_jobs"] == 0
    assert math.isnan(summary["prompt_entropy_mean"]) and math.isnan(summary["prompt_entropy_sd"])
    assert np.isnan(summary["prompt_entropy_layer"]).all()
    assert summary["entropy_mean"] == 0.0 and summary["entropy_jobs"] == 1


# ------------------------------------------------------------ mis-decoded transcripts

@pytest.mark.parametrize("text", ["a â\u0086\u0092 b", "á»«", "x Ã© y"])
def test_looks_misdecoded_flags_utf8_text_read_as_latin1(text) -> None:
    assert ar.looks_misdecoded(text) is True


@pytest.mark.parametrize("text", ["a ∧ b → c", "ừ", "plain ascii", "", None, "café"])
def test_looks_misdecoded_passes_clean_text(text) -> None:
    assert ar.looks_misdecoded(text) is False


def test_looks_misdecoded_is_public() -> None:
    assert "looks_misdecoded" in ar.__all__


def test_a_misdecoded_mark_is_reported_and_not_planned(tmp_path: Path) -> None:
    """One bad field drops that mark into the error list; the run's other marks still plan."""
    seed_dir = tmp_path / "induction" / DSV31 / "seed=0"
    seed_dir.mkdir(parents=True)
    rows = [
        ("ab", "r", "1"),                          # q0 clean
        ("ab", "r", "â\u0086\u0092"),         # q1 response mis-decoded ("→" read as latin-1)
        ("a → b", "r", "1"),                  # q2 clean, non-ASCII
        ("ab", "x Ã©", "1"),             # q3 reasoning mis-decoded
        ("a á»« b", "r", "1"),      # q4 query mis-decoded
    ]
    marks = Marks(model=DSV31, marks=tuple(
        Mark(query=q, answer=1, response=resp, score=1, compliance=COMPLIANT, reasoning=reason)
        for q, reason, resp in rows))
    path = seed_dir / f"intens--{STAMP_A}.yaml"
    path.write_text(marks.dumps())
    assert Marks.loads(path.read_text()).marks[1].response == "â\u0086\u0092"  # stored as-is

    jobs, errors = ar.build_jobs(DSV31, tmp_path, "pfx", tokenizer=CharTokenizer(DS_SPECIALS),
                                 template=ds_template())
    assert [j.mark_index for j in jobs] == [0, 2]
    assert len(errors) == 3, errors
    for idx, field_name in ((1, "response"), (3, "reasoning"), (4, "query")):
        (line,) = [e for e in errors if f"#q{idx}:" in e]
        assert str(path) in line and field_name in line, line


# ------------------------------------------------------------ chat-template fallback

_TPL_REV = "0123456789abcdef0123456789abcdef01234567"


def _fake_hub_cache(root: Path, *, not_in_repo_marker: bool) -> Path:
    """A hub cache holding tokenizer_config.json, and optionally the hub's "not in repo" marker."""
    repo = root / "models--org--tpl"
    snap = repo / "snapshots" / _TPL_REV
    snap.mkdir(parents=True)
    (snap / "tokenizer_config.json").write_text(json.dumps(
        {"chat_template": "CONFIG {{ messages[0]['content'] }}", "bos_token": "<s>", "eos_token": "</s>"}))
    if not_in_repo_marker:
        marker = repo / ".no_exist" / _TPL_REV / "chat_template.jinja"
        marker.parent.mkdir(parents=True)
        marker.touch()
    return snap


def _point_hub_at(monkeypatch, root: Path) -> None:
    import huggingface_hub.constants as hub_constants

    monkeypatch.setattr(hub_constants, "HF_HUB_CACHE", str(root))
    monkeypatch.setattr(ar, "_spec_repo_revision", lambda model: ({}, "org/tpl", _TPL_REV))


def test_an_uncached_template_file_offline_is_not_replaced_by_the_config_entry(tmp_path, monkeypatch) -> None:
    """Offline, "not in the cache" is not "not in the repo": falling back could pick another template."""
    _fake_hub_cache(tmp_path, not_in_repo_marker=False)
    _point_hub_at(monkeypatch, tmp_path)
    with pytest.raises(ar.TemplateUnavailable, match="chat_template.jinja"):
        ar.load_chat_template("any", local_files_only=True)


def test_a_cached_not_in_repo_answer_falls_back_to_the_config_entry(tmp_path, monkeypatch) -> None:
    """The hub's .no_exist marker records a real "file not in the repo" answer: fallback is allowed."""
    _fake_hub_cache(tmp_path, not_in_repo_marker=True)
    _point_hub_at(monkeypatch, tmp_path)
    template = ar.load_chat_template("any", local_files_only=True)
    assert template.source.startswith("CONFIG") and template.bos_token == "<s>"


def test_a_remote_not_in_repo_answer_falls_back_to_the_config_entry(tmp_path, monkeypatch) -> None:
    import httpx
    import huggingface_hub
    from huggingface_hub.errors import RemoteEntryNotFoundError

    snap = _fake_hub_cache(tmp_path, not_in_repo_marker=False)
    _point_hub_at(monkeypatch, tmp_path)

    def fake_download(repo, filename, revision=None, local_files_only=False, **kw):
        if filename == "chat_template.jinja":
            raise RemoteEntryNotFoundError(
                "404", response=httpx.Response(404, request=httpx.Request("HEAD", "https://hub/x")))
        return str(snap / filename)

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fake_download)
    template = ar.load_chat_template("any")
    assert template.source.startswith("CONFIG")


# ------------------------------------------------------------ resume: partial rank sets

def _gemma_jobs(tmp_path):
    jobs, errors = ar.build_jobs(GEMMA, tmp_path, "bedrock-trio/attention",
                                 tokenizer=CharTokenizer(GEMMA_SPECIALS), template=gemma_template())
    assert not errors
    return [p.job for p in jobs]


def _store_keys(s3, job, ranks, *, meta=True):
    for rank in ranks:
        npz_key, meta_key = attention.rank_keys(job.key, rank)
        s3.objects[npz_key] = b"x"
        if meta:
            s3.objects[meta_key] = b"{}"


def _plan_tp(tmp_path) -> int:
    tok = CharTokenizer(GEMMA_SPECIALS)
    plan = ar.plan_replay(tmp_path, [GEMMA], tokenizer_for=lambda m: tok,
                          template_for=lambda m: gemma_template(),
                          config_for=lambda m: {"num_hidden_layers": 2, "num_attention_heads": 4})[GEMMA]
    return plan.tp_estimate


def test_a_job_missing_a_top_rank_is_reported_partial(tmp_path, caplog) -> None:
    """Ranks 0..tp-2 stored, rank tp-1 missing: skipped forever unless reported."""
    _write_results(tmp_path, GEMMA)
    tp = _plan_tp(tmp_path)
    assert tp is not None and tp >= 2
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    _store_keys(s3, jobs[0], range(tp))
    _store_keys(s3, jobs[1], range(tp - 1))
    _store_keys(s3, jobs[2], range(tp))
    box = AuditedBox(s3)
    with caplog.at_level(logging.WARNING):
        report = _replay(tmp_path, box, s3)
    assert box.calls == []  # everything has keys: nothing is provisioned
    assert report.partial == [jobs[1].job_id]
    for key in attention.rank_keys(jobs[1].key, tp - 1):
        assert key in caplog.text, caplog.text


def test_partial_falls_back_to_rank_zero_when_tp_is_unknown(tmp_path, caplog, monkeypatch) -> None:
    _write_results(tmp_path, GEMMA)
    monkeypatch.setitem(ar.INSTANCE_TYPES, GEMMA, ())  # the plan cannot derive tp
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    s3.objects[attention.rank_keys(jobs[0].key, 0)[0]] = b"x"  # rank-0 npz without its json
    _store_keys(s3, jobs[1], [0])
    _store_keys(s3, jobs[2], [0, 1])
    box = AuditedBox(s3)
    with caplog.at_level(logging.WARNING):
        report = _replay(tmp_path, box, s3, instance_types=("p5.48xlarge",))
    assert box.calls == []
    assert report.partial == [jobs[0].job_id]
    assert "unknown" in caplog.text.lower()


# ------------------------------------------------------------ content audit

_AUDIT_CONFIG = {"num_hidden_layers": 2, "num_attention_heads": 4}


class CountingS3(FakeS3):
    def __init__(self) -> None:
        super().__init__()
        self.gets: list[str] = []

    def get_object(self, Bucket: str, Key: str) -> dict:
        self.gets.append(Key)
        return super().get_object(Bucket, Key)


def _store_capture(s3, job, tp=2, *, layers=2, heads=4, model=GEMMA, meta_over=None, entropy=None,
                   mass_row=None, prompt_entropy=None, windows=None, version=2, mass_over=None):
    """Store one job's per-rank objects as the plugin writes them; ``meta_over[rank]`` edits a meta.

    Ranks differ by a small rank-dependent term (they hold different heads); ``mass_row``
    replaces every row's four class masses, ``mass_over(rank)`` (``[L, P, H_local, 4]``) the whole array.
    ``version`` 2 writes ``prompt_entropy`` (default 0.5 everywhere, or the given
    ``[L, P, H_local]`` array; the string ``"omit"`` leaves it out) and ``capture_version``
    in the meta; ``version`` 1 writes neither. ``windows`` is the ``sliding_window`` array.
    """
    p = job.n_tokens - int(job.query_start)
    local = heads // tp
    for rank in range(tp):
        mass = np.zeros((layers, p, local, 4), np.float16)
        mass[..., 0], mass[..., 3] = 0.5 - 0.05 * rank, 0.5 + 0.05 * rank
        if mass_row is not None:
            mass[...] = np.asarray(mass_row, np.float16)
        if mass_over is not None:
            mass[...] = np.asarray(mass_over(rank), np.float16)
        ent = np.full((layers, p, local), 0.5, np.float16) if entropy is None else entropy
        extra = {}
        if version >= 2 and not (isinstance(prompt_entropy, str) and prompt_entropy == "omit"):
            pe = np.full((layers, p, local), 0.5) if prompt_entropy is None else prompt_entropy
            extra["prompt_entropy"] = np.asarray(pe).astype(np.float16)
        buf = io.BytesIO()
        np.savez(buf, mass=mass, entropy=ent.astype(np.float16), sink=np.zeros((layers, p, local), np.float16),
                 classes=np.asarray(job.classes, np.uint8), query_start=np.asarray(job.query_start, np.int32),
                 layers=np.arange(layers, dtype=np.int32), has_sink=np.zeros(layers, bool),
                 sliding_window=np.asarray(windows if windows is not None else [0] * layers, np.int32),
                 positions=np.asarray([job.n_tokens - 1], np.int32), **extra)
        blob = buf.getvalue()
        meta = {"job_id": job.job_id, "rank": rank, "tp": tp, "model": model, "n_tokens": job.n_tokens,
                "query_start": job.query_start, "mode": "mass", "layers": list(range(layers)),
                "num_heads_local": local, "rows_shape": [layers, p, local, 4],
                "gate_max_rel": 0.001, "gate_tol": 0.03, "bytes": len(blob)}
        if version >= 2:
            meta["capture_version"] = version
        meta.update((meta_over or {}).get(rank, {}))
        npz_key, meta_key = attention.rank_keys(job.key, rank)
        s3.objects[npz_key] = blob
        s3.objects[meta_key] = json.dumps(meta).encode()


def _audit(s3, jobs, **kw):
    return ar.audit_captures(s3, "b", jobs, 2, model=GEMMA, config=_AUDIT_CONFIG, **kw)


def test_the_audit_passes_a_consistent_capture(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    for job in jobs:
        _store_capture(s3, job)
    assert _audit(s3, jobs, arrays="all") == {j.job_id: None for j in jobs}


@pytest.mark.parametrize("meta_over, word", [
    ({1: {"rank": 0}}, "meta rank"),
    ({1: {"tp": 4}}, "meta tp"),
    ({0: {"model": "nemotron-3-super-120b-a12b"}}, "meta model"),
    ({0: {"job_id": "s0.intens.other.q9"}}, "meta job_id"),
    ({0: {"layers": [0, 1, 2], "rows_shape": [3, None, 2, 4]}}, "layer"),
    ({0: {"num_heads_local": 4}}, "num_heads_local"),
])
def test_the_audit_checks_every_meta_against_the_job_and_the_config(tmp_path, meta_over, word) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    for job in jobs:
        _store_capture(s3, job)
    # The defect sits on the LAST job of a run, which the array sample never downloads:
    # the meta checks must run for every job.
    victim = jobs[1]
    p = victim.n_tokens - int(victim.query_start)
    for rank_meta in meta_over.values():
        if "rows_shape" in rank_meta:
            rank_meta["rows_shape"] = [3, p, 2, 4]
    _store_capture(s3, victim, meta_over=meta_over)
    result = _audit(s3, jobs)
    assert result[victim.job_id] and word in result[victim.job_id].lower(), result
    assert result[jobs[0].job_id] is None and result[jobs[2].job_id] is None


def test_the_audit_rejects_a_wrong_rows_shape(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    for job in jobs:
        _store_capture(s3, job)
    _store_capture(s3, jobs[1], meta_over={0: {"rows_shape": [2, 1, 2, 4]}})
    assert "rows_shape" in (_audit(s3, jobs)[jobs[1].job_id] or "")


def test_the_audit_rejects_entropy_above_the_log_of_the_attended_positions(tmp_path) -> None:
    """Row i attends query_start + i + 1 keys, so its entropy is at most ln(query_start + i + 1)."""
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    job = jobs[0]
    p = job.n_tokens - int(job.query_start)
    ceiling0 = math.log(int(job.query_start) + 1)  # the first completion row's bound
    s3 = FakeS3()
    ok = np.full((2, p, 2), 0.5, np.float32)
    ok[:, 0, :] = ceiling0 - 0.05  # just under row 0's own bound: legal
    _store_capture(s3, job, entropy=ok)
    assert _audit(s3, [job])[job.job_id] is None
    bad = ok.copy()
    bad[1, 0, 1] = math.log(int(job.query_start) + 2) + 0.2  # above the bound even with a sink column
    _store_capture(s3, job, entropy=bad)
    reason = _audit(s3, [job])[job.job_id]
    assert reason and "entropy" in reason.lower(), reason


def test_arrays_all_downloads_and_checks_every_job(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = CountingS3()
    for job in jobs:
        _store_capture(s3, job)
    victim = jobs[1]  # second job of the intens run: outside the default sample
    p = victim.n_tokens - int(victim.query_start)
    bad = np.full((2, p, 2), 0.5, np.float32)
    bad[0, -1, 0] = 40.0
    _store_capture(s3, victim, entropy=bad)

    sampled = _audit(s3, jobs)
    assert sampled[victim.job_id] is None  # the sample never looked at its arrays
    sampled_npz = {k for k in s3.gets if k.endswith(".npz")}
    assert attention.rank_keys(victim.key, 0)[0] not in sampled_npz

    s3.gets.clear()
    full = _audit(s3, jobs, arrays="all")
    assert full[victim.job_id] and "entropy" in full[victim.job_id].lower()
    read = {k for k in s3.gets if k.endswith(".npz")}
    assert read == {attention.rank_keys(j.key, r)[0] for j in jobs for r in range(2)}


def test_the_audit_rejects_negative_mass_that_sums_to_one(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    _store_capture(s3, jobs[0], mass_row=[1.5, -0.5, 0.0, 0.0])  # sums to 1, sink 0
    reason = _audit(s3, jobs[:1])[jobs[0].job_id]
    assert reason and "mass minimum" in reason, reason


def test_the_audit_rejects_ranks_that_hold_identical_mass(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    jobs = _gemma_jobs(tmp_path)
    s3 = FakeS3()
    for job in jobs:
        _store_capture(s3, job)
    victim = jobs[1]
    s3.objects[attention.rank_keys(victim.key, 1)[0]] = s3.objects[attention.rank_keys(victim.key, 0)[0]]
    result = _audit(s3, jobs, arrays="all")
    assert result[victim.job_id] and "rank 1 duplicates rank 0" in result[victim.job_id], result
    assert result[jobs[0].job_id] is None and result[jobs[2].job_id] is None


def test_the_audit_refuses_an_unknown_arrays_mode(tmp_path) -> None:
    with pytest.raises(ValueError):
        _audit(FakeS3(), [], arrays="some")


# ------------------------------------------------------------ content audit: prompt entropy

def _pe_job(tmp_path):
    """The first Gemma job and its completion length P (at least 2 rows for the window tests)."""
    _write_results(tmp_path, GEMMA)
    job = _gemma_jobs(tmp_path)[0]
    p = job.n_tokens - int(job.query_start)
    assert p >= 2 and int(job.query_start) >= 3
    return job, p


def _windowed(p, *, row1_prompt_mass=0.0):
    """Layer 0 has a window of 2, layer 1 is global.

    A window w admits keys j >= pos - (w - 1), so completion row i (pos = query_start + i)
    sees a prompt key iff i < w - 1: on layer 0 only row 0 does (exactly one key,
    query_start - 1). Returns ``(mass_over, prompt_entropy)`` for a clean capture: rows
    without a prompt key carry zero prompt mass and NaN.
    """
    def mass_over(rank):
        mass = np.zeros((2, p, 2, 4), np.float32)
        mass[..., 0], mass[..., 3] = 0.5 - 0.05 * rank, 0.5 + 0.05 * rank
        mass[0, 1:, :, 0] = row1_prompt_mass
        mass[0, 1:, :, 3] = 1.0 - row1_prompt_mass
        return mass

    pe = np.full((2, p, 2), 0.5)
    pe[0, 0, :] = 0.0  # one attendable prompt key: a point mass
    pe[0, 1:, :] = np.nan
    return mass_over, pe


def test_the_audit_passes_a_windowed_capture_with_nan_exactly_past_the_prompt(tmp_path) -> None:
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    mass_over, pe = _windowed(p)
    _store_capture(s3, job, windows=[2, 0], mass_over=mass_over, prompt_entropy=pe)
    assert _audit(s3, [job], arrays="all")[job.job_id] is None


def test_the_audit_rejects_a_finite_value_where_no_prompt_key_is_attendable(tmp_path) -> None:
    """Boundary row i = w - 1 of a window w = 2 sees no prompt key, so it must be NaN."""
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    mass_over, pe = _windowed(p)
    pe[0, 1, 1] = 0.25
    _store_capture(s3, job, windows=[2, 0], mass_over=mass_over, prompt_entropy=pe)
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason and "row 1" in reason, reason


def test_the_audit_rejects_nan_on_the_last_row_that_still_sees_a_prompt_key(tmp_path) -> None:
    """Row i = w - 2 still sees key query_start - 1: NaN there is wrong even if the window is 2."""
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    mass_over, pe = _windowed(p)
    pe[0, 0, 0] = np.nan
    _store_capture(s3, job, windows=[2, 0], mass_over=mass_over, prompt_entropy=pe)
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason and "row 0" in reason, reason


def test_the_audit_rejects_nan_where_the_prompt_mass_is_clearly_positive(tmp_path) -> None:
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    pe = np.full((2, p, 2), 0.5)
    pe[1, p - 1, 0] = np.nan  # a global layer, prompt mass 0.45..0.5
    _store_capture(s3, job, prompt_entropy=pe)
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason and "nan" in reason.lower(), reason


def test_the_audit_rejects_nan_where_the_stored_prompt_mass_is_not_exactly_zero(tmp_path) -> None:
    """A NaN is accepted only with zero stored prompt mass, even where the window says no key."""
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    mass_over, pe = _windowed(p, row1_prompt_mass=1e-4)
    _store_capture(s3, job, windows=[2, 0], mass_over=mass_over, prompt_entropy=pe)
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason, reason


def test_the_audit_accepts_a_finite_value_whose_tiny_prompt_mass_rounded_away(tmp_path) -> None:
    """On a global layer a peaked row's prompt mass can underflow float16 to 0 (or sit just
    above it) while its prompt entropy is well defined: accepted."""
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()

    def mass_over(rank):
        mass = np.zeros((2, p, 2, 4), np.float32)
        mass[..., 0], mass[..., 3] = 0.5 - 0.05 * rank, 0.5 + 0.05 * rank
        mass[1, 0, :, 0], mass[1, 0, :, 3] = 0.0, 1.0        # exactly zero prompt mass
        mass[1, 1, :, 0], mass[1, 1, :, 3] = 5e-4, 1.0 - 5e-4  # below 1e-3
        return mass

    _store_capture(s3, job, mass_over=mass_over)
    assert _audit(s3, [job], arrays="all")[job.job_id] is None


@pytest.mark.parametrize("value, word", [
    (None, "above"),          # ln(query_start) + 0.2, filled in below
    (-0.05, "below"),
    (np.inf, "inf"),
])
def test_the_audit_rejects_prompt_entropy_out_of_range(tmp_path, value, word) -> None:
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    pe = np.full((2, p, 2), 0.5)
    pe[1, 0, 1] = math.log(int(job.query_start)) + 0.2 if value is None else value
    _store_capture(s3, job, prompt_entropy=pe)
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason and word in reason.lower(), reason


def test_the_audit_accepts_prompt_entropy_at_its_ceiling(tmp_path) -> None:
    """Over at most query_start prompt keys the entropy is at most ln(query_start)."""
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    pe = np.full((2, p, 2), math.log(int(job.query_start)))
    _store_capture(s3, job, prompt_entropy=pe)
    assert _audit(s3, [job], arrays="all")[job.job_id] is None


def test_the_audit_rejects_a_prompt_entropy_of_the_wrong_shape(tmp_path) -> None:
    job, p = _pe_job(tmp_path)
    s3 = FakeS3()
    _store_capture(s3, job, prompt_entropy=np.full((2, p, 1), 0.5))
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason and "shape" in reason.lower(), reason


def test_the_audit_fails_a_version_2_capture_without_prompt_entropy(tmp_path) -> None:
    job, _p = _pe_job(tmp_path)
    s3 = FakeS3()
    _store_capture(s3, job, prompt_entropy="omit")
    reason = _audit(s3, [job], arrays="all")[job.job_id]
    assert reason and "prompt_entropy" in reason, reason


def test_the_audit_reads_a_version_1_capture_unless_version_2_is_required(tmp_path) -> None:
    job, _p = _pe_job(tmp_path)
    s3 = FakeS3()
    _store_capture(s3, job, version=1)
    assert _audit(s3, [job], arrays="all")[job.job_id] is None
    reason = _audit(s3, [job], arrays="all", capture_version=2)[job.job_id]
    assert reason and "capture_version" in reason, reason


def test_replay_fails_the_audit_of_captures_from_an_old_plugin(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    report = _replay(tmp_path, AuditedBox(s3, capture_version=1), s3)
    assert not report.verified and report.audit_failures
    assert all("capture_version" in r for r in report.audit_failures.values()), report.audit_failures


# ------------------------------------------------------------ offline reader: rank sets, runs

def _mirror_job(run_dir: Path, idx: int, ranks, *, local_heads=2, pad_scale=1.0,
                status: str | None = "verified", version: int = 2) -> None:
    """Write one job's rank files; ``status`` goes into a manifest entry, ``None`` writes none.

    ``version`` 2 adds ``prompt_entropy`` (0.5) and ``sliding_window`` (all global).
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    if status is not None:
        _write_manifest_file(run_dir, idx, status)
    classes = np.asarray([2, 0, 1, 1, 1, 1, 0, 3, 3], np.uint8)  # 4 pads, query_start 7
    for rank in ranks:
        mass = np.zeros((3, 2, local_heads, 4), np.float32)
        mass[..., 1] = np.asarray([[4 / 8], [4 / 9]]) * pad_scale
        mass[..., 0] = 1 - mass[..., 1]
        extra = {}
        if version >= 2:
            extra = {"prompt_entropy": np.full((3, 2, local_heads), 0.5, np.float16),
                     "sliding_window": np.zeros(3, np.int32)}
        np.savez(run_dir / f"q{idx}.r{rank}.npz", mass=mass.astype(np.float16),
                 entropy=np.zeros((3, 2, local_heads), np.float16),
                 sink=np.zeros((3, 2, local_heads), np.float16), classes=classes,
                 query_start=np.asarray(7, np.int32), layers=np.arange(3, dtype=np.int32),
                 positions=np.asarray([8], np.int32), **extra)


def test_read_captures_refuses_a_job_missing_its_top_rank(tmp_path) -> None:
    """Ranks 0..6 of an 8-way job look like a complete tp=7 job unless heads are counted."""
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_job(run, 0, range(7), local_heads=1)
    with pytest.raises(ValueError, match="q0"):
        ar.read_captures(GEMMA, root, config={"num_hidden_layers": 3, "num_attention_heads": 8})


def test_read_captures_reads_only_the_earliest_run_per_seed_and_arm(tmp_path) -> None:
    root = tmp_path / "mirror"
    seed0 = root / "induction" / GEMMA / "seed=0"
    _mirror_job(seed0 / f"noise_intens--{STAMP_A}", 0, range(2))                 # ratio 1
    _mirror_job(seed0 / f"noise_intens--{STAMP_B}", 0, range(2), pad_scale=0.0)  # later: ratio 0
    _mirror_job(root / "induction" / GEMMA / "seed=1" / f"noise_intens--{STAMP_B}", 0, range(2))
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)
    assert out["noise_intens"]["jobs"] == 2  # seed 0's earliest run + seed 1's only run
    assert out["noise_intens"]["ratio_mean"] == pytest.approx(1.0, abs=2e-3)


def test_read_captures_reads_only_jobs_a_manifest_records_as_verified(tmp_path) -> None:
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_job(run, 0, range(2))                                               # ratio 1, verified
    _mirror_job(run, 1, range(2), pad_scale=0.0, status="audit_failed: bad")    # ratio 0, rejected
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)
    assert out["intens"]["jobs"] == 1 and out["intens"]["skipped_unverified"] == 1
    assert out["intens"]["ratio_mean"] == pytest.approx(1.0, abs=2e-3)  # the rejected job is absent


def test_read_captures_without_a_manifest_reads_nothing_and_reports_it(tmp_path, caplog) -> None:
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_job(run, 0, range(2), status=None)
    _mirror_job(run, 1, range(2), status=None)
    with caplog.at_level(logging.WARNING):
        out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)
    assert out == {}
    assert "skipping 2 job(s)" in caplog.text and str(run) in caplog.text, caplog.text


def test_read_captures_require_verified_false_reads_every_capture(tmp_path) -> None:
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_job(run, 0, range(2))
    _mirror_job(run, 1, range(2), status="audit_failed: bad")
    _mirror_job(run, 2, range(2), status=None)
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG, require_verified=False)
    assert out["intens"]["jobs"] == 3 and out["intens"]["skipped_unverified"] == 0


# ------------------------------------------------------------ offline reader: entropy

def _mirror_entropy_job(run_dir: Path, idx: int, *, p: int, pe_layers, ent_layers, windows=(0, 0, 0),
                        version: int = 2, local_heads: int = 2) -> None:
    """Write a verified 2-rank job with a per-layer constant prompt and whole-row entropy.

    ``prompt_entropy`` is NaN where the layer's window has slid past the prompt
    (row ``i >= w - 1``), as the plugin stores it.
    """
    _write_manifest_file(run_dir, idx, "verified")
    query_start = 7
    classes = np.asarray([0] * query_start + [3] * p, np.uint8)
    n_layers = len(ent_layers)
    pe = np.empty((n_layers, p, local_heads))
    ent = np.empty((n_layers, p, local_heads))
    for layer in range(n_layers):
        pe[layer], ent[layer] = pe_layers[layer], ent_layers[layer]
        if windows[layer]:
            pe[layer, windows[layer] - 1:] = np.nan
    for rank in range(2):
        mass = np.zeros((n_layers, p, local_heads, 4), np.float16)
        mass[..., 0] = 1.0
        extra = {"sliding_window": np.asarray(windows, np.int32)}
        if version >= 2:
            extra["prompt_entropy"] = pe.astype(np.float16)
        np.savez(run_dir / f"q{idx}.r{rank}.npz", mass=mass, entropy=ent.astype(np.float16),
                 sink=np.zeros((n_layers, p, local_heads), np.float16), classes=classes,
                 query_start=np.asarray(query_start, np.int32),
                 layers=np.arange(n_layers, dtype=np.int32),
                 positions=np.asarray([query_start + p - 1], np.int32), **extra)


def test_read_captures_weights_every_job_equally_in_the_entropy_means(tmp_path) -> None:
    """A long job and a short one: the mean of the two job means, not the pooled row mean."""
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_entropy_job(run, 0, p=8, pe_layers=[1.0] * 3, ent_layers=[2.0] * 3)
    _mirror_entropy_job(run, 1, p=2, pe_layers=[3.0] * 3, ent_layers=[4.0] * 3)
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)["intens"]
    # Pooled over rows these would be 1.4 and 2.4.
    assert out["prompt_entropy_mean"] == pytest.approx(2.0)
    assert out["entropy_mean"] == pytest.approx(3.0)
    assert out["prompt_entropy_jobs"] == 2 and out["entropy_jobs"] == 2
    assert out["prompt_entropy_sd"] == pytest.approx(math.sqrt(2.0))  # ddof=1 over the job means
    assert out["entropy_sd"] == pytest.approx(math.sqrt(2.0))
    np.testing.assert_allclose(out["prompt_entropy_layer"], [2.0, 2.0, 2.0])
    np.testing.assert_allclose(out["entropy_layer"], [3.0, 3.0, 3.0])
    assert out["prompt_entropy_global_mean"] == pytest.approx(2.0)
    assert math.isnan(out["prompt_entropy_window_mean"])  # no sliding-window layer
    assert math.isnan(out["entropy_window_mean"])
    assert out["prompt_entropy_v1_jobs"] == 0


def test_read_captures_splits_global_and_sliding_window_layers(tmp_path) -> None:
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    # Layer 1 has a window of 4: rows 3 and 4 of 5 see no prompt key (NaN).
    _mirror_entropy_job(run, 0, p=5, pe_layers=[1.0, 4.0, 2.0], ent_layers=[2.0, 5.0, 3.0],
                        windows=(0, 4, 0))
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)["intens"]
    # The job's own mean pools its defined values: 20 x 1.0 + 12 x 4.0 + 20 x 2.0 over 52.
    assert out["prompt_entropy_mean"] == pytest.approx(108 / 52)
    assert out["prompt_entropy_global_mean"] == pytest.approx(1.5)
    assert out["prompt_entropy_window_mean"] == pytest.approx(4.0)
    np.testing.assert_allclose(out["prompt_entropy_layer"], [1.0, 4.0, 2.0])
    assert out["entropy_mean"] == pytest.approx(10 / 3)
    assert out["entropy_global_mean"] == pytest.approx(2.5)
    assert out["entropy_window_mean"] == pytest.approx(5.0)
    assert out["prompt_entropy_jobs"] == 1 and math.isnan(out["prompt_entropy_sd"])  # one job


def test_read_captures_counts_version_1_jobs_and_leaves_them_out_of_prompt_entropy(tmp_path) -> None:
    root = tmp_path / "mirror"
    run = root / "induction" / GEMMA / "seed=0" / f"intens--{STAMP_A}"
    _mirror_entropy_job(run, 0, p=3, pe_layers=[1.0] * 3, ent_layers=[2.0] * 3)
    _mirror_entropy_job(run, 1, p=3, pe_layers=[9.0] * 3, ent_layers=[4.0] * 3, version=1)
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)["intens"]
    assert out["jobs"] == 2
    assert out["prompt_entropy_v1_jobs"] == 1 and out["prompt_entropy_jobs"] == 1
    assert out["prompt_entropy_mean"] == pytest.approx(1.0)
    assert out["entropy_jobs"] == 2 and out["entropy_mean"] == pytest.approx(3.0)


# ------------------------------------------------------------ shutdown and manifests

def test_write_manifest_sends_the_no_overwrite_condition() -> None:
    s3 = FakeS3()
    key = ar.write_manifest(s3, "b", "p/run/", {"jobs": []})
    assert s3.if_none_match == ["*"] and key in s3.objects


def test_write_manifest_refuses_a_key_the_listing_shows(monkeypatch) -> None:
    s3 = FakeS3()
    monkeypatch.setattr(ar, "format_run_ts", lambda _now: "fixed")
    s3.objects["p/run/manifest--fixed.json"] = b"{}"
    with pytest.raises(FileExistsError):
        ar.write_manifest(s3, "b", "p/run/", {"jobs": []})
    assert s3.puts == []  # refused before any put


def test_write_manifest_maps_s3_precondition_failed_to_file_exists(monkeypatch) -> None:
    """The key appeared between the listing and the put: S3 answers 412."""
    from botocore.exceptions import ClientError

    class RacyS3(FakeS3):
        def list_objects_v2(self, **kw):
            return {"Contents": []}  # the listing is blind to the racing writer

    s3 = RacyS3()
    monkeypatch.setattr(ar, "format_run_ts", lambda _now: "fixed")
    s3.objects["p/run/manifest--fixed.json"] = b"{}"
    with pytest.raises(FileExistsError):
        ar.write_manifest(s3, "b", "p/run/", {"jobs": []})

    class DeniedS3(FakeS3):
        def put_object(self, **kw):
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "PutObject")

    with pytest.raises(ClientError):  # any other S3 error still surfaces unchanged
        ar.write_manifest(DeniedS3(), "b", "p/run/", {"jobs": []})


class ShutdownBox(AuditedBox):
    """AuditedBox whose provision / capture / shutdown can be scripted to fail."""

    def __init__(self, s3, *, provision_exc=None, attn_exc=None, shutdown_script=()):
        super().__init__(s3)
        self.provision_exc, self.attn_exc = provision_exc, attn_exc
        self.shutdown_script = list(shutdown_script)
        self.shutdowns: list[dict] = []

    def provision_spot_instance(self, instance_types=None, **kw):
        if self.provision_exc is not None:
            self.calls.append("provision-failed")
            raise self.provision_exc
        return super().provision_spot_instance(instance_types, **kw)

    def attn_start(self, state, payload):
        if self.attn_exc is not None:
            raise self.attn_exc
        return super().attn_start(state, payload)

    def shutdown_instance(self, wait=True):
        self.calls.append("shutdown")
        self.shutdowns.append({"wait": wait, "sigint": signal.getsignal(signal.SIGINT)})
        step = self.shutdown_script.pop(0) if self.shutdown_script else None
        if step is not None:
            raise step


def test_a_keyboard_interrupt_during_capture_still_shuts_the_box_down(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    box = ShutdownBox(s3, attn_exc=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        _replay(tmp_path, box, s3)
    assert box.calls[-1] == "shutdown"


def test_a_failed_provision_still_attempts_shutdown(tmp_path) -> None:
    """A spot request can land a box and then fail: termination must run for provisioning too."""
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    box = ShutdownBox(s3, provision_exc=RuntimeError("spot request failed after launch"))
    with pytest.raises(RuntimeError, match="spot request failed"):
        _replay(tmp_path, box, s3)
    assert box.calls == ["provision-failed", "shutdown"]


def test_a_shutdown_failure_on_the_success_path_surfaces(tmp_path) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    box = ShutdownBox(s3, shutdown_script=[RuntimeError("TerminateInstances denied")])
    with pytest.raises(RuntimeError, match="TerminateInstances denied"):
        _replay(tmp_path, box, s3)


def test_an_interrupt_inside_shutdown_still_terminates_the_box(tmp_path) -> None:
    """Ctrl-C during the graceful /shutdown POST escapes before TerminateInstances: retry it.

    The retry skips the termination waiter and runs with SIGINT ignored, so a second
    Ctrl-C cannot cut it short; the interrupt is re-raised afterwards.
    """
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    before = signal.getsignal(signal.SIGINT)
    box = ShutdownBox(s3, shutdown_script=[KeyboardInterrupt(), None])
    with pytest.raises(KeyboardInterrupt):
        _replay(tmp_path, box, s3)
    assert len(box.shutdowns) == 2, box.shutdowns
    assert box.shutdowns[1]["wait"] is False
    assert box.shutdowns[1]["sigint"] == signal.SIG_IGN
    assert signal.getsignal(signal.SIGINT) == before  # restored


def test_a_failed_retry_after_an_interrupt_is_logged_and_the_interrupt_propagates(tmp_path, caplog) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    box = ShutdownBox(s3, shutdown_script=[KeyboardInterrupt(), RuntimeError("terminate failed")])
    with caplog.at_level(logging.ERROR), pytest.raises(KeyboardInterrupt):
        _replay(tmp_path, box, s3)
    assert len(box.shutdowns) == 2
    assert "terminate failed" in caplog.text


def test_a_manifest_failure_keeps_the_report(tmp_path, monkeypatch) -> None:
    _write_results(tmp_path, GEMMA)
    s3 = FakeS3()
    real_write = ar.write_manifest
    written: list[str] = []

    def flaky_write(client, bucket, prefix, payload):
        if written:
            raise OSError("manifest PUT denied")
        written.append(real_write(client, bucket, prefix, payload))
        return written[-1]

    monkeypatch.setattr(ar, "write_manifest", flaky_write)
    box = ShutdownBox(s3)
    report = _replay(tmp_path, box, s3)
    assert len(report.verified) == 3
    assert report.manifests == written  # the manifest written before the failure is kept
    assert report.manifest_error and "manifest PUT denied" in report.manifest_error
    assert box.calls[-1] == "shutdown"


# ------------------------------------------------------------ presigning client

def test_the_default_s3_client_signs_the_no_overwrite_condition(monkeypatch) -> None:
    """boto3 presigns S3 with SigV2 unless told otherwise, and SigV2 drops IfNoneMatch."""
    from urllib.parse import parse_qs, urlsplit

    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/dev/null")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/dev/null")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x" * 40)
    url = attention.presign_put(ar._default_s3_factory(), ar.BUCKET,
                                "bedrock-trio/attention/induction/m/seed=0/intens--t/q0.r0.npz",
                                "application/octet-stream", 60)
    signed = parse_qs(urlsplit(url).query).get("X-Amz-SignedHeaders", [""])[0].split(";")
    assert "if-none-match" in signed, url


# ------------------------------------------------- related_intens: pad by construction

#: Two real rule lines, then what the arm adds, then the question (``bt.QUESTION_START``).
REAL_RULES = "Every 2 positions write ab.\nEvery 3 positions write cd.\n"
ADDED_RULES = "Every 4 positions write mk.\n" * 3
TAIL_WS = "  \t"
QUESTION = "\nQuestion: next?"
RELATED_STAMP = "2026-11-14T01:00:00.000001Z"


def _related_query(question: str = QUESTION, added: str = ADDED_RULES, tail: str = TAIL_WS) -> str:
    return REAL_RULES + added + tail + question


def _write_related_results(root: Path, model: str, *, intens=None, related=None,
                           noise: bool = True) -> None:
    """Write a seed-0 fixture with ``intens``, ``related_intens`` and ``noise_intens`` runs.

    ``intens=None`` writes no intens run at all; the default queries pair question ``i`` of
    both arms. Reasoning is stored for every mark, so no mark is rebuilt with an empty block.
    """
    def marks(queries):
        return Marks(model=model, marks=tuple(
            Mark(query=q, answer=1, response="1", score=1, compliance=COMPLIANT, reasoning="r")
            for q in queries))

    seed_dir = root / "induction" / model / "seed=0"
    seed_dir.mkdir(parents=True)
    if intens is not False:
        queries = [REAL_RULES + QUESTION] if intens is None else intens
        (seed_dir / f"intens--{STAMP_A}.yaml").write_text(marks(queries).dumps())
    related = [_related_query(), _related_query("\nQuestion: and then?")] if related is None else related
    (seed_dir / f"related_intens--{RELATED_STAMP}.yaml").write_text(marks(related).dumps())
    if noise:
        (seed_dir / f"noise_intens--{STAMP_A}.yaml").write_text(marks(["ab" + PAD + "c"]).dumps())


def _build_related(root: Path, model: str = DSV31, tok=None):
    tok = tok or CharTokenizer(DS_SPECIALS)
    return ar.build_jobs(model, root, "p", tokenizer=tok, template=ds_template())


def _by_arm(planned):
    return {(p.run.arm, p.mark_index): p for p in planned}


def _query_classes(planned_job, query: str):
    """Classes of the query's tokens, for a character-level tokenizer (query starts after 2 specials)."""
    classes = planned_job.job.classes
    return list(classes[2:2 + len(query)])


def test_related_intens_pad_is_the_added_lines_and_trailing_whitespace(tmp_path: Path) -> None:
    _write_related_results(tmp_path, DSV31, intens=[REAL_RULES + QUESTION, REAL_RULES + "\nQuestion: and then?"])
    planned, errors = _build_related(tmp_path)
    assert errors == []
    jobs = _by_arm(planned)
    for idx, question in enumerate((QUESTION, "\nQuestion: and then?")):
        query = _related_query(question)
        classes = _query_classes(jobs[("related_intens", idx)], query)
        lo, hi = len(REAL_RULES), len(REAL_RULES) + len(ADDED_RULES) + len(TAIL_WS)
        # Class 1 exactly on the added lines and the trailing whitespace, and on nothing else.
        assert [i for i, c in enumerate(classes) if c == 1] == list(range(lo, hi))
        # Outside the pad: class 0 on every visible character, class 2 on whitespace.
        for i, (ch, c) in enumerate(zip(query, classes)):
            if not lo <= i < hi:
                assert c == (2 if ch.isspace() else 0), (i, ch, c)
        note = next(n for n in jobs[("related_intens", idx)].notes if "by construction" in n)
        assert note == f"pad span by construction: {hi - lo} tokens class 1, 0 straddle an edge of the span"
    # The other arms of the same fixture are as before: by rule, or no pad at all.
    noise = jobs[("noise_intens", 0)].job.classes
    assert noise.count(1) == len(PAD)
    assert 1 not in jobs[("intens", 0)].job.classes
    assert all("by construction" not in n for k in (("noise_intens", 0), ("intens", 0)) for n in jobs[k].notes)


def test_related_intens_question_i_is_compared_with_intens_question_i(tmp_path: Path) -> None:
    """The head comes from the intens query at the same question index."""
    _write_related_results(
        tmp_path, DSV31,
        intens=[REAL_RULES + QUESTION, "Every 9 positions write zz.\n" + QUESTION],
        related=[_related_query(), _related_query()],
    )
    planned, errors = _build_related(tmp_path)
    assert _by_arm(planned).keys() >= {("related_intens", 0)}
    assert ("related_intens", 1) not in _by_arm(planned)  # its head differs from intens q1's
    assert len(errors) == 1 and errors[0].endswith(
        "does not start with the intens query's rules") and "#q1" in errors[0]
    assert "related_intens--" in errors[0]


@pytest.mark.parametrize("case, reason", [
    ("no_intens_run", "no intens run for seed 0"),
    ("missing_question", "question 1 is missing from the intens run"),
    ("prefix_mismatch", "does not start with the intens query's rules"),
    ("empty_pad", "empty pad"),
    ("no_question_after_head", "no '\\nQuestion:' after the rules"),
])
def test_related_intens_mark_with_no_usable_intens_query_is_an_error_not_a_job(
        tmp_path: Path, case: str, reason: str) -> None:
    good = _related_query()
    if case == "no_intens_run":
        _write_related_results(tmp_path, DSV31, intens=False, related=[good])
        bad = 0
    elif case == "missing_question":
        _write_related_results(tmp_path, DSV31, related=[good, good])
        bad = 1
    elif case == "prefix_mismatch":
        _write_related_results(tmp_path, DSV31, related=["Every 5 positions write qq.\n" + QUESTION])
        bad = 0
    elif case == "empty_pad":
        _write_related_results(tmp_path, DSV31, related=[REAL_RULES + QUESTION])
        bad = 0
    else:
        _write_related_results(tmp_path, DSV31, related=[REAL_RULES + "no question here"])
        bad = 0
    planned, errors = _build_related(tmp_path)
    related_jobs = [p for p in planned if p.run.arm == "related_intens"]
    assert [p.mark_index for p in related_jobs] == ([0] if case == "missing_question" else [])
    assert len(errors) == 1
    assert f"related_intens--{RELATED_STAMP}.yaml#q{bad}: " in errors[0] and reason in errors[0]
    # The error is the plan's too, and the other arms still plan.
    plan = ar.plan_replay(tmp_path, [DSV31], **_plan_kwargs(CharTokenizer(DS_SPECIALS)))[DSV31]
    assert plan.errors == errors and plan.per_arm["noise_intens"]["marks"] == 1


def test_a_token_straddling_the_pad_edge_is_not_class_one_and_is_counted(tmp_path: Path) -> None:
    """Trailing " " plus the question's "\\n" merge into one token that crosses the span's end."""
    tok = CharTokenizer(DS_SPECIALS + (" \n",))
    query = _related_query(tail=" ")
    _write_related_results(tmp_path, DSV31, related=[query])
    planned, errors = _build_related(tmp_path, tok=tok)
    assert errors == []
    job = _by_arm(planned)[("related_intens", 0)]
    note = next(n for n in job.notes if "by construction" in n)
    assert note == (f"pad span by construction: {len(ADDED_RULES)} tokens class 1, "
                    "1 straddle an edge of the span")
    # The merged token (one id for two characters) follows the last class-1 token as class 2.
    classes = list(job.job.classes[2:])
    assert classes[len(REAL_RULES):len(REAL_RULES) + len(ADDED_RULES)] == [1] * len(ADDED_RULES)
    assert classes[len(REAL_RULES) + len(ADDED_RULES)] == 2


def test_rebuild_sequence_pad_span_is_validated_and_the_query_must_be_unique() -> None:
    tok = CharTokenizer(DS_SPECIALS)
    fmt = ar.REASONING_FORMATS[DSV31]
    for span in ((-1, 2), (3, 2), (0, 99)):
        with pytest.raises(ValueError, match="pad_query_span"):
            ar.rebuild_sequence("abcdef", "r", "1", tokenizer=tok, template=ds_template(), fmt=fmt,
                                pad_query_span=span)
    twice = ar.ChatTemplate("{{ messages[0]['content'] }}|{{ messages[0]['content'] }}")
    with pytest.raises(ValueError, match="2 times"):
        ar.rebuild_sequence("abcdef", "r", "1", tokenizer=tok, template=twice, fmt=fmt,
                            pad_query_span=(1, 3))
    # Without a span the same template is accepted, as before.
    ar.rebuild_sequence("abcdef", "r", "1", tokenizer=tok, template=twice, fmt=fmt)


def test_rebuild_sequence_shifts_the_span_when_the_template_strips_the_query() -> None:
    """Gemma's template trims the query: a span given in the untrimmed text still hits the same characters."""
    tok = CharTokenizer(GEMMA_SPECIALS)
    fmt = ar.REASONING_FORMATS[GEMMA]
    query = "  head" + "XYZ" + "tail  "
    r = ar.rebuild_sequence(query, "r", "1", tokenizer=tok, template=gemma_template(), fmt=fmt,
                            pad_query_span=(len("  head"), len("  head") + 3))
    pad = [i for i, c in enumerate(r.classes[: len(r.prompt_ids)]) if c == 1]
    assert "".join(tok.decode_tokens([r.prompt_ids[i] for i in pad])) == "XYZ"


# ---------------------------------------------------------------- pull_captures

PULL_PREFIX = "bedrock-trio/attention"
PULL_URI = f"s3://bucket/{PULL_PREFIX}"


class RecordingS3:
    """Wraps a fake client and records every method called on it."""

    def __init__(self, inner: FakeS3) -> None:
        self._inner = inner
        self.calls: list[str] = []

    def __getattr__(self, name: str):
        self.calls.append(name)
        return getattr(self._inner, name)


def _fill_bucket(tmp_path: Path, model_runs: dict[str, str]) -> tuple[FakeS3, Path]:
    """Return a fake bucket holding one verified two-rank capture (q0) per model and its source tree.

    The objects are the bytes ``_mirror_job`` and ``_write_manifest_file`` write, so a pulled
    tree can be compared with ``read_captures`` of the source. ``q0.r<rank>.json`` metas are tiny.
    """
    source = tmp_path / "source"
    s3 = FakeS3()
    for model, run_name in model_runs.items():
        run_dir = source / "induction" / model / "seed=0" / run_name
        _mirror_job(run_dir, 0, [0, 1])
        for rank in (0, 1):
            (run_dir / f"q0.r{rank}.json").write_text(json.dumps({"rank": rank}))
    for path in source.rglob("*"):
        if path.is_file():
            s3.objects[f"{PULL_PREFIX}/{path.relative_to(source).as_posix()}"] = path.read_bytes()
    return s3, source


def _files_below(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_pull_captures_mirrors_what_read_captures_reads(tmp_path: Path) -> None:
    run = f"noise_intens--{STAMP_A}"
    s3, source = _fill_bucket(tmp_path, {GEMMA: run, NEMO: run})
    # Objects that are not captures or manifests: a probe, a stray file, a non-run folder.
    for key in (f"{PULL_PREFIX}/_probe/q0.r0.npz", f"{PULL_PREFIX}/induction/{GEMMA}/_probe/q0.r0.npz",
                f"{PULL_PREFIX}/induction/{GEMMA}/seed=0/{run}/notes.txt",
                f"{PULL_PREFIX}/induction/{GEMMA}/seed=0/q0.r0.npz"):
        s3.objects[key] = b"x"
    mirror = tmp_path / "mirror"
    written = ar.pull_captures(PULL_URI, mirror, [GEMMA], s3_client_factory=lambda: s3)
    expected = {p for p in _files_below(source) if f"induction/{GEMMA}/" in p}
    assert written == len(expected) == 5  # 2 ranks x (npz, json) + one manifest
    assert _files_below(mirror) == expected
    for rel in expected:
        assert (mirror / rel).read_bytes() == (source / rel).read_bytes()
    # The mirror is the ``mirror_root`` of read_captures and reads exactly like the source tree.
    got = ar.read_captures(GEMMA, mirror, config=_MIRROR_CONFIG)
    want = ar.read_captures(GEMMA, source, config=_MIRROR_CONFIG)
    assert got["noise_intens"]["jobs"] == 1
    assert got["noise_intens"]["ratio_mean"] == want["noise_intens"]["ratio_mean"]
    # models=None pulls every model found.
    everything = tmp_path / "all"
    assert ar.pull_captures(PULL_URI, everything, s3_client_factory=lambda: s3) == 10
    assert _files_below(everything) == _files_below(source)


def test_pull_captures_keeps_same_size_files_and_replaces_other_sizes(tmp_path: Path) -> None:
    s3, _source = _fill_bucket(tmp_path, {GEMMA: f"noise_intens--{STAMP_A}"})
    counting = CountingS3()
    counting.objects = s3.objects
    mirror = tmp_path / "mirror"
    assert ar.pull_captures(PULL_URI, mirror, [GEMMA], s3_client_factory=lambda: counting) == 5
    assert len(counting.gets) == 5
    # Second pull: every size matches, so nothing is fetched or written.
    assert ar.pull_captures(PULL_URI, mirror, [GEMMA], s3_client_factory=lambda: counting) == 0
    assert len(counting.gets) == 5
    # A file of another size (here truncated) is replaced; a same-size one is not touched.
    victim = next(mirror.rglob("q0.r1.npz"))
    good = victim.read_bytes()
    victim.write_bytes(good[:10])
    bystander = next(mirror.rglob("q0.r0.npz"))
    bystander.write_bytes(b"\0" * len(bystander.read_bytes()))  # same size, different bytes: kept
    assert ar.pull_captures(PULL_URI, mirror, [GEMMA], s3_client_factory=lambda: counting) == 1
    assert victim.read_bytes() == good and set(bystander.read_bytes()) == {0}
    assert not [p for p in mirror.rglob("*") if p.name.endswith(".part")]


def test_pull_captures_never_leaves_a_partial_file_under_a_final_name(tmp_path: Path) -> None:
    s3, _source = _fill_bucket(tmp_path, {GEMMA: f"noise_intens--{STAMP_A}"})

    class Dies(FakeS3):
        def get_object(self, Bucket: str, Key: str) -> dict:
            if Key.endswith("q0.r1.npz"):
                class Body:
                    def read(self, *_):
                        raise ConnectionError("connection reset")
                return {"Body": Body()}
            return super().get_object(Bucket, Key)

    dying = Dies()
    dying.objects = s3.objects
    mirror = tmp_path / "mirror"
    with pytest.raises(ConnectionError):
        ar.pull_captures(PULL_URI, mirror, [GEMMA], s3_client_factory=lambda: dying)
    left = _files_below(mirror)
    assert not any(name.endswith(".part") for name in left)
    assert not any(name.endswith("q0.r1.npz") for name in left)


def test_pull_captures_only_lists_and_gets_and_follows_every_page(tmp_path: Path) -> None:
    s3, source = _fill_bucket(tmp_path, {GEMMA: f"noise_intens--{STAMP_A}"})
    s3.page_size = 2  # five matching keys over three pages
    recorder = RecordingS3(s3)
    mirror = tmp_path / "mirror"
    assert ar.pull_captures(PULL_URI, mirror, s3_client_factory=lambda: recorder) == 5
    assert s3.list_calls == 3
    assert _files_below(mirror) == _files_below(source)
    assert set(recorder.calls) == {"list_objects_v2", "get_object"}
    assert s3.puts == [] and s3.if_none_match == []


def test_pull_captures_refuses_a_bad_uri_or_model_name(tmp_path: Path) -> None:
    for uri in ("bucket/prefix", "s3://"):
        with pytest.raises(ValueError):
            ar.pull_captures(uri, tmp_path, s3_client_factory=FakeS3)
    for model in ("", "..", "a/b"):
        with pytest.raises(ValueError, match="model name"):
            ar.pull_captures(PULL_URI, tmp_path, [model], s3_client_factory=FakeS3)
