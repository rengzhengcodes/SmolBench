"""Per-lane driver for the DEDUCTION side of the family-ladder scaling study.

WHAT THIS IS
------------
``notebooks/induction/run_study.py`` documents a 21-checkpoint family-ladder
scaling study (``MODELS``: 7 vendor families x 3 rungs each). It runs ONE
MODEL PER BOX under a fleet supervisor (``scripts/run_fleet.py``). That file
covers the INDUCTION phase. THIS file is the matching DEDUCTION-phase
driver. One invocation serves exactly ONE checkpoint on one EC2 box. It
runs one ``smolbench.deduction.lean.runner.sweep`` (a Lean4 theorem-proving
sweep) against that checkpoint. The fleet supervisor launches up to 21 of
these as subprocesses, one per lane. Each lane normally REATTACHES to the
same box its induction phase already provisioned. It reuses the same
``EC2_EXPERIMENT_TAG`` and the same EC2 state file (see
``scripts/run_fleet.py``'s ``lane_env``). This avoids provisioning a second
instance per model.

This file does not redeclare ``MODELS`` (spec key -> short analysis tag) or
``COT_ARGS`` (spec key -> per-request reasoning-toggle kwargs). It imports
both by file path from ``notebooks/induction/run_study.py``, the single
source of truth for this study's roster. See "MODULE IMPORT ORDER" below
for how and why.

MODULE IMPORT ORDER (load-bearing -- read this before editing anything else)
------------------------------------------------------------------------------
This file's top-level statements MUST execute in the order below. This
order is the single most important property of this file. If you get it
wrong, the file raises no exception. Instead, this lane's EC2 tag, state
file, and vLLM image silently drift onto whatever value a
fleet-supervisor export, an unrelated ``keys.env``, or
``smolbench.evals.ec2``'s own hardcoded defaults happen to set. You
discover this drift only later, on a live billing box, when you notice two
lanes swapped their served checkpoints.

  1. Stdlib imports only (``argparse``, ``copy``, ``importlib.util``,
     ``logging``, ``os``, ``sys``, ``pathlib.Path``, ``typing.Any``).
  2. Compute ``REPO_ROOT`` and the S3-spool constants (pure arithmetic, no
     environment or filesystem side effects).
  3. Define ``lane_env_defaults`` (a pure function). It has no side effects
     on its own, but step 4 calls it, so it must exist first.
  4. Read the RAW ``LEAN_MODEL`` and ``LEAN_STATE_FILE`` strings from
     ``os.environ``. Do NOT validate ``LEAN_MODEL`` against ``MODELS``
     yet -- ``MODELS`` is not loaded until step 6. For every ``(name,
     value)`` pair ``lane_env_defaults`` derives from those raw strings,
     call ``os.environ.setdefault(name, value)``. Use ``setdefault``,
     NEVER a bare assignment, for all four variables. This way, a value
     the fleet supervisor already exported into this subprocess's
     environment always wins over this file's own default.
  5. THEN, and only then, import ``smolbench.evals.ec2`` (transitively, via
     loading ``notebooks/induction/run_study.py`` in step 6 below) and
     anything else that reads ``EC2_*`` environment variables at MODULE
     SCOPE.
  6. Load ``notebooks/induction/run_study.py`` by file path (never a bare
     ``import run_study`` -- see the docstring of the loader block below for
     why), and bind ``MODELS`` / ``COT_ARGS`` from it.
  7. Import ``smolbench.evals.ec2``, ``smolbench.deduction.lean.runner``,
     and ``smolbench.deduction.lean.nullverify`` (``# noqa: E402`` on all
     three, matching ``notebooks/induction/run_study.py``'s own late-import
     style for the same reason).

WHY THIS ORDER IS CORRECT (verified against the current tree, not assumed
from memory of some other file's contents -- see the note at the end of
this section):

  * ``smolbench/evals/ec2.py`` reads ``EC2_EXPERIMENT_TAG``,
    ``EC2_VLLM_IMAGE``, ``EC2_INSTANCE_TYPES``, and ``EC2_REGIONS`` via
    ``os.getenv(...)`` at MODULE SCOPE, and freezes each into a plain
    module constant. Python caches module imports in ``sys.modules``, so
    once this process imports that module once, those four values stay
    fixed for the rest of the process. An ``os.environ`` write after that
    import has NO effect on them, however you spell it. So our own
    ``setdefault`` calls (step 4) matter only if they land before the
    FIRST import of ``smolbench.evals.ec2`` anywhere in this process
    (step 7, and transitively step 6 -- see below).
  * Step 6 loads ``notebooks/induction/run_study.py``. That module's own
    top-level code calls ``load_dotenv(.../induction/keys.env)`` as a side
    effect (see that file's own module docstring). This call pulls in
    ``smolbench.induction.experiment``, which imports
    ``smolbench.evals.ec2``. So step 6 is ALSO the first point that
    imports ``ec2.py``. Steps 4 and 6 must stay in this order.
  * That ``load_dotenv`` call does NOT pass ``override=True`` (confirmed by
    reading that file directly, not assumed). So it can only fill in
    variables that are CURRENTLY UNSET in ``os.environ`` -- it can never
    overwrite a value already present. This is why "our setdefault first,
    then load that module" is enough: whatever ``keys.env`` does or does
    not set is irrelevant to variables we already set ourselves before
    that module loads.
  * One caveat, stated plainly rather than left implicit: this file does
    not rely on, or hardcode, WHICH specific ``EC2_*`` keys
    ``notebooks/induction/keys.env`` sets. A sibling study owns that file,
    and its contents can and do change over time (run ``grep '^EC2_'
    notebooks/induction/keys.env`` for the CURRENT answer). The ordering
    above is correct no matter what that file currently contains, because
    it follows from the two mechanisms above (import-time freezing plus a
    non-overriding ``load_dotenv``), not from any one snapshot of that
    file's keys.

SWEEP CONFIG (USER-LOCKED)
---------------------------
``build_config`` returns a fixed sweep configuration: seed, decoding params,
the theorem pool selector, and the four rungs. This configuration is
identical for all 21 checkpoints, except for ``model``, ``display_name``,
and ``extra_params`` (which vary per checkpoint) and ``run_name`` (which
varies per lane). Holding everything else fixed lets a next-tactic
success-rate difference between two checkpoints point to the model, not to
a changed sweep. See ``build_config``'s own docstring for the exact keys
and values, and for why they must never be renamed or re-derived here --
this driver adapts nothing; ``runner.sweep`` already accepts every key
verbatim.

VERIFIER SELECTION (``LEAN_VERIFY``, default ``"defer"``)
-------------------------------------------------------------
``runner.sweep`` never touches Lean directly. Every Dojo interaction goes
through an injected ``verifier`` object (see
``smolbench.deduction.lean.nullverify``'s module docstring, "Two-phase
workflow"). This driver runs on the MAIN venv (Python 3.14), which cannot
import ``smolbench.deduction.lean.verify`` at all -- that module requires
``lean_dojo``, which pins ``python<3.13``. So by default
(``LEAN_VERIFY=defer``) this driver passes a ``NullVerifier()`` and
produces GENERATION-ONLY rows (every cell's verdict is ``"unverified"``).
A separate, later pass under ``.venv-lean`` replays and verifies those
candidate proof tails against the real Dojo. ``LEAN_VERIFY=real`` exists
for completeness, so this same file can, in principle, drive a real
verifying sweep. It is reachable only under ``.venv-lean`` itself -- see
``select_verifier``'s docstring for the exact guard and error message.

LIFECYCLE (``main``)
---------------------
1. Resolve the lane's model key from ``LEAN_MODEL`` (``selected_model``).
   Raises ``SystemExit`` if it is unset or unknown.
2. Build this lane's sweep config and compute its run directory.
3. Resolve the verifier (``select_verifier``). Do this BEFORE provisioning,
   so a bad ``LEAN_VERIFY`` value aborts before any EC2 spend. This matches
   the "fail fast before billing" pattern used throughout this study's
   tooling (see e.g. ``notebooks/induction/run_study.py``'s
   ``completion_budget`` and ``scripts/run_fleet.py``'s ``preflight``, both
   of which run entirely before ``provision_spot_instance``).
4. Call ``ec2.provision_spot_instance()`` with NO arguments. Its behavior
   depends entirely on the ``EC2_INSTANCE_TYPES``/``EC2_REGIONS`` frozen
   module constants (set from this process's environment, per the ordering
   above). This call is idempotent: it reattaches to a live instance
   recorded under this lane's state file / experiment tag, instead of
   launching a second one. This is exactly how a deduction lane reattaches
   to the box its own induction phase already provisioned.
5. Enter ``with ec2.serve_model(key):``. If ``--force-rerun`` was passed,
   first archive any existing ``all_rows.jsonl`` in the run directory to a
   timestamped ``_SUPERSEDED`` file (see ``main``'s own code for why).
   Then call ``n = runner.sweep(config, run_dir,
   resume=not args.force_rerun, verifier=...)``.
6. Unless ``--no-s3`` was passed, spool the run directory to S3
   (``spool_to_s3``).
7. If ``--teardown`` was passed, call ``ec2.shutdown_instance()``. This
   runs in a ``finally`` block, so it still fires if the sweep raised.
   WITHOUT the flag (the default), nothing is torn down: under the fleet,
   the supervisor owns instance lifecycle end-to-end, and shuts the box
   down itself once it has finished with this lane (see
   ``scripts/run_fleet.py``'s module docstring, "Phases and the
   reuse-then-shutdown lifecycle"). ``--teardown`` exists purely for
   STANDALONE use: a solo smoke test of this file with nothing else
   depending on the box.

S3 SPOOL (``spool_to_s3``) -- END-OF-RUN ONLY, a documented limitation
--------------------------------------------------------------------------
``spool_to_s3`` is called exactly ONCE, after ``runner.sweep`` returns.
``runner.sweep``'s full signature and config-key list expose NO progress
hook, no per-cell callback, and no way to observe partial completion from
outside the call. It is a single blocking call that returns only when the
whole sweep finishes (or raises an unrecoverable exception). An
incremental, every-N-cells sync would need a new callback parameter on
``runner.sweep`` itself -- a change to
``smolbench/deduction/lean/runner.py``, and therefore explicitly OUT OF
SCOPE for this file (a sibling module owns that file; this file must not
touch it). So every replicate this lane collects sits on local disk for
the full sweep, and reaches S3 only at the very end. A crash mid-sweep
means whatever the sweep already wrote to ``all_rows.jsonl`` on local disk
stays unspooled until a later call reaches this point again. Even so, a
RELAUNCH of this same lane picks up where the crash left off, because
``runner.sweep`` has its own on-disk ``all_rows.jsonl``/resume mechanism
(see ``runner.sweep``'s ``resume`` parameter) -- independent of whether
anything was ever spooled.

Cost warning
------------
``ec2.provision_spot_instance()`` and ``ec2.serve_model()`` make LIVE AWS
calls against a self-provisioned (or reattached) EC2 spot instance. AWS
bills for the whole time it stays up. Running this file standalone
(``LEAN_MODEL`` set by hand, no fleet) provisions or reattaches to exactly
one box for exactly one checkpoint. Running it under the fleet does this
up to 21 times concurrently, one subprocess per lane. Either way, this is
real GPU spend. Verify ``LEAN_MODEL`` before you invoke this file outside
the fleet, and verify ``LEAN_STATE_FILE`` too if you care about reattaching
versus launching fresh.

Environment
-----------
``LEAN_MODEL``
    Required. A single spec key from ``MODELS`` (e.g. ``"glm-4.7"``): the
    ONE checkpoint this invocation serves and sweeps against.
``LEAN_STATE_FILE``
    Optional. A bare filename or absolute path for this lane's EC2 state
    file. When unset (the default), this driver derives
    ``.ec2_state_scaling_<LEAN_MODEL>.json`` under ``REPO_ROOT``. The fleet
    supervisor passes a bare filename here (see ``scripts/run_fleet.py``'s
    ``Lane.state_file``), specifically so this driver reattaches to the box
    its own induction phase already provisioned: both phases resolve the
    SAME bare filename against the SAME repo root.
``LEAN_RUN_NAME``
    Optional. Overrides ``build_config``'s ``run_name`` (default
    ``f"scaling_{LEAN_MODEL}"``). Read at ``build_config`` call time, not
    at import time.
``LEAN_SHARD``
    Optional. A stride string ``"i/n"`` (e.g. ``"0/4"``) that splits this
    study's theorem pool across concurrent shard processes. Read at
    ``build_config`` call time. When set, ``build_config`` adds a
    ``"shard"`` key to the returned config's ``theorems`` dict, and the
    default ``run_name`` gains a ``_shard<i>of<n>`` suffix (an explicit
    ``LEAN_RUN_NAME`` still wins verbatim). See ``build_config``'s own
    docstring for the exact mechanics.
``LEAN_CELL_WHITELIST``
    Optional. A path to a cell-whitelist file. Read at ``build_config``
    call time. When set, ``build_config`` adds a ``"cell_whitelist"`` key
    to the returned config (the path plus a content hash), and
    ``runner.sweep`` reads this same variable itself to restrict which
    cells it generates. See ``build_config``'s own docstring, "LEAN_CELL_WHITELIST
    sidecar stamp" note, for why the config carries a hash and not just
    the path.
``LEAN_VERIFY``
    Optional, default ``"defer"``. See "VERIFIER SELECTION" above.

Run (repo root, main venv)::

    LEAN_MODEL=glm-4.7 .venv/bin/python notebooks/deduction/run_study.py
    LEAN_MODEL=glm-4.7 .venv/bin/python notebooks/deduction/run_study.py --teardown
"""

