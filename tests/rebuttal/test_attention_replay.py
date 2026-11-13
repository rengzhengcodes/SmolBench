"""Offline tests of the Bedrock-transcript attention replay driver (``rebuttal/attention_replay.py``).

No AWS, no GPU, no network: S3 is a dict fake, the box is a fake that uploads through the
minted presigned URLs, tokenizers are the real cached ``tokenizer.json`` files when present
(``HF_HUB_OFFLINE``) and a character-level stub otherwise. Chat templates are not cached for
any of the three checkpoints, so the real-template tests skip unless they are.
"""
from __future__ import annotations

import io
import json
import re
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
    assert not plan.capture_supported and plan.unsupported_reason
    assert plan.est_basis.startswith("ESTIMATE:")
    expected = 0
    tp = plan.tp_estimate
    for n_tokens, n_completion in ((10, 4), (12, 4), (90, 3)):
        expected += 61 * n_completion * 128 * 6 * 2 + tp * n_tokens
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

    def __init__(self, s3: FakeS3, tp: int = 2, fail_attn: bool = False) -> None:
        self.s3, self.tp, self.fail_attn = s3, tp, fail_attn
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
                mass[..., 0], mass[..., 3] = 0.5, 0.5
                buf = io.BytesIO()
                np.savez(buf, mass=mass, entropy=np.ones((2, p, 2), np.float16),
                         sink=np.zeros((2, p, 2), np.float16),
                         classes=np.asarray(line["classes"], np.uint8),
                         query_start=np.asarray(qs, np.int32), layers=np.arange(2, dtype=np.int32),
                         positions=np.asarray(line["positions"], np.int32))
                blob = buf.getvalue()
                key = line["put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                meta_key = line["meta_put_urls"][rank].split("signed/", 1)[1].split("?", 1)[0]
                self.s3.put_object(Bucket="b", Key=key, Body=blob)
                self.s3.put_object(Bucket="b", Key=meta_key, Body=json.dumps(
                    {"n_tokens": n, "bytes": len(blob), "mode": "mass", "query_start": qs,
                     "gate_max_rel": 0.001, "gate_tol": 0.03, "rank": rank}).encode())
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
    _write_results(tmp_path, DSV31)
    box = AuditedBox(FakeS3())
    with pytest.raises(ar.CaptureUnsupported):
        ar.replay_model(DSV31, tmp_path, approved=True, ec2=box,
                        s3_client_factory=lambda: (_ for _ in ()).throw(AssertionError("S3")),
                        **_plan_kwargs(CharTokenizer(DS_SPECIALS)))
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
    out = ar.read_captures(GEMMA, root)
    assert set(out) == {"noise_intens"}
    summary = out["noise_intens"]
    assert summary["jobs"] == 1
    assert summary["ratio_layer_head"].shape == (3, 4)
    assert summary["ratio_mean"] == pytest.approx(1.0, abs=2e-3)
