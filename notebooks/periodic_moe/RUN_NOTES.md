# periodic_moe run notes

Provenance for the all-MoE induction study. `keys.env` is gitignored (it holds
secrets), so anything about the serving stack that matters for interpreting
results has to be recorded here instead.

## vLLM image: a moving tag

`keys.env` sets `EC2_VLLM_IMAGE=vllm/vllm-openai:nightly`. That tag was needed
because the 2026 architectures in this trio (Qwen3.5 hybrid Gated-DeltaNet +
MoE, Nemotron-3, gpt-oss harmony) predate any stable vLLM release that serves
them.

`nightly` **moves**. Runs of this study are therefore NOT automatically served
by the same build, and the tag alone does not record which one was used. What
is known:

| arm | collected | `nightly` digest |
|---|---|---|
| `intens`, `extens`, `zero` (R=30) | 2026-07-19 | not recorded at the time; the tag has moved many times since |
| `noise_intens` (R=30) | 2026-08-03 | `sha256:b9104b7ef3048e42f79fba9ab5da06e5aff8164aca9968692ec2f569aaaf34c6` (pushed 2026-08-03T06:17:04Z, also published as `nightly-5e35a6f4f9bbc217c599692157ca985c894373f7`) |

So the `noise_intens` arm is served by a **different build** than the arms it
is compared against. Prompts are byte-identical across arms (proved by
`scripts/verify_study_drivers.py`, which diffs regenerated prompts against the
ones recorded inside the replicate YAMLs) and decoding is seeded, so this is a
caveat to report rather than a confound that invalidates the comparison — but
it should be stated in any writeup of the noise contrast.

### Why the image is not pinned in `keys.env`

Pinning was attempted (`vllm/vllm-openai@sha256:b9104b7e...`) and reverted: the
EC2 **user-data has a hard 16 KB limit**, and the rendered payload sits about
49 bytes below it. A digest reference adds 63 bytes, which overflowed the cap —
`smolbench/evals/payloads/__init__.py:166` asserted at 16,398 bytes and the run
aborted before provisioning anything. The shortest pinned form vLLM publishes
(`nightly-<40-char-sha>`, +41 bytes) would fit with roughly 8 bytes to spare,
which is too tight to rely on.

Pinning this properly needs the user-data payload to be slimmed first — see
`smolbench/evals/payloads/` and the budget canary in
`tests/test_ec2_payloads.py`. Until then, record the digest here per run:

```bash
curl -s https://hub.docker.com/v2/repositories/vllm/vllm-openai/tags/nightly \
  | python -c "import json,sys; d=json.load(sys.stdin); print(d['digest'], d['last_updated'])"
```

## Noise arm re-collection (2026-08-03)

The `noise_intens` arm was re-collected after the length control was rebuilt:
it now pads with whitespace to an exact TOKEN count under each model's own
tokenizer, where it previously padded with random characters to a matched
CHARACTER count and consequently ran ~1.6x the extensional arm's token length.
New noise numbers are **not comparable** to any noise figure in the committed
`figures/accuracy_bars.png` or in `DEDUCTION_RESULTS.md`-era notes; those
describe the old, confounded control.