import argparse
import copy
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + S3-spool constants (pure; no environment or filesystem effects)
# ---------------------------------------------------------------------------
# This file is <repo>/notebooks/deduction/run_study.py, so parents[0] is
# .../notebooks/deduction, parents[1] is .../notebooks, and parents[2] is
# the repo root. This anchors via __file__, never the cwd, because the
# fleet, a notebook kernel, or a bare shell may launch this file from any
# working directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Same bucket and region ``scripts/run_fleet.py``'s own
#: ``sync_deduction_spool`` uses for the induction-phase results store.
#: This study's whole S3 footprint lives in one bucket. This value is a
#: plain literal (not imported from ``run_fleet``), so this file has no
#: dependency on that off-limits module.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
SPOOL_REGION: str = "us-west-2"
#: Differs from ``run_fleet.sync_deduction_spool``'s own
#: ``"deduction/runs"`` destination prefix in spelling only -- same value,
#: chosen independently here. This file owns its own spool contract end to
#: end (upload-verify-prune), instead of delegating to that off-limits
#: script.
SPOOL_PREFIX: str = "deduction/runs"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derive this lane's four ``EC2_*``/``SMOLBENCH_LEAN_RESULTS`` defaults.

    A PURE function. It reads only its own arguments, performs no
    filesystem or environment I/O, and returns a brand-new ``dict`` on
    every call. It stays pure on purpose: only the caller (this module's
    own top-level code) ever touches ``os.environ``, and tests can
    exercise the derivation logic with no process-environment dependency
    at all.

    Parameters
    ----------
    key : str
        Spec key for the checkpoint this lane serves (e.g. ``"glm-4.7"``).
        This function does NOT validate it against ``MODELS``. See the
        module docstring's "MODULE IMPORT ORDER" section for why
        validation waits for ``selected_model``, called later, after
        ``MODELS`` loads.
    repo_root : Path
        Repo root to anchor the derived state-file and results paths
        against. Callers pass ``REPO_ROOT`` in production; tests may pass
        anything.
    state_file : str or None, optional
        Override for the EC2 state-file location. ``None`` (the default)
        derives ``repo_root / f".ec2_state_scaling_{key}.json"``. A
        relative or bare string (e.g. the fleet supervisor's
        ``.ec2_state_scaling_<key>.json``) resolves AGAINST `repo_root`,
        not the process's cwd. This lets this lane reattach to the exact
        box its induction phase provisioned: both phases anchor the same
        bare filename to the same repo root. An absolute string is used
        verbatim.

    Returns
    -------
    dict[str, str]
        Exactly four keys:

        - ``"EC2_EXPERIMENT_TAG"``: ``f"scaling-{key}"``.
        - ``"EC2_STATE_FILE"``: absolute path string, derived as described
          above.
        - ``"EC2_VLLM_IMAGE"``: digest-pinned to the build the 2026-08-16
          determinism hinge experiment certified (see
          ``smolbench.evals.ec2.EC2_VLLM_IMAGE``'s own comment for the full
          provenance). This driver reattaches to a box already serving
          under that same image during the induction phase, so using any
          other image here would risk a mid-study image swap.
        - ``"SMOLBENCH_LEAN_RESULTS"``: ``str(repo_root / "notebooks" /
          "deduction" / "results")``. This function sets it EXPLICITLY,
          rather than leave it to ``runner.results_root()``'s own
          independent default (which happens to compute the same path via
          a different anchor, ``smolbench.__file__``). This keeps this
          file's output location decoupled from how the ``smolbench``
          package happens to be installed in a given environment.

    Notes
    -----
    This module's own top-level code installs every value here into
    ``os.environ`` via ``os.environ.setdefault`` (never a bare assignment).
    See the module docstring's "MODULE IMPORT ORDER" section for why it
    uses ``setdefault`` specifically, and why the four resulting
    ``os.environ`` writes must land before the first import of
    ``smolbench.evals.ec2``.

    Examples
    --------
    >>> sorted(lane_env_defaults("glm-4.7", repo_root=Path("/repo")))
    ['EC2_EXPERIMENT_TAG', 'EC2_STATE_FILE', 'EC2_VLLM_IMAGE', 'SMOLBENCH_LEAN_RESULTS']
    >>> lane_env_defaults("glm-4.7", repo_root=Path("/repo"))["EC2_EXPERIMENT_TAG"]
    'scaling-glm-4.7'
    """
    if state_file is None:
        resolved_state_file = repo_root / f".ec2_state_scaling_{key}.json"
    else:
        candidate = Path(state_file)
        resolved_state_file = candidate if candidate.is_absolute() else repo_root / candidate

    return {
        "EC2_EXPERIMENT_TAG": f"scaling-{key}",
        "EC2_STATE_FILE": str(resolved_state_file),
        "EC2_VLLM_IMAGE": "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7",
        "SMOLBENCH_LEAN_RESULTS": str(repo_root / "notebooks" / "deduction" / "results"),
    }


# ---------------------------------------------------------------------------
# Env setdefaults -- MUST run before smolbench.evals.ec2 is imported by
# anything (directly or transitively). See the module docstring's "MODULE
# IMPORT ORDER" section for the full mechanical justification.
# ---------------------------------------------------------------------------
# Read RAW, unvalidated. The table that would let us validate LEAN_MODEL
# (MODELS, loaded below) is not available yet. Validating it here would
# require loading that table first, which would import smolbench.evals.ec2
# too early. Validation waits for selected_model(), called later from
# main().
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # Use setdefault, NEVER a bare assignment: a value the fleet
        # supervisor (or an interactive shell) already exported into this
        # process's environment must always win over this file's own
        # default.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value

    # GUARD -- cross-lane box adoption. setdefault above means an
    # EC2_EXPERIMENT_TAG already in the environment WINS. This is correct
    # when a fleet supervisor overrides it per lane, but catastrophic when
    # the value is shared: boxes are discovered by tag whenever a state
    # file is absent (``_recover_tagged_instance``), so a second lane
    # started under the same tag ADOPTS the first lane's instance and
    # serves its own model on top of it. Rows generated after such a swap
    # get attributed to the wrong model.
    #
    # This is not hypothetical. keys.env ships
    # ``EC2_EXPERIMENT_TAG=scaling-standalone`` as a standalone-run safety
    # default, and a launcher that sources keys.env with ``set -a`` exports
    # it into every lane. On 2026-08-14 three lanes (exaone-4.5-33b,
    # gemma-4-31b, deepseek-v3.1) converged on one g6e.12xlarge this way. We
    # caught it because the instance was tagged scaling-standalone rather
    # than scaling-<key>, before any row was written.
    #
    # A lane's tag must name its lane. Fail loudly, rather than let a run
    # produce mislabelled data.
    _TAG = os.environ.get("EC2_EXPERIMENT_TAG", "")
    if _RAW_LEAN_MODEL not in _TAG:
        raise SystemExit(
            f"EC2_EXPERIMENT_TAG={_TAG!r} does not name this lane's model "
            f"({_RAW_LEAN_MODEL!r}).\n"
            "Two lanes sharing a tag will adopt each other's EC2 instance and "
            "generate rows under the wrong model.\n"
            "Most likely cause: a launcher sourced notebooks/deduction/keys.env "
            "with `set -a`, exporting its standalone default and overriding the "
            "per-lane value this driver would otherwise install.\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        )
    del _TAG
# else: LEAN_MODEL is unset/empty. Deriving a tag/state-file from an
# empty key (e.g. "scaling-") would be actively misleading, with no
# benefit: selected_model() (called later, from main()) raises an
# actionable SystemExit for exactly this case, before anything else in
# this module's runtime path does real work. So this file simply skips
# the whole setdefault block, instead of seeding it with a placeholder
# key.

# ---------------------------------------------------------------------------
# Load notebooks/induction/run_study.py BY FILE PATH -- the single source
# of truth for MODELS / COT_ARGS. Never use a bare `import run_study`:
# this repo's own deduction and induction trees each ship a same-named
# run_study.py, so a bare module-name import would be ambiguous the
# moment both are ever on sys.path in the same process. That is exactly
# the situation scripts/run_fleet.py is already in, and it uses this same
# by-path pattern for the same reason.
# ---------------------------------------------------------------------------
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# MUST register in sys.modules BEFORE exec_module. On Python 3.14, a
# @dataclass decorator applied inside a module object not yet present in
# sys.modules raises `AttributeError: 'NoneType' object has no attribute
# '__dict__'` (some dataclass-machinery introspection resolves the
# defining module by looking it up in sys.modules by name). Without this
# line, the loaded module hits that same error at its first @dataclass.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key -> short analysis tag. Imported, never re-declared -- see the
#: module docstring's "WHAT THIS IS" section.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key -> per-request CoT-toggle kwargs, TOTAL over MODELS. Imported,
#: never re-declared.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# ---------------------------------------------------------------------------
# Late imports: safe only now that (a) our own EC2_* setdefaults have
# landed, and (b) MODELS/COT_ARGS are bound. noqa: E402 matches
# notebooks/induction/run_study.py's own late-import convention, for the
# same reason: these imports are intentionally not at the top of the
# file.
# ---------------------------------------------------------------------------
from smolbench.evals import ec2  # noqa: E402
from smolbench.deduction.lean import runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolve and validate this lane's model key from ``LEAN_MODEL``.

    This is the deferred-validation counterpart to the raw, unvalidated
    read at module-import time (``_RAW_LEAN_MODEL``). By the time this
    function runs, ``MODELS`` is guaranteed to be loaded. So the check
    that could not happen at import time (see the module docstring's
    "MODULE IMPORT ORDER" section) happens here instead.

    Returns
    -------
    str
        The validated spec key, a member of ``MODELS``.

    Raises
    ------
    SystemExit
        If ``LEAN_MODEL`` is unset or empty, or if it does not name a key
        of ``MODELS``. Both messages list every valid key (sorted). This
        makes the failure actionable without opening this file to look up
        the roster.
    """
    key = os.environ.get("LEAN_MODEL", "").strip()
    valid = ", ".join(sorted(MODELS))
    if not key:
        raise SystemExit(
            "LEAN_MODEL is unset (or empty). This driver serves exactly ONE "
            f"checkpoint per invocation. Set it to one of: {valid}"
        )
    if key not in MODELS:
        raise SystemExit(f"LEAN_MODEL={key!r} is not a known spec key. Valid keys: {valid}")
    return key


