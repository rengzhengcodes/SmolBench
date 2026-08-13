"""Headless driver for the FAMILY-LADDER SCALING induction study.

WHAT THIS STUDY IS
-------------------
Every prior induction study (``periodic``, ``chromatic``, ``periodic_moe``,
``periodic_coprime``, ``periodic_divisor``) held the MODEL fixed (one small
trio) and varied the QUIZ (sequence length, rule count, noise). This study
inverts that: the quiz is the plain ``periodic_moe`` baseline (``n=9``
harmonics, unmodified), held fixed, and what varies is the MODEL --
7 vendor families x 3 rungs each (smallest / geometric-middle / largest
checkpoint on that family's public ladder) = 21 checkpoints:

    Qwen3.5 (Alibaba, CN)        27B / 122B-A10B / 397B-A17B (FP8)
    Nemotron-3 (NVIDIA, US)      Nano-4B / Nano-30B-A3B / Super-120B-A12B
    Gemma-4 (Google, US)         E2B / 12B / 31B
    GLM-4.x (Zhipu/Z.ai, CN)     4.7-Flash / 4.5-Air / 4.7 (cross-generation)
    Ministral-3 (Mistral, FR)    3B / 8B / 14B
    EXAONE (LG AI Research, KR)  4.0-32B / 4.5-33B / K-EXAONE-236B-A23B (x-gen)
    DeepSeek (CN)                V4-Flash / V3.1 / V4-Pro (cross-generation)

The point of holding the quiz fixed is to read accuracy as a function of
PARAMETER COUNT WITHIN a vendor family and then compare the shape of that
curve ACROSS families -- "does the intens/extens gap close with scale, and
does it close at the same rate for every lab" is a question the varying-quiz
studies cannot answer, because they never held more than three checkpoints
still long enough to plot a ladder.

Full deployment facts (hf_model_id, tensor parallelism, instance tier,
reasoning-parser wiring) live in ``smolbench.evals.ec2.EC2_DEPLOY_SPECS`` --
see its "Family-ladder scaling study roster" comment block. THIS file is the
single source of truth for the STUDY's config (seeds, info arms, per-model
CoT toggles, budget derivation); the notebook
``notebooks/induction/induction_eval.ipynb`` imports every module-level name
below rather than re-declaring any of them, so the notebook and a standalone
``python run_study.py`` invocation can never drift apart.

ONE MODEL PER BOX, driven by a fleet
-------------------------------------
Unlike the three-checkpoint studies, which serve their whole trio in
sequence on one instance, this study provisions ONE EC2 spot instance PER
MODEL -- 21 boxes, potentially all live at once. That fan-out is owned by a
fleet supervisor (``scripts/run_fleet.py``, written separately, not by this
file) which sets ``INDUCTION_MODELS=<single spec key>`` in each lane's
environment before invoking this driver, so a standalone run of this file
(no ``INDUCTION_MODELS`` set) still does the obvious thing -- run every
model, one after another -- for local smoke-testing and for anyone who wants
to reproduce the whole study serially without the fleet.

Seeds: BASE_SEED=0, n_replicates=30 (USER-LOCKED)
---------------------------------------------------
Every induction study before this one seeded from 1776 (the July 4th, 1776
nod baked into ``InductionExperiment.base_seed``'s own default). This study
deliberately uses ``BASE_SEED=0`` instead -- seeds 0..29 -- a user-locked
choice, NOT an oversight or a copy-paste of the wrong constant. It exists so
this study's replicate seeds can never silently alias a sibling study's
(e.g. sharing a results bucket prefix by accident would still produce
distinguishable seed ranges). ``N_REPLICATES=30`` is likewise user-locked
and, unlike every prior driver's ``*_N_REPLICATES`` environment override, is
NOT environment-overridable here -- the family-ladder comparison across 21
checkpoints is only apples-to-apples if every checkpoint collects exactly
the same replicate count, so there is deliberately no knob that could let
one lane collect a different R than its siblings.

The four info arms
--------------------
Identical to ``periodic_moe``'s: ``intens`` (the rule list), ``extens`` (the
full positional listing), ``noise_intens`` (the rule list padded with
whitespace to ``extens``'s own token count under the SERVED model's
tokenizer -- a length control, not a content control), and ``zero`` (empty
context, chance-floor baseline). See ``make_quizzes`` below.

Reasoning: CoT is ON for every model in this study
-----------------------------------------------------
Every one of the 21 checkpoints is served with its thinking/reasoning mode
enabled -- ``COT_ARGS`` below is TOTAL over ``MODELS`` (a table, not a
computed default), because a ``KeyError`` on ``COT_ARGS[model]`` inside
``main()`` would fire only AFTER ``EXPERIMENT.provision()``, i.e. on a
billing box. How thinking gets turned on differs by vendor template:

  * Qwen3.5 / Nemotron-3 / Gemma-4 / GLM-4.x / EXAONE / K-EXAONE:
    ``chat_template_kwargs={"enable_thinking": True}``. Gemma-4's shipped
    template and EXAONE-4.0-32B's shipped template both default this to
    FALSE, so for those two the explicit ``True`` is load-bearing, not
    redundant -- omitting it would silently serve them non-reasoning. (The
    other five checkpoints in this bucket default thinking ON already; the
    explicit kwarg is still sent so the table stays auditable at a glance
    against ``ec2.py``'s "Reasoning wiring" comment, rather than half the
    rows relying on an unstated per-vendor default.)
  * DeepSeek V4-Flash / V3.1 / V4-Pro:
    ``chat_template_kwargs={"thinking": True}`` -- a DIFFERENT kwarg name
    from every other family. For the two V4 checkpoints this also selects
    the ``<think>``-opening branch of the inline ``DSV4_CHAT_TEMPLATE`` (see
    ``ec2.py``) since DeepSeek-V4 ships no chat template of its own.
  * Ministral-3 (3B/8B/14B): the empty dict ``{}``. Ministral's ``[THINK]``
    protocol lives ONLY in its shipped template's ``default_system_message``,
    which the template injects when no system message is supplied --
    ``ec2.py``'s deploy spec already injects that exact text as the
    checkpoint's ``system_prompt``, so a ``chat_template_kwargs`` entry here
    would do nothing. The empty-dict entries stay in the table (rather than
    being omitted) purely so the table remains TOTAL over ``MODELS`` --
    dropping them would make ``COT_ARGS[model]`` raise for exactly the three
    keys most likely to be re-added carelessly later.

Environment
-----------
``INDUCTION_SHARD``
    ``"index/count"`` -- splits ONE model's 30 replicates across ``count``
    processes/instances (see ``_parse_shard``). Orthogonal to the
    one-model-per-box fan-out above: sharding exists for the case where even
    one model's replicates should be parallelised further.
``INDUCTION_MODELS``
    Comma-separated subset filter on SPEC KEY (e.g.
    ``glm-4.7-flash``), NOT on the analysis tag -- the fleet supervisor sets
    this to a SINGLE spec key per lane. Unset/empty (the default) selects
    all 21, in ``MODELS`` declaration order; see ``selected_models``.
``INDUCTION_STATE_FILE``
    Repo-root-anchored basename for this process's EC2 state file, threaded
    through the ``InductionExperiment(state_file=...)`` constructor
    argument. Setting the bare shell variable ``EC2_STATE_FILE`` is NOT
    enough on its own: ``InductionExperiment._apply_env`` OVERWRITES
    ``EC2_STATE_FILE`` from the ``state_file`` field on every
    ``provision``/``run``/``teardown`` call, so the only way to point this
    driver at a non-default state file is through this environment variable
    (which flows into the constructor) or by editing ``_DEFAULT_STATE_FILE``
    directly. With 21 lanes potentially live at once, the fleet supervisor
    MUST set a distinct value per lane -- two lanes sharing a state file
    would have the second ``provision()`` call reattach to the first lane's
    instance and swap the served model out from under it.

Lifecycle contract: NO teardown on the normal path
-----------------------------------------------------
This is the single most dangerous thing to get wrong in this file.
``main()`` never calls ``EXPERIMENT.teardown()`` except behind the explicit
``--teardown`` flag. Under the fleet, EACH LANE'S BOX IS REUSED BY A LATER
DEDUCTION-PHASE LANE -- the fleet supervisor owns instance lifecycle
end-to-end and runs its own shutdown step only after BOTH phases have
finished with that box. A ``teardown()`` call here, on the normal
induction-phase path, would terminate the instance the deduction phase is
about to reattach to -- silently turning a scheduled reuse into a second,
unplanned provision (new spot bid, new HF cache pull, real dollars) or, if
the deduction lane loses the race, an outright failure. ``--teardown`` exists
purely for STANDALONE use (a solo smoke test of this file with nothing else
depending on the box); it must never be invoked by the fleet's normal path.

Cost warning
------------
``EXPERIMENT.provision()`` and ``EXPERIMENT.run()`` are LIVE AWS calls
against self-provisioned EC2 spot instances, one PER MODEL, billed for the
duration each is up. Instance tiers span g6e.4xlarge (single L40S) up to
p5e.48xlarge (8x H200) depending on the checkpoint -- see
``EC2_DEPLOY_SPECS``'s tier table. Running this file unsharded, unfiltered,
and standalone provisions and serves ALL 21 checkpoints in turn on ONE
instance that is reconfigured 21 times; running it under the fleet
provisions up to 21 DISTINCT instances concurrently. Either way this is real
GPU spend -- verify ``INDUCTION_MODELS`` before invoking outside the fleet.

Run (repo root, main venv):
    .venv/bin/python notebooks/induction/run_study.py
"""

