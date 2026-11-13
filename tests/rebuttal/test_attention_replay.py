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
                # The meta json the plugin writes, with the fields the content audit checks.
                self.s3.put_object(Bucket="b", Key=meta_key, Body=json.dumps(
                    {"job_id": line["job_id"], "rank": rank, "tp": payload["tp"],
                     "model": payload["served_model_name"], "n_tokens": n, "bytes": len(blob),
                     "mode": "mass", "query_start": qs, "layers": [0, 1], "num_heads_local": 2,
                     "rows_shape": [2, p, 2, 4], "gate_max_rel": 0.001, "gate_tol": 0.03}).encode())
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

#: Config of the mirror fixtures: 3 attention layers, 4 heads (2 ranks x 2 local heads).
_MIRROR_CONFIG = {"num_hidden_layers": 3, "num_attention_heads": 4}


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
    out = ar.read_captures(GEMMA, root, config=_MIRROR_CONFIG)
    assert set(out) == {"noise_intens"}
    summary = out["noise_intens"]
    assert summary["jobs"] == 1
    assert summary["ratio_layer_head"].shape == (3, 4)
    assert summary["ratio_mean"] == pytest.approx(1.0, abs=2e-3)


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


def _store_capture(s3, job, tp=2, *, layers=2, heads=4, model=GEMMA, meta_over=None, entropy=None):
    """Store one job's per-rank objects as the plugin writes them; ``meta_over[rank]`` edits a meta."""
    p = job.n_tokens - int(job.query_start)
    local = heads // tp
    for rank in range(tp):
        mass = np.zeros((layers, p, local, 4), np.float16)
        mass[..., 0], mass[..., 3] = 0.5, 0.5
        ent = np.full((layers, p, local), 0.5, np.float16) if entropy is None else entropy
        buf = io.BytesIO()
        np.savez(buf, mass=mass, entropy=ent.astype(np.float16), sink=np.zeros((layers, p, local), np.float16),
                 classes=np.asarray(job.classes, np.uint8), query_start=np.asarray(job.query_start, np.int32),
                 layers=np.arange(layers, dtype=np.int32), has_sink=np.zeros(layers, bool),
                 sliding_window=np.zeros(layers, np.int32), positions=np.asarray([job.n_tokens - 1], np.int32))
        blob = buf.getvalue()
        meta = {"job_id": job.job_id, "rank": rank, "tp": tp, "model": model, "n_tokens": job.n_tokens,
                "query_start": job.query_start, "mode": "mass", "layers": list(range(layers)),
                "num_heads_local": local, "rows_shape": [layers, p, local, 4],
                "gate_max_rel": 0.001, "gate_tol": 0.03, "bytes": len(blob)}
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


def test_the_audit_refuses_an_unknown_arrays_mode(tmp_path) -> None:
    with pytest.raises(ValueError):
        _audit(FakeS3(), [], arrays="some")


# ------------------------------------------------------------ offline reader: rank sets, runs

def _mirror_job(run_dir: Path, idx: int, ranks, *, local_heads=2, pad_scale=1.0) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    classes = np.asarray([2, 0, 1, 1, 1, 1, 0, 3, 3], np.uint8)  # 4 pads, query_start 7
    for rank in ranks:
        mass = np.zeros((3, 2, local_heads, 4), np.float32)
        mass[..., 1] = np.asarray([[4 / 8], [4 / 9]]) * pad_scale
        mass[..., 0] = 1 - mass[..., 1]
        np.savez(run_dir / f"q{idx}.r{rank}.npz", mass=mass.astype(np.float16),
                 entropy=np.zeros((3, 2, local_heads), np.float16),
                 sink=np.zeros((3, 2, local_heads), np.float16), classes=classes,
                 query_start=np.asarray(7, np.int32), layers=np.arange(3, dtype=np.int32),
                 positions=np.asarray([8], np.int32))


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


# ------------------------------------------------------------ shutdown and manifests

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