def build_config(key: str) -> dict:
    """Build this lane's ``runner.sweep`` configuration.

    USER-LOCKED values. By design, every key below is identical across all
    21 checkpoints in this study, except ``run_name`` and the per-model
    ``models[0]`` entry. Holding the sweep fixed, and varying only the
    served model, is what lets a next-tactic success-rate difference
    between two checkpoints point to the model, not to a changed sweep.
    This function does not rename, adapt, or re-derive any key from
    ``runner.sweep``'s defaults: ``runner.sweep`` already accepts every one
    of them verbatim (see its own docstring's "Config keys" section).

    Parameters
    ----------
    key : str
        Spec key for the checkpoint this lane serves. Callers must
        validate it first (e.g. via ``selected_model()``): ``COT_ARGS[key]``
        raises a plain ``KeyError`` for a key outside ``MODELS``, since
        ``COT_ARGS`` is TOTAL over ``MODELS`` by construction (see
        ``notebooks/induction/run_study.py``'s own docstring). This
        function does not re-check that invariant.

    Returns
    -------
    dict
        A sweep config with 16 keys: ``run_name``, ``seed``,
        ``temperature``, ``max_tokens``, ``request_timeout``,
        ``max_retries``, ``dojo_timeout``, ``concurrent_gen``,
        ``skip_trivial``, ``k``, ``n_replicates``, ``theorems``, ``rungs``,
        ``theorem_workers``, ``max_concurrency``, ``models``. ``theorems``
        contains the five keys ``source``, ``kind``, ``split``, ``limit``,
        ``seed`` (the ``replay_passing``/``novel_premises``/``val`` pool,
        300 of its 805 theorems, itself seeded 0). It also has a sixth
        key, ``shard``, present ONLY when ``LEAN_SHARD`` is set in the
        environment at call time (see the comment above the ``theorems``
        assignment in this function's body for the sharding mechanics).
        ``models`` is a single-element list; its ``extra_params`` is a
        DEEP COPY of ``COT_ARGS[key]`` (see Notes), so it is always equal
        to, but never the same object as, ``COT_ARGS[key]``. A seventeenth
        key, ``cell_whitelist``, is present ONLY when
        ``LEAN_CELL_WHITELIST`` is set in the environment at call time
        (see the "LEAN_CELL_WHITELIST sidecar stamp" note below). With it
        unset, the returned dict's top-level key set is unchanged from
        before this parameter existed.

    Notes
    -----
    Pure, except for three environment reads at CALL time, never cached
    and never read at import time: ``LEAN_SHARD``, ``LEAN_RUN_NAME``, and
    ``LEAN_CELL_WHITELIST``. A caller may set any of them any time before
    calling this function.

    ``LEAN_SHARD`` (a stride string, e.g. ``"0/4"``), when set, adds a
    ``shard`` key to the ``theorems`` dict and appends a
    ``_shard<i>of<n>`` suffix to the DEFAULT ``run_name`` (see the comment
    above the ``theorems`` assignment in this function's body for why). An
    explicit ``LEAN_RUN_NAME`` still wins verbatim over that suffix.

    ``LEAN_RUN_NAME``, when unset or empty, falls back to
    ``f"scaling_{key}"`` (plus the shard suffix above, when present) --
    matching ``scripts/run_fleet.py``'s ``Lane`` naming convention for
    ``scaling_<model>`` run directories.

    Also reads ``LEAN_CELL_WHITELIST`` at CALL time and, when set,
    additionally performs FILE I/O (``runner.load_cell_whitelist`` reads
    and parses that path). This function is no longer pure in that
    branch, and can raise `ValueError` (propagated from
    `load_cell_whitelist`) before any AWS call -- matching this driver's
    established "fail fast before billing" pattern (see the module
    docstring's LIFECYCLE step 3).

    This function builds ``extra_params`` with
    ``copy.deepcopy(COT_ARGS[key])`` rather than reuse it by reference.
    ``COT_ARGS`` is a shared, imported table (see ``MODELS``/``COT_ARGS``
    above). If a caller mutates the returned config's ``extra_params`` in
    place (e.g. to layer on an ad hoc per-request override before calling
    ``runner.sweep``), that mutation must never corrupt the shared table
    for every OTHER lane still building a config in this same process. A
    shallow copy would not be enough here, because ``COT_ARGS`` values are
    themselves nested dicts (e.g.
    ``{"chat_template_kwargs": {"enable_thinking": True}}``).

    Examples
    --------
    >>> cfg = build_config("glm-4.7")
    >>> cfg["rungs"]
    ['stepk:1', 'hint:2', 'noise:3', 'hint:3']
    >>> cfg["models"][0]["extra_params"] == COT_ARGS["glm-4.7"]
    True
    >>> cfg["models"][0]["extra_params"] is COT_ARGS["glm-4.7"]
    False
    """
    # Optional theorem-stride shard ("i/n", passed through to
    # runner._select_theorems). The shard key is CONDITIONALLY present.
    # When LEAN_SHARD is unset, the theorems block stays byte-identical to
    # the unsharded study config. When sharding, the DEFAULT run_name
    # gains a _shard<i>of<n> suffix. This stops two concurrently running
    # shards from sharing a run directory: concurrent appends to one
    # all_rows.jsonl from separate processes interleave large rows and
    # corrupt the file. An explicit LEAN_RUN_NAME still wins verbatim, so
    # a caller overriding it for a sharded launch owns that uniqueness
    # themselves.
    shard = os.environ.get("LEAN_SHARD", "").strip()
    shard_suffix = ""
    if shard:
        shard_suffix = "_shard" + shard.replace("/", "of")
    run_name = os.environ.get("LEAN_RUN_NAME", "").strip() or f"scaling_{key}{shard_suffix}"
    theorems: dict[str, Any] = {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }
    if shard:
        theorems["shard"] = shard

    cfg: dict[str, Any] = {
        "run_name": run_name,
        "seed": 0,
        "temperature": 0.7,
        "max_tokens": 32768,
        "request_timeout": 1800,
        "max_retries": 2,
        "dojo_timeout": 300,
        "concurrent_gen": True,
        "skip_trivial": True,
        "k": {"strategy": "last"},
        "n_replicates": 1,
        "theorems": theorems,
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
        "theorem_workers": 4,
        "max_concurrency": 8,
        "models": [
            {
                "provider": "ec2",
                "model": key,
                "display_name": key,
                "extra_params": copy.deepcopy(COT_ARGS[key]),
            }
        ],
    }

    # Optional LEAN_CELL_WHITELIST sidecar stamp -- CONDITIONALLY present,
    # mirroring the shard key above. Unlike `shard`, this value does NOT
    # drive `runner.sweep`'s own behavior: `runner.sweep` reads
    # `LEAN_CELL_WHITELIST` directly from the environment itself (see that
    # function's docstring). This function writes this key purely so the
    # run's `manifest.json` sidecar (`sweep` stamps `{"config": config,
    # ...}` verbatim -- see that function's "Output layout" docstring
    # section) records WHICH whitelist file was in effect for this run,
    # without embedding the (possibly large) key list a second time.
    # Recording the path alone would not be enough, because a whitelist
    # file can be edited or replaced after a run starts. So
    # `runner.hash_cell_keys` fingerprints its SORTED content instead. A
    # reader can diff `sha256` against a fresh
    # `hash_cell_keys(runner.load_cell_whitelist(path))` call to confirm
    # the file on disk is the exact one this run used.
    # `runner.load_cell_whitelist` itself raises loudly on a missing or
    # malformed file, so an operator gets that failure HERE, before any
    # AWS call -- see this function's own Notes section.
    whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    if whitelist_path:
        cfg["cell_whitelist"] = {
            "path": whitelist_path,
            "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(whitelist_path)),
        }

    return cfg


