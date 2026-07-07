# Induction

The current operational definition of induction is information derived from empirical evidence. In induction,  propositions that have to fit empirical evidence and any change in empirical evidence necessitates the model change (i.e., the model does not control the observables, but the observables control the model). The full enumerative list of empirical evidence is called the extensional representation. The pattern-fitted version is called the intensional representation. Our hypothesis is that while extensional and intensional representations both represent positive information, the fact that extensional representations usually require more tokens leads to performance degradation compared to intensional representations.

The following are a non-exhaustive list of types of induction, which all follow the same format: extensional representations are compacted into shorter intensional representations. Note that, for induction, all intensional representations supervene on extensional representations and that changes in the extensional representation by necessity can change the intensional representation.

## Chromatic Intervals

Chromatic intervals are examples where an interval has a certain "color" and whatever color is contained in the interval leads to certain properties. For example, the terms of presidencies are chromatic intervals, where the president is the color, the intervals are on time, and the additional properties are how one conducts the duties of the presidency.

The extensional representation for presidencies is "George Washington was President Apr. 30 1789, May 1 1789, May 2 1789,... and Mar. 4 1797." The intensional representation is "George Washington was President between Apr. 30 1789 and Mar. 4 1797." Note that if George Washington's presidency had for some reason changed (e.g., if he sought a third term, retired early, been temporarily incapacitated, etc.) the extensional representation changes which induces a change in the intensional representation.

A query on a chromatic interval always involves the form "was the interval [color] from [start, end]." For example, "could George Washington have signed the Judiciary Act of 1789" involves querying "was the presidency 'George Washington' from [Sep. 24 1789, Sep. 24 1789]."

The above distinguishes itself from classical needle-in-a-haystack (NIAH) problems because the queries are not necessarily limited to just one date but can encompass multiple dates. For example, the query "could George Washington have signed a bill on Jan. 1 1800" requires taking the complement of all of time and the time George Washington was President. In that case, both intensional and extensional representations are positive utility information but the intensional representation has less tokens that need to be processed.

## Running the notebook experiments

Each of the three eval notebooks —
`notebooks/periodic/induction_eval.ipynb`,
`notebooks/chromatic/induction_eval.ipynb`, and
`notebooks/chromatic/induction_eval_one_hop.ipynb` — builds one
`smolbench.induction.experiment.InductionExperiment` instead of hand-rolling
the harness/EC2-provisioning/serve-loop cells that used to be copy-pasted
(and had begun to drift) across all three. A notebook cell reduces to
constructing the experiment and then calling its methods in lifecycle
order: `EXPERIMENT.provision()` once, `EXPERIMENT.run(model, ...)` once per
archetype section, `EXPERIMENT.summarize(model)` / `.cot_chain_lengths()`
any number of times, `EXPERIMENT.teardown()` once at the end.

The three notebooks' constructors differ only in `notebook_dir`,
`state_file`, and `prefix` — everything else (`archetype_tags`,
`make_quizzes`, `n_replicates=30`, `base_seed=BASE_SEED`) is
experiment-specific config the notebook already computes above the cell:

| Notebook | `notebook_dir` | `state_file` | `prefix` |
|---|---|---|---|
| `periodic/induction_eval.ipynb` | `"periodic"` | (default — `ec2.py`'s own `.ec2_state.json` at the repo root) | (none) |
| `chromatic/induction_eval.ipynb` | `"chromatic"` | `".ec2_state_chromatic.json"` | (none) |
| `chromatic/induction_eval_one_hop.ipynb` | `"chromatic"` | `".ec2_state_chromatic.json"` | `"one_hop_"` |

The one-hop notebook shares both its EC2 state file AND its `results/`
directory with the sibling chromatic notebook (same `notebook_dir`); the
`prefix` is what keeps their replicate directories from colliding
(`results/one_hop_{tag}_{info}/` vs. `results/{tag}_{info}/}`) — see
`smolbench/evals/replicates.py`'s `ReplicateHarness.prefix`.

### keys.env first, then import

Every notebook's first cell calls `load_dotenv(Path.cwd() / "keys.env")`
*before* importing anything that reads `EC2_*` provisioning config.
This is not stylistic: `smolbench.evals.ec2`'s provisioning constants
(`EC2_EXPERIMENT_TAG`, `EC2_INSTANCE_TYPES`, `EC2_S3_MODEL_CACHE`, ...) are
captured once at IMPORT time as ordinary module attributes (so notebooks
can read them back as `ec2.EC2_EXPERIMENT_TAG`), not re-read per call — an
import that runs ahead of `load_dotenv` silently freezes them to their
un-overridden defaults for the rest of the kernel's life. Accordingly,
`smolbench.induction.experiment` never imports `smolbench.evals.ec2` at
module scope either: every `InductionExperiment` method that needs the EC2
lifecycle (`provision`, `run`, `agent_status`, `teardown`) imports it
lazily, inside the method body, so a notebook that does
`import smolbench.induction.experiment` ahead of its `load_dotenv` call (a
perfectly ordinary cell order) still gets the override. See that module's
docstring (the "CRITICAL: no `smolbench.evals.ec2` import at module scope"
section) for the full contract.

### Seed conventions

A "replicate" is the SAME quiz regenerated under a fresh seed, not a
different quiz. `InductionExperiment.seeds` is always
`tuple(base_seed + r for r in range(n_replicates))`; every notebook to date
uses `base_seed=1776` (the July 4th, 1776 nod) and `n_replicates=30`, so
replicate `r`'s seed is `1776 + r`. That one seed does double duty: it
drives the quiz's OWN randomness (label/interval/color sampling — see
`PeriodicConfig.seed` / `ChromaticIntervalsConfig.seed`) AND, in the same
call, is threaded through as the per-request decoding seed. This is what
makes a replicate's on-disk artifact (`rep_{seed}.yaml`) fully reproducible
from its filename alone — regenerating `make_quizzes(seed)` reproduces
byte-identical prompts, and the filename's seed is exactly the decoding
seed that was used against them.

### Offline vs. billed methods

`InductionExperiment.summarize(model)` and `.cot_chain_lengths()` only read
cached YAML off disk — no AWS or network calls, safe to call any number of
times. `.provision()`, `.run(model, ...)`, `.agent_status()`, and
`.teardown()` are LIVE AWS calls against a self-provisioned EC2 spot
instance billed for the duration it is up (see `smolbench/evals/ec2.py`
for the current per-hour rate and the idle-watchdog/max-lifetime safety
nets that cover an abandoned notebook).

### Figures and the analysis notebook

`smolbench/induction/figures.py` (`accuracy`, `load_condition_accuracies`,
`plot_archetype_accuracy`) backs
`notebooks/chromatic/induction_eval_analysis.ipynb`, which is a PINNED
HISTORICAL figure over the archived `result2/` pilot directory (flat,
single-run result files — not the per-replicate `results/<tag>/rep_<seed>.yaml`
tree the current `InductionExperiment`-driven notebooks write). Matplotlib
is imported lazily inside `plot_archetype_accuracy` only, so importing
`figures.py` (or the rest of `smolbench.induction`) does not require the
`notebook` extra.