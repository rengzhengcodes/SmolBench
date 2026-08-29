# Architecture facts for the family-ladder roster

Records what each of the study's 21 checkpoints actually is: how every layer
mixes tokens, how every layer encodes position, where the feed-forward goes
sparse — read from each checkpoint's own `config.json`.

The study's own record (`smolbench/evals/providers/ec2.py`, `scripts/fleet/run_fleet.py`,
`notebooks/induction/run_study.py`) captures how each checkpoint was *served* —
tensor parallelism, context window, reasoning wiring — but nothing about what
each one *is*. This closes that gap so the results can be read mechanistically.

## Contents

```
fetch_arch_facts.py      HF config.json + generation_config.json for all 21 repos
                         -> arch_configs_raw.json   (verbatim, the audit trail)
                         -> arch_facts.json         (normalised + provenance)

kv_budget.py             corrected KV-cache sizing for the roster, over
                         arch_configs_raw.json (2026-08-13 fleet audit)

research/                seven family research briefs; every claim cited and
                         labelled verified / inferred / unverified
```

`arch_configs_raw.json` is tracked: it is the audit trail `kv_budget.py` and
`tests/tooling/test_kv_budget.py` read, and the archived config record
`smolbench/evals/providers/ec2.py` cites. `arch_facts.json` is not tracked; regenerate it
with `fetch_arch_facts.py` (needs network).

## Where each claim comes from

**Structural numbers** — layer counts, head counts and dimensions, RoPE bases
and scaling parameters, expert counts, window sizes, SSM state sizes, vocab
sizes — are read from each checkpoint's own `config.json`, fetched from the
exact repo the fleet served, and stamped with that repo's resolved commit SHA.
Nothing structural is transcribed by hand.

**Prose** — what a mechanism is called, when a checkpoint was released, how
many parameters it has, and which config fields the reference implementation
actually reads — cannot come from a config file. It lives in the family
research briefs in `research/`, which cite their sources.

Where the two layers disagree, the config wins. Nemotron-3 and EXAONE both
declare RoPE fields their implementations ignore; each such divergence is
stated in that family's brief.

## Checks

```bash
.venv/bin/python scripts/arch/fetch_arch_facts.py --check   # configs vs the fleet's fixture
.venv/bin/python -m pytest tests/tooling/test_kv_budget.py  # KV formulas vs the audit table
```

`--check` compares the fetched configs against
`tests/fixtures/roster_configs.json`, the fixture `tests/evals/test_deploy_specs.py`
pins against, on the four fields both hold; a mismatch means an upstream
checkpoint moved under the study.

## Removed: the atlas page builder (2026-08-29)

This directory also held a pipeline that rendered these facts into a published
HTML page (`build_page.py`, `build_page_data.py`, `page_template.html`,
`annotations*.json`, `check_annotations.py`, `render_check.mjs`). The page was
a presentation artifact rather than study tooling, and it was removed from the
tree. Its two built outputs had already been archived on PR #4 on 2026-08-25.