def select_verifier() -> Any:
    """Resolve the verifier object to hand to ``runner.sweep``, from ``LEAN_VERIFY``.

    Returns
    -------
    Any
        ``NullVerifier()`` when ``LEAN_VERIFY`` is unset, empty, or
        ``"defer"`` (the default). Every cell's proof-checking verdict is
        then recorded as ``"unverified"``, instead of replayed against a
        real Dojo session -- see the module docstring's "VERIFIER
        SELECTION" section for why this is the normal path for THIS
        driver (the main venv cannot import the real verifier at all).
        The ``smolbench.deduction.lean.verify`` MODULE object (not an
        instance -- ``runner.sweep`` calls its functions directly, e.g.
        ``verifier.try_tail(...)``) when ``LEAN_VERIFY`` is exactly
        ``"real"`` AND the interpreter is below Python 3.13. In practice
        that means the dedicated ``.venv-lean`` environment, pinned to
        Python 3.12 (see ``pyproject.toml``).

    Raises
    ------
    SystemExit
        - ``LEAN_VERIFY="real"`` under Python >= 3.13: ``verify.py``
          requires ``lean_dojo``, which pins ``python<3.13`` and is only
          installable in the dedicated ``.venv-lean`` environment (Python
          3.12). This function checks the version BEFORE attempting the
          import, instead of letting ``verify.py``'s own ``ImportError``
          propagate, so the message can name this driver's actual normal
          path: run with ``LEAN_VERIFY=defer`` (generation only), then
          verify separately, later, under ``.venv-lean`` via
          ``scripts/lean_verify_rows.py``.
        - Any other value: the message names the two valid values
          (``"defer"``, ``"real"``).

    Notes
    -----
    The ``from smolbench.deduction.lean import verify`` import lives
    INSIDE this function's ``"real"`` branch, not at module scope.
    A module-scope import here would make importing THIS file itself
    fail under Python 3.14 (the main venv this driver normally runs on),
    because ``verify.py`` unconditionally imports ``lean_dojo`` at its own
    module top level. The version guard above runs BEFORE this function
    attempts that import, so a 3.14 interpreter never reaches the import
    line at all.
    """
    choice = os.environ.get("LEAN_VERIFY", "defer").strip() or "defer"
    if choice == "defer":
        return NullVerifier()
    if choice == "real":
        if sys.version_info >= (3, 13):
            raise SystemExit(
                "LEAN_VERIFY=real requires the 'lean_dojo' package, which pins "
                "python<3.13 and is only installable in the dedicated "
                ".venv-lean environment (Python 3.12); this interpreter is "
                f"{sys.version_info.major}.{sys.version_info.minor}. The normal "
                "path for this driver is LEAN_VERIFY=defer (generation only, "
                "the default) followed by a separate verification pass under "
                ".venv-lean via scripts/lean_verify_rows.py."
            )
        from smolbench.deduction.lean import verify  # local: only reachable under .venv-lean

        return verify
    raise SystemExit(f"LEAN_VERIFY={choice!r} is not valid; expected 'defer' or 'real'.")


