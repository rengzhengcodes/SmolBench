# Provenance: `encoding_dsv4_vendored.py`

DeepSeek-V4's official chat-encoding module, vendored BYTE-VERBATIM (which
is why this note lives beside the file, not inside it). It is the ground
truth `tests/evals/test_dsv4_chat_template.py` renders the inline serving
template against; never patch it to match the template -- re-vendor from
upstream instead, and check the hash:

```
sha256 bdbd57c132a1b3725042323d02b98b9d1df28e5f388f134399555d041f5055e0  (27908 bytes)
```

identical at both revisions `smolbench/evals/providers/ec2.py` pins
(MIT-licensed):

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/encoding/encoding_dsv4.py
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/encoding/encoding_dsv4.py

No installable substitute exists (checked 2026-08-31): DeepSeek publishes
no package for it, PyPI's `deepseek-tokenizer` is BPE-only, and vLLM's
`vllm/tokenizers/deepseek_v4_encoding.py` is a third-party copy that
tracks newer upstream revisions and would drag the torch/CUDA stack into
an offline test.
