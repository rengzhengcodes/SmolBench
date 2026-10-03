# Induction

This study compares extensional evidence lists with intensional pattern rules.

`noise_intens` pads the intensional prompt to the extensional token count under
the tested model's tokenizer, separating length from representation. `zero`
uses an empty context and omits `$seq_len`, which would reveal the period-1
answer.

Conditions (`intens`, `extens`, `noise_intens`, `zero`) come from
`periodic.CONDITIONS` and remain ordered dictionary keys.

## Periodic patterns

A periodic pattern combines labels from rules firing at multiples of each period.

Extensional: "Position 2: fizz. Position 3: buzz. ... Position 6: fizz|buzz."
Intensional: "Every 2 positions write fizz. Every 3 positions write buzz."

Queries ask membership at a position or a count across one period.

## The experiment API

`smolbench.induction.experiment.InductionExperiment` is the shared harness.
The driver is `notebooks/induction/run_study.py`.

### keys.env first, then import

Load `keys.env` before imports that read `EC2_*`: `ec2` captures them at import.

### Seed conventions

A replicate regenerates the same quiz with a new seed. Shards partition the
seed tuple by `r % count` and need separate EC2 state files and tags.

Each seed drives quiz and decoding randomness. Recreate prompts with
`make_quizzes(seed, model)`; the model controls noise-arm padding.

### Offline vs. billed methods

`summarize()` reads stored marks. Provisioning, running, status, and teardown
use billed EC2 instances.

## Reproducing the ICLR 2027 results

`iclr.json` records the protocol of the submission's runs: the public bucket, seeds,
arms, each model's pinned checkpoint, a SHA-256 digest of each seed's published runs, and
the published accuracies. `repro.py` reads it:

```
python -m smolbench.induction.repro models
python -m smolbench.induction.repro fetch --out <results folder>
python -m smolbench.induction.repro check-data <results folder>
python -m smolbench.induction.repro report <results folder>
```

`fetch` copies an `induction/` prefix (the public one, or your own run's bucket) into a
local folder with the store's key layout. `notebooks/induction/analysis/induction_results.py`
writes the paper table from that folder. The root `README.md` walks through both paths:
from the released results, and from a new run of `notebooks/induction/run_study.py`.