def spool_to_s3(run_dir: Path, key: str, *, client: Any = None) -> int:
    """Upload one lane's run directory to S3, verify it, then prune local disk.

    END-OF-RUN ONLY: this function runs exactly once, after
    ``runner.sweep`` has already returned (see ``main``). ``runner.sweep``'s
    full signature and documented config-key list expose no progress hook
    and no per-cell callback. It is one blocking call from start to
    finish. So this file cannot implement an incremental, every-N-cells
    sync without adding such a hook to
    ``smolbench/deduction/lean/runner.py`` itself -- out of scope here,
    since this file must not touch that module. This is a documented
    limitation, not an oversight. A crash mid-sweep means whatever
    ``all_rows.jsonl`` already holds on local disk stays there, unspooled,
    until a relaunch of this same lane reaches this call again.

    Parameters
    ----------
    run_dir : Path
        The sweep's output directory (``runner.results_root() / "runs" /
        run_name``).
    key : str
        Spec key for the checkpoint this run belongs to. Used to build
        the S3 destination prefix, ``f"{SPOOL_PREFIX}/scaling_{key}/"``.
        This function builds the prefix from `key`, not from
        ``run_dir.name``, on purpose. The two normally agree
        (``build_config``'s default ``run_name`` IS ``f"scaling_{key}"``),
        but ``LEAN_RUN_NAME`` can override ``run_name`` independently. The
        S3 layout must stay keyed on the MODEL, regardless of what a
        caller named the run directory.
    client : Any, optional
        A boto3 S3 client exposing ``upload_file`` and ``head_object``.
        ``None`` (the default) makes this function lazily import ``boto3``
        INSIDE itself, and build a real client against `SPOOL_REGION`.
        boto3 is never imported at module scope, so importing this file
        needs no AWS SDK at all (this mirrors ``smolbench.evals.ec2``'s
        own lazy-import convention, and ``scripts/run_fleet.py``'s
        ``sync_deduction_spool``, which follows the same pattern). This
        parameter exists so tests can inject a fake client with no network
        access.

    Returns
    -------
    int
        Number of files uploaded (and verified). Returns ``0``, with
        nothing uploaded or pruned, when `run_dir` is not a directory.
        This is NOT an error: a lane whose sweep produced nothing yet, or
        whose run directory a prior call already spooled and pruned,
        simply has nothing to sync.

    Raises
    ------
    RuntimeError
        If ANY upload fails verification: either ``head_object`` itself
        raised (network error, access denied, object briefly not yet
        consistent), or its ``"ContentLength"`` does not match the local
        file's size. The message names the offending S3 key and, when
        available, both the local and remote sizes (see Notes for the one
        case where a "remote size" does not exist to report). This
        function raises BEFORE any pruning: a failed verification must
        never delete local data, so on this path every file uploaded so
        far (verified or not) stays in place on disk, exactly as it was
        before this call.

    Notes
    -----
    Two-phase: upload-verify-ALL, then prune-ANY. This function collects
    the file list once, sorts it for deterministic ordering, then uploads
    and verifies every file in that fixed order. Pruning begins only
    after every single file has passed verification. This ordering is
    what makes the "do NOT prune anything on a failed verification"
    guarantee correct. If pruning were interleaved with upload and
    verify, a failure on file 10 of 20 would already have deleted files
    1-9 from local disk, with no guarantee those uploads were themselves
    still intact in the bucket.

    This resolves one message-wording ambiguity conservatively. The spec
    for this function says a RuntimeError on "any mismatch or exception"
    must name "the key and both sizes". For an actual SIZE MISMATCH, both
    sizes are always available, and this function reports both. For an
    EXCEPTION raised by ``head_object`` itself (e.g. the object briefly
    not found, a throttled call, a permissions error), there IS no
    "remote size" to report, because nothing was successfully retrieved.
    In that case this function reports the key, the local size, and the
    underlying exception's own message in place of a nonexistent remote
    size -- the closest available reading of "both sizes" when only one
    exists.

    Pruning deletes every uploaded file EXCEPT ``run_dir / "manifest.json"``
    (the run's config/run-id record, written by ``runner.sweep`` -- see
    that function's "Output layout" docstring section). It then removes
    every now-empty subdirectory, deepest-first (by path-segment count,
    so it only attempts a parent once every child under it is already
    clear). It swallows ``OSError`` on each ``rmdir()``: a non-empty
    directory (e.g. one holding a file this function does not manage) is
    simply left alone. ``run_dir`` itself is never removed, since it
    keeps ``manifest.json``.

    This function uses boto3's ``upload_file``/``head_object`` directly,
    not the ``aws`` CLI: the CLI is not a declared dependency of this
    repo, while boto3 already is.
    """
    if not run_dir.is_dir():
        logging.info(f"spool_to_s3[{key}]: no run directory at {run_dir}; nothing to sync.")
        return 0

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"{SPOOL_PREFIX}/scaling_{key}/"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file())

    # Phase 1: upload + verify EVERY file before deleting anything (see
    # docstring's "Two-phase" note for why this ordering is load-bearing).
    for path in files:
        rel = path.relative_to(run_dir).as_posix()
        dest_key = dest_prefix + rel
        client.upload_file(str(path), SPOOL_BUCKET, dest_key)

        local_size = path.stat().st_size
        try:
            head = client.head_object(Bucket=SPOOL_BUCKET, Key=dest_key)
            remote_size = head["ContentLength"]
        except Exception as exc:  # noqa: BLE001 -- re-raised below with actionable context
            raise RuntimeError(
                f"spool_to_s3[{key}]: could not verify upload of {dest_key!r} "
                f"(local size {local_size} bytes; head_object failed: {exc}); "
                "local data left intact, nothing pruned."
            ) from exc
        if remote_size != local_size:
            raise RuntimeError(
                f"spool_to_s3[{key}]: size mismatch verifying {dest_key!r}: "
                f"local={local_size} bytes, remote={remote_size} bytes; "
                "local data left intact, nothing pruned."
            )

    # Phase 2: every upload is verified, so pruning is now safe. This
    # keeps manifest.json so a later resume of this run recognises it
    # already exists, without re-downloading the whole spool from S3
    # first just to check.
    manifest_path = run_dir / "manifest.json"
    for path in files:
        if path != manifest_path:
            path.unlink()

    subdirs = sorted(
        (p for p in run_dir.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True
    )
    for subdir in subdirs:
        try:
            subdir.rmdir()
        except OSError:
            pass  # not empty -- fine, leave it

    logging.info(
        f"spool_to_s3[{key}]: uploaded and verified {len(files)} file(s) to "
        f"s3://{SPOOL_BUCKET}/{dest_prefix}"
    )
    return len(files)


def main(argv: list[str] | None = None) -> None:
    """Entry point: resolve the lane, provision/serve/sweep, spool, maybe teardown.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments to parse, or ``None`` (the default) to
        parse ``sys.argv`` as ``argparse`` normally would. This is a
        parameter so tests and notebook cells can call this function
        directly, without going through a subprocess.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        From argument parsing itself, from ``selected_model()`` (unset or
        unknown ``LEAN_MODEL``), or from ``select_verifier()`` (invalid or
        unsupported ``LEAN_VERIFY``). This function checks all three
        BEFORE any AWS call, so a configuration mistake never lands on a
        billing box.

    Notes
    -----
    This function makes live AWS calls (``ec2.provision_spot_instance()``,
    ``ec2.serve_model()``, and, with ``--teardown``,
    ``ec2.shutdown_instance()``) on every path except a failing argument
    parse or an early ``SystemExit`` from
    ``selected_model``/``select_verifier``. See the module docstring's
    "Cost warning" section.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Deduction-phase driver: serves ONE Lean theorem-proving "
            "checkpoint on one EC2 box and runs one runner.sweep of "
            "replicates against it."
        )
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        default=False,
        help=(
            "Terminate this lane's EC2 instance after the sweep (or after "
            "a failure) and exit. STANDALONE USE ONLY: under the fleet, "
            "the supervisor owns instance lifecycle and tears the box "
            "down itself once every phase scheduled for this lane has "
            "finished -- do not pass this flag from fleet-driven "
            "automation."
        ),
    )
    parser.add_argument(
        "--no-s3",
        action="store_true",
        default=False,
        help=(
            "Skip the end-of-run S3 spool sync (spool_to_s3) and leave "
            "this lane's replicate rows on local disk only."
        ),
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        default=False,
        help=(
            "Regenerate EVERY cell, including ones that already have a "
            "proof, and move the existing all_rows.jsonl aside first. For "
            "decontaminating a lane whose cells were generated on more "
            "than one hardware config -- resume alone cannot do this, "
            "because it (correctly) skips cells that already have content."
        ),
    )
    args = parser.parse_args(argv)

    key = selected_model()
    config = build_config(key)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    # Resolved -- and any SystemExit raised -- BEFORE provisioning: see the
    # module docstring's "LIFECYCLE" step 3.
    verifier = select_verifier()

    logging.info(
        f"main[{key}]: provisioning (idempotent -- reattaches to this "
        f"lane's live 'scaling-{key}'-tagged instance if one already "
        "exists, e.g. the one the induction phase provisioned; otherwise "
        "launches a fresh one) ..."
    )
    ec2.provision_spot_instance()

    n = 0
    try:
        with ec2.serve_model(key):
            # Provenance sidecar: snapshot the serving stack INSIDE the
            # serve block (the landed box is the one that generates), and
            # write it into run_dir so spool_to_s3 carries it with the
            # rows. One file per run, not per row: a deduction run serves
            # on one box unless it crashes. A relaunch APPENDS a fresh
            # timestamped snapshot instead of overwriting, so a resumed
            # run that landed on different hardware stays visible in the
            # log.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import datetime

                import yaml

                # mkdir first: runner.sweep creates run_dir itself, but
                # this sidecar writes BEFORE the sweep runs. (2026-08-14:
                # a missing mkdir crashed the first gemma deduction
                # relaunch.)
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            if args.force_rerun:
                # Move the old rows aside instead of appending on top of
                # them. With resume=False the sweep regenerates every
                # cell, but it still APPENDS to all_rows.jsonl. That would
                # leave both the superseded and the fresh row for each key
                # in one file, on different hardware, with nothing but
                # line order to tell them apart. Archiving removes that
                # confound, so it is part of the operation, not a
                # courtesy. The archive stays inside run_dir, so
                # spool_to_s3 carries it to S3 under its own key: this
                # preserves the superseded data and labels it plainly,
                # and never silently drops it.
                old = run_dir / "all_rows.jsonl"
                if old.exists():
                    import datetime

                    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                        "%Y%m%dT%H%M%SZ"
                    )
                    archived = run_dir / f"all_rows_SUPERSEDED-{stamp}.jsonl"
                    old.rename(archived)
                    logging.warning(
                        f"main[{key}]: --force-rerun: archived {old.name} -> "
                        f"{archived.name} ({archived.stat().st_size} bytes); "
                        "regenerating ALL cells on the current box."
                    )
            n = runner.sweep(
                config, run_dir, resume=not args.force_rerun, verifier=verifier
            )
        logging.info(f"main[{key}]: sweep wrote {n} cell row(s) to {run_dir}")
        if args.no_s3:
            logging.info(f"main[{key}]: --no-s3 set; leaving replicate rows on local disk.")
        else:
            spool_to_s3(run_dir, key)
    finally:
        # In the finally block so a lane launched with --teardown still
        # tears its box down even if the sweep itself raised -- see the
        # module docstring's "LIFECYCLE" step 7.
        if args.teardown:
            logging.info(f"main[{key}]: --teardown set; shutting down this lane's instance.")
            ec2.shutdown_instance()

    print(f"DEDUCTION LANE COMPLETE: {key} ({n} cell row(s)) run_dir={run_dir}", flush=True)


if __name__ == "__main__":
    main()
