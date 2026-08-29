# Architecture atlas for the family-ladder roster

Builds a published reference page describing what each of the study's 21
checkpoints actually is: how every layer mixes tokens, how every layer encodes
position, where the feed-forward goes sparse.

The study's own record (`smolbench/evals/providers/ec2.py`, `scripts/fleet/run_fleet.py`,
`notebooks/induction/run_study.py`) captures how each checkpoint was *served* —
tensor parallelism, context window, reasoning wiring — but nothing about what
each one *is*. This closes that gap so the results can be read mechanistically.

## Pipeline

```
fetch_arch_facts.py      HF config.json + generation_config.json for all 21 repos
   │                     -> arch_configs_raw.json   (verbatim, the audit trail)
   │                     -> arch_facts.json         (normalised + provenance)
   ▼
build_page_data.py       per-layer tracks, repeating motifs, rotary fractions,
   │                     merged with the prose in annotations*.json
   │                     -> page_data.json
   ▼
build_page.py            injects page_data.json into page_template.html
                         -> model_architectures.html   (the published artifact)
```

`build_page.py` re-runs `build_page_data.py` itself, so one command rebuilds
everything:

```bash
.venv/bin/python scripts/arch/build_page.py
```

## Where each claim comes from

**Structural numbers** — layer counts, head counts and dimensions, RoPE bases
and scaling parameters, expert counts, window sizes, SSM state sizes, vocab
sizes — are read from each checkpoint's own `config.json`, fetched from the
exact repo the fleet served, and stamped with that repo's resolved commit SHA.
Nothing structural is transcribed by hand.

**Prose** — what a mechanism is called, when a checkpoint was released, how
many parameters it has, and which config fields the reference implementation
actually reads — cannot come from a config file. It lives in
`annotations_models.json`, written from the seven family research briefs in
`research/`, which cite their sources and label claims verified / inferred /
unverified.

The split is deliberate: `annotations.json` holds the page's own copy
(masthead, legend, method) and `annotations_models.json` holds the per-model
prose, so regenerating one can never clobber the other.

Where the two layers disagree, the config wins and the disagreement is shown on
the page as a flag rather than being smoothed over. A few annotations
deliberately *override* a config-derived value — Nemotron-3 and EXAONE both
declare RoPE fields their implementations ignore — and each override is stated
in that model's prose.

## Checks

```bash
.venv/bin/python scripts/arch/fetch_arch_facts.py --check   # configs vs the fleet's fixture
.venv/bin/python scripts/arch/check_annotations.py          # field coverage + SVG length limits
node scripts/arch/render_check.mjs                          # runs the page's renderer headless
```

`--check` compares the fetched configs against
`tests/fixtures/roster_configs.json`, the fixture `tests/evals/test_deploy_specs.py`
pins against, on the four fields both hold; a mismatch means an upstream
checkpoint moved under the study.

`check_annotations.py` enforces the character limits that keep annotation text
inside its fixed-width SVG boxes — those strings do not wrap, they overrun.

`render_check.mjs` executes the page's own renderer against a `document` stub
and asserts every region is populated. The page builds its DOM at runtime, so a
renderer fault produces a blank section rather than a build error; nothing else
in the pipeline would catch it.

## Colour

Four categorical hues carry meaning in the diagrams (softmax attention, gated
linear attention, Mamba-2, mixture-of-experts). They were validated with the
`dataviz` skill's palette validator for colour-vision separation and surface
contrast against both the light and dark page surfaces. Every coloured cell
also carries its meaning in text, so nothing on the page depends on hue alone.

## Built outputs are not tracked (since 2026-08-25)

`page_data.json` and `model_architectures.html` were removed from the tree and
archived on PR #4 (see `notebooks/README.md`). Run
`.venv/bin/python scripts/arch/build_page.py` before `check_annotations.py` or
`render_check.mjs`; both read the built files.
