# Induction

This study compares extensional evidence lists with intensional pattern rules.

`noise_intens` pads the intensional prompt to the extensional token count under the tested
model's tokenizer, separating length from representation. `zero` uses an empty context
and omits `$seq_len`, which would reveal the period-1 answer.

## Periodic patterns

A periodic pattern combines labels from rules firing at multiples of each period.

Extensional: "Position 2: fizz. Position 3: buzz. ... Position 6: fizz|buzz."
Intensional: "Every 2 positions write fizz. Every 3 positions write buzz."

Queries ask membership at a position or a count across one period.

The released results hold 16 models, 3 arms (`intens`, `noise_intens`, and `extens`), and
30 seeds. The table leaves out the `zero` arm.

## Reproducing the released results

`iclr.json` records the protocol, model checkpoints, published accuracies, and digests of
the released runs. `repro.py` provides:

```
python -m smolbench.induction.repro fetch --out <results-folder>
python -m smolbench.induction.repro check-data <results-folder>
python -m smolbench.induction.repro report <results-folder>
python -m smolbench.induction.repro models
```

The `fetch` command downloads the public results without credentials. The analysis table
is produced by `notebooks/induction/analysis/induction_results.py`.