import argparse
import logging
import os
import string
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd, and MUST land before smolbench.evals.ec2
# is imported anywhere -- ec2.py freezes its EC2_* constants at import time
# (see InductionExperiment's module docstring, "CRITICAL: no
# smolbench.evals.ec2 import at module scope"). NOT override=True: under the
# fleet, the supervisor materialises a per-lane environment (INDUCTION_MODELS,
# INDUCTION_STATE_FILE, EC2_EXPERIMENT_TAG, ...) before this file is invoked,
# and keys.env populating already-set variables would clobber that per-lane
# config with this file's own local defaults.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parses a ``index/count`` shard selector from the environment.

    Sharding splits ONE model's replicates across N processes/instances,
    orthogonal to this study's one-model-per-box fan-out (see the module
    docstring): even a single model's 30 replicates can be parallelised
    further if 30 sequential requests to one box is still the bottleneck.

    Parameters
    ----------
    var : str
        Name of the environment variable to read (e.g. ``"INDUCTION_SHARD"``).

    Returns
    -------
    tuple[int, int] | None
        ``(index, count)`` if `var` is set to a valid ``"index/count"``
        string; ``None`` if `var` is unset or empty (the unsharded default).

    Raises
    ------
    SystemExit
        If `var` is set but is not parseable as ``"int/int"``, or if the
        parsed values fail ``count >= 1`` / ``0 <= index < count``. Raised
        rather than returned so a malformed shard selector fails immediately
        at import time rather than silently running as unsharded or crashing
        deep inside ``InductionExperiment``.
    """
    raw = os.environ.get(var, "").strip()
    if not raw:
        return None
    try:
        index, count = (int(part) for part in raw.split("/", 1))
    except ValueError:
        raise SystemExit(f"{var}={raw!r}: expected 'index/count', e.g. {var}=0/3")
    if count < 1 or not (0 <= index < count):
        raise SystemExit(f"{var}={raw!r}: need count >= 1 and 0 <= index < count")
    return index, count


SHARD = _parse_shard("INDUCTION_SHARD")

# A shard needs its OWN AWS tag and state file -- without that, shard 1
# reattaches to shard 0's live box and swaps the served model out from under
# a run in progress (the exact collision the periodic_divisor driver hit
# first). Deriving both from the lane, rather than asking every caller to
# remember two more environment variables, removes that footgun.
#
# This MUST execute before smolbench.evals.ec2 is imported below: ec2.py
# freezes its EC2_* constants from os.environ at import time, so a tag set
# afterwards is silently ignored. Unsharded runs get an empty suffix.
_LANE = ""
if SHARD is not None:
    _models = os.environ.get("INDUCTION_MODELS", "").strip().replace(",", "-")
    _LANE = (f"-{_models}" if _models else "") + "-s{}of{}".format(*SHARD)
    os.environ["EC2_EXPERIMENT_TAG"] = (
        os.environ.get("EC2_EXPERIMENT_TAG", "induction-scaling") + _LANE
    )
_DEFAULT_STATE_FILE = f".ec2_state_induction{_LANE}.json"

from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    get_periodic_zero_info_numeric_quiz,
    numeric_count_query_gen,
)

#: USER-LOCKED. Every prior induction study seeded from 1776; this study
#: deliberately uses 0 so its seed range (0..29) can never silently alias a
#: sibling study's -- see the module docstring's "Seeds" section.
BASE_SEED: int = 0

#: USER-LOCKED and, unlike every sibling driver's ``*_N_REPLICATES``
#: environment override, NOT environment-overridable: the family-ladder
#: comparison across 21 checkpoints is only apples-to-apples if every
#: checkpoint collects the same replicate count.
N_REPLICATES: int = 30

#: The four amounts-of-positive-information conditions, identical to
#: periodic_moe's. See the module docstring's "The four info arms" section.
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens", "zero")

#: The served checkpoints' context window. Every EC2_DEPLOY_SPECS entry in
#: this study's roster serves at max_model_len=131072 uniformly (see that
#: table's roster comment) -- a scaling study cannot let context vary with
#: the vendor's own YaRN generosity, or a family's ceiling would be
#: confounded with its context budget rather than its parameter count.
CONTEXT_LIMIT: int = 131_072

#: Tokens withheld from the completion budget, covering what a count() on
#: one seed's prompt cannot see: the chat template's own special/BOS tokens
#: (count() deliberately excludes them -- see the Tokenizer protocol
#: docstring in tokenization.py) plus cross-seed variation in the
#: randomly-sampled labels, which compounds over a long extensional
#: listing. Sized generously (sibling studies measured this reserve in the
#: 1,500-3,700 token range on comparable listings) so the derived budget
#: stays safe even when the seed probe below misses the single longest seed
#: across all 30. It costs only completion headroom that would otherwise go
#: unused.
TEMPLATE_RESERVE: int = 8_000

#: Seeds sampled when measuring the worst-case prompt in completion_budget.
#: See that function's docstring for why bracketed subsampling suffices.
PROBE_SEEDS: int = 6

#: Floor below which a run is not worth starting. A completion budget below
#: this is likely to truncate a CoT checkpoint's reasoning before it reaches
#: the final integer -- collecting empties (no completion AND no reasoning
#: trace) rather than data that can be scored, marked invalid, or even
#: diagnosed after the fact.
MIN_VIABLE_BUDGET: int = 48_000

#: Ceiling applied AFTER the derived per-model budget below. A single plain
#: int, NOT a per-model dict -- see completion_budget's docstring for why a
#: cross-vendor SCALING study cannot let this vary by vendor.
BUDGET_CAP: int = CONTEXT_LIMIT

# Byte-identical to periodic_moe's / periodic_divisor's template: the prompt
# WORDING is held fixed across every induction study to date, so the only
# thing that ever varies between studies is the roster (model, quiz
# generator, or -- in periodic_divisor's case -- the harmonic set) that
# fills in $positive_info / $seq_len / $label.
template = string.Template(
    "You are a precise integer counter.\n"
    "\n"
    "Task: answer the question below with a single integer and nothing else.\n"
    "\n"
    "Output format:\n"
    "Return exactly one integer and nothing else.\n"
    "Do not output any explanation, punctuation, quotes, or extra whitespace.\n"
    "Stop immediately after writing the integer.\n"
    "\n"
    "Context:\n"
    "There is a counting game. Positions are counted starting from 1. "
    "At each position, words are written according to the following rules:\n"
    "$positive_info\n"
    "Question:\n"
    "How many of the positions 1 through $seq_len include '$label'?"
)

# Spec key (smolbench.evals.ec2.EC2_DEPLOY_SPECS key, also vLLM's
# --served-model-name) -> short analysis tag used in result directory names
# and figure legends. Exactly EC2_DEPLOY_SPECS's 21 family-ladder entries,
# i.e. every key except the "qwen2.5-1.5b" single-GPU smoke entry. Order is
# the study's canonical order -- see selected_models' docstring for why this
# matters beyond mere readability.
MODELS: dict[str, str] = {
    # -- Qwen3.5 (Alibaba, CN): 27B dense / 122B-A10B / 397B-A17B (FP8) --
    "qwen3.5-27b": "qwen35_27b",
    "qwen3.5-122b-a10b": "qwen35_122b",
    "qwen3.5-397b-a17b": "qwen35_397b",
    # -- Nemotron 3 (NVIDIA, US): Nano-4B / Nano-30B-A3B / Super-120B-A12B --
    "nemotron-3-nano-4b": "nemo3_4b",
    "nemotron-3-nano-30b-a3b": "nemo3_30b",
    "nemotron-3-super-120b-a12b": "nemo3_120b",
    # -- Gemma 4 (Google, US): E2B / 12B / 31B instruction-tuned --
    "gemma-4-e2b": "gemma4_e2b",
    "gemma-4-12b": "gemma4_12b",
    "gemma-4-31b": "gemma4_31b",
    # -- GLM-4.x (Zhipu/Z.ai, CN): 4.7-Flash / 4.5-Air / 4.7 (cross-gen) --
    "glm-4.7-flash": "glm_flash",
    "glm-4.5-air": "glm_air",
    "glm-4.7": "glm_47",
    # -- Ministral-3 Reasoning (Mistral, FR): 3B / 8B / 14B --
    "ministral-3-3b": "min3_3b",
    "ministral-3-8b": "min3_8b",
    "ministral-3-14b": "min3_14b",
    # -- EXAONE (LG AI Research, KR): 4.0-32B / 4.5-33B / K-EXAONE-236B (x-gen) --
    "exaone-4.0-32b": "exaone_32b",
    "exaone-4.5-33b": "exaone_33b",
    "k-exaone-236b-a23b": "exaone_236b",
    # -- DeepSeek (CN): V4-Flash / V3.1 / V4-Pro (cross-generation) --
    "deepseek-v4-flash": "ds_flash",
    "deepseek-v3.1": "ds_v31",
    "deepseek-v4-pro": "ds_pro",
}

# Per-request extra args that turn CoT ON for each of the 21 checkpoints.
# TOTAL over MODELS by construction (written out literally, not built from a
# prefix rule) so the table itself is the audit surface against ec2.py's
# "Reasoning wiring" comment, and so a typo in a family prefix can never
# produce a silent KeyError deep inside main() on a billing box. Four rules,
# summarised (full rationale for each is in the module docstring):
#   1. Qwen3.5 / Nemotron-3 / Gemma-4 / GLM-4.x / EXAONE / K-EXAONE:
#      {"chat_template_kwargs": {"enable_thinking": True}}.
#   2. DeepSeek V4-Flash / V3.1 / V4-Pro: {"chat_template_kwargs":
#      {"thinking": True}} -- note the DIFFERENT kwarg name from rule 1.
#   3. Ministral-3 (3B/8B/14B): {} -- its think protocol is switched on by
#      ec2.py's injected system_prompt, not by a chat_template_kwarg.
#   4. Gemma-4-* and EXAONE-4.0-32B in particular NEED their explicit
#      "enable_thinking": True: both checkpoints' shipped templates default
#      thinking OFF, so omitting the kwarg would silently serve them
#      non-reasoning while every other checkpoint in the study reasons.
COT_ARGS: dict[str, dict] = {
    "qwen3.5-27b": {"chat_template_kwargs": {"enable_thinking": True}},
    "qwen3.5-122b-a10b": {"chat_template_kwargs": {"enable_thinking": True}},
    "qwen3.5-397b-a17b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-nano-4b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-nano-30b-a3b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-super-120b-a12b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-e2b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-12b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-31b": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.7-flash": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.5-air": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.7": {"chat_template_kwargs": {"enable_thinking": True}},
    "ministral-3-3b": {},
    "ministral-3-8b": {},
    "ministral-3-14b": {},
    "exaone-4.0-32b": {"chat_template_kwargs": {"enable_thinking": True}},
    "exaone-4.5-33b": {"chat_template_kwargs": {"enable_thinking": True}},
    "k-exaone-236b-a23b": {"chat_template_kwargs": {"enable_thinking": True}},
    "deepseek-v4-flash": {"chat_template_kwargs": {"thinking": True}},
    "deepseek-v3.1": {"chat_template_kwargs": {"thinking": True}},
    "deepseek-v4-pro": {"chat_template_kwargs": {"thinking": True}},
}


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generates one replicate's four info-type quizzes, keyed by info type.

    The plain ``periodic_moe`` baseline config (``n=9`` harmonics, default
    consecutive-integer periods 1..9, lcm==2,520) -- unmodified, because this
    study's independent variable is the MODEL, not the quiz. Holding the
    quiz fixed across all 21 checkpoints is what makes an accuracy
    difference between two rungs of one family, or between two families at
    a comparable rung, attributable to the model rather than to a changed
    task.

    Parameters
    ----------
    seed : int
        Drives both the quiz's own randomness (label sampling; see
        ``PeriodicConfig.seed``) and, downstream in ``ReplicateHarness``, the
        per-request decoding seed -- see ``InductionExperiment``'s module
        docstring, "Seed convention".
    model : str
        Spec key of the checkpoint under test (an ``EC2_DEPLOY_SPECS`` /
        ``MODELS`` key). Required because ``noise_intens`` is a TOKEN-LENGTH
        control: it is padded with whitespace until its prompt has exactly
        as many tokens as the matching ``extens`` prompt, measured with
        THIS model's own tokenizer (``for_model(model)``) -- a
        character-matched pad would systematically over- or under-pad
        depending on how that model's tokenizer happens to encode
        structured vs. random text (see ``tokenization.py``'s module
        docstring for the measured magnitude of that error). The other
        three conditions are model-independent and stay byte-identical
        across every checkpoint in the study.

    Returns
    -------
    dict[str, tuple]
        Keys exactly ``INFO_TYPES`` ("intens", "extens", "noise_intens",
        "zero"), in that order. Each value is the ``Quiz`` (tuple of
        prompt/answer pairs) for that info type.

    Notes
    -----
    Calls the MODULE-LEVEL ``for_model`` by plain global lookup (not a
    captured default argument or local alias) so tests can monkeypatch
    ``run_study.for_model`` to stay off the network -- see
    ``tests/test_induction_study.py``, which does exactly that (and also
    monkeypatches ``run_study.make_quizzes`` for the same reason) to keep the
    offline suite from downloading a tokenizer.
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    prompter = Prompter(template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(
        cfg, prompter, tokenizer=for_model(model)
    )
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


def completion_budget(model: str, seeds: range) -> int:
    """Largest completion budget that cannot overflow this model's context.

    Derived rather than hardcoded -- sibling studies (periodic_divisor,
    periodic_moe) both learned the hard way that a hand-picked completion
    budget either truncates a CoT checkpoint mid-``<think>`` (empty
    completion AND empty reasoning) or, sized too generously against a
    measured-not-actual prompt length, overshoots the context window by even
    one token and gets the whole request rejected with a 400. So the
    arithmetic lives here, run over the ACTUAL worst-case prompt across a
    bracketed subsample of this study's seeds, with ``TEMPLATE_RESERVE``
    covering what ``count()`` cannot see (chat-template special tokens) and
    what one seed's prompt cannot show (cross-seed label-length variation).
    Runs BEFORE provisioning, so its cost is wall-clock on a machine that is
    not yet billing.

    No per-model ceiling. ``BUDGET_CAP`` is a single ``int`` (==
    ``CONTEXT_LIMIT``), not a per-model dict as in the periodic_divisor
    driver this function was ported from -- deliberately, because THIS study
    tests whether accuracy scales with parameter count ACROSS vendors. If
    one family's completion budget were capped tighter than another's (e.g.
    because one checkpoint in the trio had once truncated), any accuracy gap
    between the two families would be inseparable from "the capped one just
    had less room to finish its reasoning" -- the scaling claim this study
    exists to make would stop being falsifiable. So every checkpoint gets
    the same context-derived ceiling; the ``min()`` below is therefore a
    documented no-op guard against the (currently impossible, since
    ``BUDGET_CAP == CONTEXT_LIMIT``) case of a future edit reintroducing a
    tighter cap without updating the arithmetic that follows it.

    Parameters
    ----------
    model : str
        Spec key of the checkpoint to size a budget for.
    seeds : range
        The full seed range this study will send to `model` (e.g.
        ``range(BASE_SEED, BASE_SEED + N_REPLICATES)``). Only a bracketed
        subsample of these is actually probed -- see Notes.

    Returns
    -------
    int
        ``min(CONTEXT_LIMIT - worst - TEMPLATE_RESERVE, BUDGET_CAP)``, where
        ``worst`` is the largest token count seen across every info type of
        every probed seed. Always ``>= MIN_VIABLE_BUDGET`` (see Raises).

    Raises
    ------
    SystemExit
        If the derived budget would fall below ``MIN_VIABLE_BUDGET``. The
        message names `model`, the measured worst-case prompt size, the
        budget that arithmetic would have produced, and the floor it fell
        under, so the failure is actionable without re-deriving any of those
        numbers by hand.

    Notes
    -----
    Pure CPU + a HuggingFace tokenizer fetch (via ``for_model``) -- no AWS,
    runnable before any instance is provisioned. Subsamples ``PROBE_SEEDS``
    seeds, always including both endpoints of `seeds`, rather than probing
    all 30: the structural drivers of prompt length (info type, harmonic
    count, sequence length) are identical for every seed in this study --
    only the randomly-sampled labels vary, a few hundred tokens at most --
    and ``TEMPLATE_RESERVE`` already covers far more than that residual
    variation, so probing all 30 would cost minutes per model for
    negligible additional safety.
    """
    tok = for_model(model)
    picks = sorted({seeds[0], seeds[-1],
                    *(seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)]
                      for i in range(PROBE_SEEDS))}) if len(seeds) > 1 else list(seeds)
    worst = 0
    for seed in picks:
        for quiz in make_quizzes(seed, model).values():
            worst = max(worst, max(tok.count(q.prompt) for q in quiz))
    budget = min(CONTEXT_LIMIT - worst - TEMPLATE_RESERVE, BUDGET_CAP)
    if budget < MIN_VIABLE_BUDGET:
        raise SystemExit(
            f"{model}: worst prompt is {worst:,} tokens, leaving only {budget:,} for "
            f"completion against a {CONTEXT_LIMIT:,} context. That is below the "
            f"{MIN_VIABLE_BUDGET:,} floor and would collect empties, not data. "
            "Shorten the period set or investigate why this checkpoint's prompts "
            "are unusually large."
        )
    logging.info(
        f"{model}: worst prompt {worst:,} tok (+{TEMPLATE_RESERVE:,} reserve) "
        f"-> completion budget {budget:,}"
    )
    return budget


# notebook_dir="induction" is what makes results_store.experiment_name()
# derive this experiment's S3 log path segment to "induction" -- i.e. every
# replicate this study collects lands under S3 keys shaped
# induction/<spec-key>/seed=<seed>/<info>--<run_ts>.yaml, distinct from
# every sibling study's own notebook_dir-derived prefix.
EXPERIMENT = InductionExperiment(
    notebook_dir="induction",
    archetype_tags=MODELS,
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=N_REPLICATES,
    base_seed=BASE_SEED,
    state_file=os.environ.get("INDUCTION_STATE_FILE", _DEFAULT_STATE_FILE),
    shard=SHARD,
    # INDUCTION_FORCE_RERUN=1: re-collect every replicate this process is
    # responsible for even when the store already has it (newest run_ts
    # supersedes on read). For deliberate re-collection ONLY -- e.g. the
    # 2026-08-13 gemma-4-12b re-run on g7 hardware to keep the lane's 30
    # seeds serving-stack-homogeneous. Combine with INDUCTION_SHARD to
    # parallelize the re-run across boxes.
    force_rerun=os.environ.get("INDUCTION_FORCE_RERUN", "").strip() == "1",
)


def selected_models() -> "tuple[str, ...]":
    """Returns the spec keys to run, in ``MODELS`` declaration order.

    Declaration order -- not, say, smallest-checkpoint-first as the
    three-model drivers used to fail fast on the biggest pull -- because
    that failure-ordering rationale does not transfer here: the fleet runs
    exactly ONE model per lane, so there is no "run the cheap one first on
    this box" benefit to reordering. Family-grouped declaration order is
    instead this study's CANONICAL order (it is the order the roster is
    documented in, in both this file and ``ec2.py``), and keeping
    ``selected_models()`` stable in that order is what makes a standalone,
    unsharded, unfiltered run of this file deterministic and easy to reason
    about against the module docstring's roster listing.

    Returns
    -------
    tuple[str, ...]
        Spec keys from ``INDUCTION_MODELS`` (or all 21 keys of ``MODELS`` if
        that variable is unset/empty), filtered to ``MODELS`` declaration
        order regardless of the order they were listed in the environment
        variable.

    Raises
    ------
    SystemExit
        If ``INDUCTION_MODELS`` names any key that is not in ``MODELS`` --
        the message lists every offending key together with the full set of
        valid keys. Also raised if ``INDUCTION_MODELS`` is SET but resolves
        to ZERO keys after splitting/stripping (e.g. ``","`` or ``" , "`` --
        a lone comma is non-empty, so it does NOT fall into the "unset/empty
        selects all" branch above it). That degenerate case matters more
        than a cosmetic validation nicety: ``main()`` calls
        ``EXPERIMENT.provision()`` unconditionally and, per this file's
        "Lifecycle contract" (see the module docstring), never tears the
        instance down on the normal path -- so a silently-empty selection
        would provision a live GPU box, run zero replicates on it, and leave
        it billing with nothing driving it. Both failures fire before any
        instance is provisioned.
    """
    wanted = os.environ.get("INDUCTION_MODELS", "").strip()
    if not wanted:
        return tuple(MODELS)
    keys = [k.strip() for k in wanted.split(",") if k.strip()]
    if not keys:
        raise SystemExit(
            f"INDUCTION_MODELS={wanted!r}: named no models (only commas/"
            "whitespace after splitting). Leave it unset to select all 21, "
            "or name at least one spec key."
        )
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        raise SystemExit(
            f"INDUCTION_MODELS: unknown key(s) {unknown}; pick from {sorted(MODELS)}"
        )
    chosen = set(keys)
    return tuple(m for m in MODELS if m in chosen)


def main(argv: "list[str] | None" = None) -> None:
    """Entry point: warms tokenizers, provisions, runs, summarizes.

    Never tears the instance(s) down on the normal path -- see the module
    docstring's "Lifecycle contract" section for why that omission is
    deliberate rather than an oversight.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments to parse, or ``None`` (the default) to parse
        ``sys.argv`` as ``argparse`` normally would. Exposed as a parameter
        so this function is callable from a test or notebook cell without
        going through a subprocess.

    Returns
    -------
    None

    Notes
    -----
    Live AWS calls (``EXPERIMENT.provision()`` / ``EXPERIMENT.run()``) on
    every path except ``--teardown`` with nothing yet provisioned and every
    path where argument parsing itself fails. See the module docstring's
    cost warning.
    """
    parser = argparse.ArgumentParser(
        description="Family-ladder scaling induction study driver."
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        help=(
            "Terminate this experiment's EC2 instance and exit immediately. "
            "STANDALONE USE ONLY: under the fleet, the supervisor owns "
            "instance lifecycle and tears down after the deduction phase "
            "has also finished with the box -- do not invoke this flag from "
            "fleet-driven automation."
        ),
    )
    args = parser.parse_args(argv)

    if args.teardown:
        EXPERIMENT.teardown()
        return

    models = selected_models()
    logging.info(f"running models: {list(models)}")

    # Warm every model's tokenizer and derive its completion budget BEFORE
    # provisioning anything: an HF tokenizer-download failure or an
    # under-budget SystemExit must never land between a billing GPU box and
    # the first inference request.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets: dict[str, int] = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    EXPERIMENT.provision()
    for model in models:
        EXPERIMENT.run(
            model,
            extra_args={"max_completion_tokens": budgets[model], **COT_ARGS[model]},
        )
        EXPERIMENT.summarize(model)
    # NOTE: deliberately NO EXPERIMENT.teardown() here. See the module
    # docstring's "Lifecycle contract" section -- the fleet supervisor owns
    # instance lifecycle and this box may be reused by the deduction phase
    # after this process exits. Tearing down here would terminate it out
    # from under that reattachment.
    print(f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
          flush=True)


if __name__ == "__main__":
    main()
