# Induction

We define induction operationally: induction is information derived from
empirical evidence. Propositions must fit the empirical evidence. Any
change in the evidence forces a change in the model. The model does not
control the observables; the observables control the model.

The full enumerative list of empirical evidence is the extensional
representation. The pattern-fitted version is the intensional
representation. Our hypothesis: both representations carry positive
information, but the extensional representation usually needs more
tokens, and that extra length degrades performance relative to the
intensional representation.

The benchmark below follows that format: an extensional representation
compacts into a shorter intensional representation. For induction, every
intensional representation supervenes on its extensional representation.
A change in the extensional representation can, by necessity, change the
intensional representation.

## Periodic patterns

A periodic pattern is a set of overlapping harmonics: the k-th rule
fires at every multiple of its period, and each position's label is the
concatenation of every rule that fires there — a generalized FizzBuzz
(`smolbench/induction/periodic.py`).

The extensional representation enumerates the sequence position by
position: "Position 2: fizz. Position 3: buzz. ... Position 6:
fizz|buzz." The intensional representation states the rules: "Every 2
positions write fizz. Every 3 positions write buzz." If the sequence
had differed at any position, the rule set that fits it would have to
change too.

A query asks either whether a label appears at a given position
(True/False) or how many positions across one full period contain it
(an integer). This is not a classical needle-in-a-haystack problem: a
count query spans the whole sequence, and a membership query at a
position where nothing fires exercises the complement of every rule.
Both representations are positive-utility information for either query,
but the intensional one needs fewer tokens.

## The experiment API

`smolbench.induction.experiment.InductionExperiment` is the one shared
harness for induction evals. A driver constructs the experiment once
and then calls its methods in lifecycle order: `provision()` once,
`run(model, ...)` once per model section, `summarize(model)` /
`cot_chain_lengths()` any number of times, and `teardown()` once at the
end.

The live driver is `notebooks/induction/run_study.py`, with its sibling
notebook `notebooks/induction/induction_eval.ipynb`.

### keys.env first, then import

Load `keys.env` (via `load_dotenv`) before you import anything that
reads `EC2_*` provisioning config. This is not stylistic.
`smolbench.evals.providers.ec2` captures its provisioning constants
(`EC2_EXPERIMENT_TAG`, `EC2_INSTANCE_TYPES`, `EC2_S3_MODEL_CACHE`, ...)
once at IMPORT time as ordinary module attributes; it does not re-read
them per call. An import that runs ahead of `load_dotenv` silently
freezes them to their un-overridden defaults for the rest of the
process. For this reason `smolbench.induction.experiment` never imports
`smolbench.evals.providers.ec2` at module scope: every `InductionExperiment`
method that needs the EC2 lifecycle (`provision`, `run`,
`agent_status`, `teardown`) imports it lazily, inside the method body.
A driver that imports `smolbench.induction.experiment` ahead of its
`load_dotenv` call still gets the override. See that module's docstring
(its closing "CRITICAL" paragraph) for the full contract.

### Seed conventions

A "replicate" is the SAME quiz regenerated under a fresh seed, not a
different quiz. `InductionExperiment.seeds` is always
`tuple(base_seed + r for r in range(n_replicates))`. The constructor's
default is `base_seed=1776` (the July 4th, 1776 nod). The current
family-ladder study deliberately overrides this:
`notebooks/induction/run_study.py` locks `BASE_SEED=0` (seeds 0..29) -- see
its docstring for why. One seed
does double duty: it drives the quiz's OWN randomness (label and query
sampling — see `PeriodicConfig.seed`) AND, in the same call, threads through
as the per-request decoding seed. This makes a replicate's on-disk
artifact (`rep_{seed}.yaml`) fully reproducible from its filename
alone. Regenerate `make_quizzes(seed, model)` (the model matters: the
noise arm pads under that model's own tokenizer) and you get
byte-identical prompts, and the filename's seed is exactly the decoding
seed used against them.

### Offline vs. billed methods

`InductionExperiment.summarize(model)` and `.cot_chain_lengths()` only
read stored marks back through the results store (`ReplicateHarness`'s
`self.store`). They spend no EC2 or inference cost, so you can call them
any number of times -- but against an S3-backed store
(`SMOLBENCH_RESULTS_S3`) the reads are S3 requests, not local disk.
`.provision()`, `.run(model, ...)`,
`.agent_status()`, and `.teardown()` are LIVE AWS calls against a
self-provisioned EC2 spot instance, billed for the duration it is up.
See `smolbench/evals/providers/ec2.py` for the current per-hour rate and the
idle-watchdog / max-lifetime safety nets that cover an abandoned
driver.

### Figures

`smolbench/induction/figures.py` (`accuracy`, `load_condition_accuracies`,
`plot_archetype_accuracy`) reads the FLAT, single-run result layout -- not
the per-replicate `results/<tag>/rep_<seed>.yaml` tree `InductionExperiment`
writes. Matplotlib imports lazily inside `plot_archetype_accuracy` only, so
importing `figures.py` (or the rest of `smolbench.induction`) does not
require the `notebook` extra.
