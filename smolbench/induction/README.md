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

The types of induction below all follow the same format: an extensional
representation compacts into a shorter intensional representation. For
induction, every intensional representation supervenes on its
extensional representation. A change in the extensional representation
can, by necessity, change the intensional representation.

## Chromatic intervals

A chromatic interval is an interval that has a "color", and the color of
an interval gives it certain properties. Presidency terms are an
example. The president is the color, the intervals lie on time, and the
extra properties are how the office holder conducts the duties of the
presidency.

The extensional representation for a presidency is "George Washington
was President Apr. 30 1789, May 1 1789, May 2 1789, ... and Mar. 4
1797." The intensional representation is "George Washington was
President between Apr. 30 1789 and Mar. 4 1797." If the presidency had
changed (a third term, an early retirement, a temporary incapacity),
the extensional representation would change, and that change would
induce a change in the intensional representation.

A query on a chromatic interval always has the form "was the interval
[color] from [start, end]." For example, "could George Washington have
signed the Judiciary Act of 1789" queries "was the presidency 'George
Washington' from [Sep. 24 1789, Sep. 24 1789]."

This is not a classical needle-in-a-haystack (NIAH) problem. A query is
not limited to one date; it can span many dates. The query "could
George Washington have signed a bill on Jan. 1 1800" takes the
complement of the presidency interval over all of time. Both
representations are positive-utility information there, but the
intensional one needs fewer tokens.

## The experiment API

`smolbench.induction.experiment.InductionExperiment` is the one shared
harness for induction evals. A driver constructs the experiment once
and then calls its methods in lifecycle order: `provision()` once,
`run(model, ...)` once per model section, `summarize(model)` /
`cot_chain_lengths()` any number of times, and `teardown()` once at the
end.

The live driver is `notebooks/induction/run_study.py` (with its sibling
notebook `notebooks/induction/induction_eval.ipynb`). The three retired
Jupyter notebooks that this API was extracted for
(`periodic/induction_eval.ipynb`, `chromatic/induction_eval.ipynb`, and
`chromatic/induction_eval_one_hop.ipynb`) now live only in the archive
zip and the git history. `smolbench/evals/replicates.py` keeps the
record of why the shared harness exists: the three notebooks used to
copy-paste these cells, and the copies had begun to drift.

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
(the "CRITICAL: no `smolbench.evals.providers.ec2` import at module scope"
section) for the full contract.

### Seed conventions

A "replicate" is the SAME quiz regenerated under a fresh seed, not a
different quiz. `InductionExperiment.seeds` is always
`tuple(base_seed + r for r in range(n_replicates))`. The constructor's
default is `base_seed=1776` (the July 4th, 1776 nod), which every
retired notebook used with `n_replicates=30`. The current family-ladder
study deliberately overrides this: `notebooks/induction/run_study.py`
locks `BASE_SEED=0` (seeds 0..29) — see its docstring for why. One seed
does double duty: it drives the quiz's OWN randomness (label, interval,
and color sampling — see `PeriodicConfig.seed` /
`ChromaticIntervalsConfig.seed`) AND, in the same call, threads through
as the per-request decoding seed. This makes a replicate's on-disk
artifact (`rep_{seed}.yaml`) fully reproducible from its filename
alone. Regenerate `make_quizzes(seed, model)` (the model matters: the
noise arm pads under that model's own tokenizer) and you get
byte-identical prompts, and the filename's seed is exactly the decoding
seed used against them.

### Offline vs. billed methods

`InductionExperiment.summarize(model)` and `.cot_chain_lengths()` only
read cached YAML off disk. They make no AWS or network calls, so you
can call them any number of times. `.provision()`, `.run(model, ...)`,
`.agent_status()`, and `.teardown()` are LIVE AWS calls against a
self-provisioned EC2 spot instance, billed for the duration it is up.
See `smolbench/evals/providers/ec2.py` for the current per-hour rate and the
idle-watchdog / max-lifetime safety nets that cover an abandoned
driver.

### Figures and the analysis notebook

`smolbench/induction/figures.py` (`accuracy`,
`load_condition_accuracies`, `plot_archetype_accuracy`) was extracted
from `induction_eval_analysis.ipynb`, a PINNED HISTORICAL figure over
the archived `result2/` pilot directory (flat, single-run result files
— not the per-replicate `results/<tag>/rep_<seed>.yaml` tree that
`InductionExperiment` writes). That notebook is retired to the archive
zip with the rest of the old trees. Matplotlib imports lazily inside
`plot_archetype_accuracy` only, so an import of `figures.py` (or the
rest of `smolbench.induction`) does not require the `notebook` extra.
