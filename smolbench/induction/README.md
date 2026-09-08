# Induction

Induction here is operational: information derived from empirical evidence,
where any change in the evidence forces a change in the model. The enumerative
list of the evidence is the EXTENSIONAL representation; the pattern-fitted
version is the INTENSIONAL one. Hypothesis: both carry positive information,
but the extensional representation needs more tokens, and that extra length
degrades performance.

Two control arms separate the confounds. `noise_intens` is the intensional
prompt whitespace-padded to exactly the extensional prompt's token count under
the model-under-test's own tokenizer (`_common.py`), so a gap cannot be
explained by prompt length alone. `zero` is the same query with an empty
context AND a range-free question (no `$seq_len`) -- the chance floor. The
range must be omitted there specifically: on the default 1..n harmonic set the
period-1 harmonic's answer IS `seq_len`, so "positions 1 through $seq_len"
would hand that one answer away for free in the arm meant to measure what a
model reaches with no positive information at all.

All four conditions (`intens`, `extens`, `noise_intens`, `zero`) are declared
once as `periodic.CONDITIONS`; the quiz builders return a `dict` keyed by
condition name in that order, not a positional tuple.

## Periodic patterns

A periodic pattern is a set of overlapping harmonics: the k-th rule fires at
every multiple of its period, and each position's label is the concatenation
of every rule that fires there -- a generalized FizzBuzz (`periodic.py`).

Extensional: "Position 2: fizz. Position 3: buzz. ... Position 6: fizz|buzz."
Intensional: "Every 2 positions write fizz. Every 3 positions write buzz."

A query asks whether a label appears at a given position (True/False) or how
many positions across one full period contain it (an integer). Neither is a
needle in a haystack: a count query spans the whole sequence, and a membership
query where nothing fires exercises the complement of every rule.

## The experiment API

`smolbench.induction.experiment.InductionExperiment` is the one shared harness,
called in lifecycle order: `provision()` once, `run(model, ...)` once per model
section, `summarize(model)` / `cot_chain_lengths()` any number of times,
`teardown()` once. The live driver is `notebooks/induction/run_study.py`,
beside its notebook `notebooks/induction/induction_eval.ipynb`.

### keys.env first, then import

Load `keys.env` (via `load_dotenv`) before importing anything that reads
`EC2_*` config. `smolbench.evals.providers.ec2` captures those constants at
IMPORT time and never re-reads them, so an import ahead of `load_dotenv`
silently freezes them to their un-overridden defaults. `experiment.py` keeps
its `ec2` imports lazy for that reason (its docstring has the contract), so a
driver that imports the experiment before `load_dotenv` still gets overrides.

### Seed conventions

A "replicate" is the SAME quiz regenerated under a fresh seed, not a different
quiz. Unsharded, `InductionExperiment.seeds` is `tuple(base_seed + r for r in
range(n_replicates))`. Under `shard=(index, count)` it STRIDES that tuple,
keeping replicates with `r % count == index`, so N shards partition one seed
set without overlap (`shard=(1, 4)`, `base_seed=0`, `n_replicates=30` gives 1,
5, 9, ... 29); a shard also needs its own EC2 state file and experiment tag.
The constructor default is `base_seed=1776`; the family-ladder study overrides
it to `BASE_SEED=0` (seeds 0..29).

One seed does double duty: the quiz's own randomness (`PeriodicConfig.seed`)
and the per-request decoding seed. How much the former covers depends on the
generator -- `numeric_count_query_gen` (what the live study wires) seeds the
LABELS only and ignores `seed` otherwise, since its query set is one query per
label in ascending-period order; `tof_membership_query_gen` seeds labels AND
query sampling, drawing up to `MAX_QUERIES_PER_POLARITY` True and False queries
without replacement. Either way a replicate's artifact is reproducible from its
filename alone: re-run `make_quizzes(seed, model)` (the model matters -- the
noise arm pads under that model's tokenizer) for byte-identical prompts.

### Offline vs. billed methods

`summarize(model)` and `.cot_chain_lengths()` only read stored marks back, so
they cost nothing beyond S3 requests against an S3-backed store. `.provision()`,
`.run(model, ...)`, `.agent_status()` and `.teardown()` are live AWS calls
against a self-provisioned EC2 spot instance, billed while it is up;
`smolbench/evals/providers/ec2.py` carries the per-hour rate and the
idle-watchdog / max-lifetime safety nets.
