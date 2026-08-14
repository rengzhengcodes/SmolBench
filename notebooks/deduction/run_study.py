"""Per-lane driver for the DEDUCTION side of the family-ladder scaling study.

WHAT THIS IS
------------
``notebooks/induction/run_study.py`` documents a 21-checkpoint family-ladder
scaling study (``MODELS``: 7 vendor families x 3 rungs each) run ONE MODEL
PER BOX under a fleet supervisor (``scripts/run_fleet.py``). That file
covers the INDUCTION phase. THIS file is the matching DEDUCTION-phase
driver: one invocation serves exactly ONE checkpoint on one EC2 box and runs
one ``smolbench.deduction.lean.runner.sweep`` (a Lean4 theorem-proving
sweep) against it. The fleet supervisor launches up to 21 of these as
subprocesses -- one per lane -- normally REATTACHING each lane to the same
box its induction phase already provisioned (same ``EC2_EXPERIMENT_TAG``,
same EC2 state file; see ``scripts/run_fleet.py``'s ``lane_env``), rather
than provisioning a second instance per model.

``MODELS`` (spec key -> short analysis tag) and ``COT_ARGS`` (spec key ->
per-request reasoning-toggle kwargs) are NOT re-declared here. They are
imported by file path from ``notebooks/induction/run_study.py``, which is
the single source of truth for this study's roster -- see "MODULE IMPORT
ORDER" below for exactly how and why.

MODULE IMPORT ORDER (load-bearing -- read this before editing anything else)
------------------------------------------------------------------------------
This file's top-level statements MUST execute in the following order. This
is the single most important property of this file: getting it wrong does
not raise an exception -- it silently makes this lane's EC2 tag / state
file / vLLM image drift onto whatever a fleet-supervisor-exported value, an
unrelated ``keys.env``, or ``smolbench.evals.ec2``'s own hardcoded defaults
happen to be, and that drift is only discoverable later, on a live billing
box, by noticing two lanes swapped each other's served checkpoint.

  1. Stdlib imports only (``argparse``, ``copy``, ``importlib.util``,
     ``logging``, ``os``, ``sys``, ``pathlib.Path``, ``typing.Any``).
  2. Compute ``REPO_ROOT`` and the S3-spool constants (pure arithmetic, no
     environment or filesystem side effects).
  3. Define ``lane_env_defaults`` (a pure function -- defining it has no
     side effects, but it must exist before step 4 calls it).
  4. Read the RAW ``LEAN_MODEL`` / ``LEAN_STATE_FILE`` strings from
     ``os.environ`` -- WITHOUT validating ``LEAN_MODEL`` against ``MODELS``
     yet, because ``MODELS`` is not loaded until step 6. Then, for every
     ``(name, value)`` pair ``lane_env_defaults`` derives from those raw
     strings, call ``os.environ.setdefault(name, value)`` -- ``setdefault``,
     NEVER a bare assignment, for every single one of the four variables, so
     a value the fleet supervisor already exported into this subprocess's
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

WHY this exact order, mechanically (verified against the current tree,
not asserted from memory of some other file's contents -- see the note
at the end of this section):

  * ``smolbench/evals/ec2.py`` reads ``EC2_EXPERIMENT_TAG``,
    ``EC2_VLLM_IMAGE``, ``EC2_INSTANCE_TYPES``, and ``EC2_REGIONS`` via
    ``os.getenv(...)`` at MODULE SCOPE and freezes each into a plain module
    constant. Once that module has been imported once by this process (and
    Python caches module imports in ``sys.modules``), those four values are
    fixed for the process's lifetime -- an ``os.environ`` write after that
    import has NO effect on them, however it is spelled. So our own
    ``setdefault`` calls (step 4) are only meaningful if they land before
    the FIRST import of ``smolbench.evals.ec2`` anywhere in this process
    (step 7, and transitively step 6 -- see below).
  * Step 6 loads ``notebooks/induction/run_study.py``, and that module's own
    top-level code calls ``load_dotenv(.../induction/keys.env)`` as a side
    effect (see that file's own module docstring) -- which in turn pulls in
    ``smolbench.induction.experiment``, which imports ``smolbench.evals.ec2``.
    That means step 6 is ALSO the first point ``ec2.py`` gets imported, so
    steps 4 and 6 must not be reordered.
  * ``load_dotenv`` there is called WITHOUT ``override=True`` (confirmed by
    reading that file directly, not assumed), so it can only fill in
    variables that are CURRENTLY UNSET in ``os.environ`` -- it can never
    clobber a value already present. That is exactly what makes
    "our setdefault first, then load that module" sufficient: whatever that
    ``keys.env`` does or does not set is irrelevant to variables we already
    set ourselves before that module is loaded.
  * A caveat worth stating plainly rather than leaving implicit: WHICH
    specific ``EC2_*`` keys ``notebooks/induction/keys.env`` sets is NOT a
    fact this file relies on or hardcodes anywhere -- that file is owned by
    a sibling study and its contents can and do change over time (verify
    with ``grep '^EC2_' notebooks/induction/keys.env`` if you need the
    CURRENT answer). The ordering above is correct regardless of what that
    file currently contains, precisely because it is derived from the two
    mechanisms above (import-time freezing + non-overriding ``load_dotenv``)
    and not from any particular snapshot of that file's keys.

SWEEP CONFIG (USER-LOCKED)
---------------------------
``build_config`` returns a fixed sweep configuration -- seed, decoding
params, the theorem pool selector, and the four rungs -- identical for
every one of the 21 checkpoints except ``model``/``display_name``/
``extra_params`` (which vary per checkpoint) and ``run_name`` (which varies
per lane). Holding everything else fixed is what makes a next-tactic
success-rate difference between two checkpoints attributable to the model
rather than to a changed sweep. See ``build_config``'s own docstring for the
exact keys and values, and for why they must never be renamed or re-derived
here (this driver adapts nothing -- every key is already accepted verbatim
by ``runner.sweep``).

VERIFIER SELECTION (``LEAN_VERIFY``, default ``"defer"``)
-------------------------------------------------------------
``runner.sweep`` never touches Lean directly -- every Dojo interaction goes
through an injected ``verifier`` object (see
``smolbench.deduction.lean.nullverify``'s module docstring, "Two-phase
workflow"). This driver runs on the MAIN venv (Python 3.14), which cannot
import ``smolbench.deduction.lean.verify`` at all (that module requires
``lean_dojo``, which pins ``python<3.13``). So by default
(``LEAN_VERIFY=defer``) this driver passes a ``NullVerifier()`` and produces
GENERATION-ONLY rows (every cell's verdict is ``"unverified"``); a separate,
later pass under ``.venv-lean`` replays and verifies those candidate proof
tails against the real Dojo. ``LEAN_VERIFY=real`` is provided for
completeness (so this same file can, in principle, drive a real verifying
sweep) but is only reachable under ``.venv-lean`` itself -- see
``select_verifier``'s docstring for the exact guard and error message.

LIFECYCLE (``main``)
---------------------
1. Resolve the lane's model key from ``LEAN_MODEL`` (``selected_model``,
   ``SystemExit`` if unset or unknown).
2. Build this lane's sweep config and compute its run directory.
3. Resolve the verifier (``select_verifier``) -- BEFORE provisioning, so a
   bad ``LEAN_VERIFY`` value aborts before any EC2 spend, matching the
   "fail fast before billing" pattern used throughout this study's tooling
   (see e.g. ``notebooks/induction/run_study.py``'s ``completion_budget``
   and ``scripts/run_fleet.py``'s ``preflight``, both of which run entirely
   before ``provision_spot_instance``).
4. ``ec2.provision_spot_instance()`` -- called with NO arguments, so its
   behavior is entirely governed by the ``EC2_INSTANCE_TYPES``/
   ``EC2_REGIONS`` frozen module constants (set from this process's
   environment, per the ordering above). Idempotent: reattaches to a live
   instance recorded under this lane's state file / experiment tag rather
   than launching a second one -- this is exactly how a deduction lane
   reattaches to the box its own induction phase already provisioned.
5. ``with ec2.serve_model(key): n = runner.sweep(config, run_dir, verifier=...)``.
6. Unless ``--no-s3``, spool the run directory to S3 (``spool_to_s3``).
7. If ``--teardown`` was passed, ``ec2.shutdown_instance()`` -- in a
   ``finally`` block, so it still runs if the sweep raised. WITHOUT the
   flag (the default), nothing is torn down: under the fleet, the
   supervisor owns instance lifecycle end-to-end and shuts the box down
   itself once it has finished with this lane (see
   ``scripts/run_fleet.py``'s module docstring, "Phases and the
   reuse-then-shutdown lifecycle"). ``--teardown`` exists purely for
   STANDALONE use (a solo smoke test of this file with nothing else
   depending on the box).

S3 SPOOL (``spool_to_s3``) -- END-OF-RUN ONLY, a documented limitation
--------------------------------------------------------------------------
``spool_to_s3`` is called exactly ONCE, after ``runner.sweep`` returns.
``runner.sweep``'s full signature and config-key list expose NO progress
hook, no per-cell callback, and no way to observe partial completion from
outside the call -- it is a single blocking call that returns only when the
whole sweep (or an unrecoverable exception) is done. An incremental,
every-N-cells sync would require adding a callback parameter to
``runner.sweep`` itself, which is a change to ``smolbench/deduction/lean/runner.py``
and therefore explicitly OUT OF SCOPE for this file (that module is owned
elsewhere and is not to be touched here). So every replicate this lane
collects sits on local disk for the full duration of the sweep and is
spooled to S3 only at the very end -- a crash mid-sweep loses whatever has
not yet reached ``all_rows.jsonl`` on disk to S3, though ``runner.sweep``'s
own on-disk ``all_rows.jsonl``/resume mechanism means a RELAUNCH of this
same lane picks up where the crash left off (see ``runner.sweep``'s
``resume`` parameter), independent of whether anything was ever spooled.

Cost warning
------------
``ec2.provision_spot_instance()`` and ``ec2.serve_model()`` are LIVE AWS
calls against a self-provisioned (or reattached) EC2 spot instance, billed
for the duration it is up. Running this file standalone (``LEAN_MODEL`` set
by hand, no fleet) provisions or reattaches to exactly one box for exactly
one checkpoint; running it under the fleet does this up to 21 times
concurrently, one subprocess per lane. Either way this is real GPU spend --
verify ``LEAN_MODEL`` (and, if you care about reattaching vs. launching
fresh, ``LEAN_STATE_FILE``) before invoking outside the fleet.

Environment
-----------
``LEAN_MODEL``
    Required. A single spec key from ``MODELS`` (e.g. ``"glm-4.7"``) --
    the ONE checkpoint this invocation serves and sweeps against.
``LEAN_STATE_FILE``
    Optional. A bare filename or absolute path for this lane's EC2 state
    file. Unset (the default) derives ``.ec2_state_scaling_<LEAN_MODEL>.json``
    under ``REPO_ROOT`` -- the fleet supervisor passes a bare filename here
    (see ``scripts/run_fleet.py``'s ``Lane.state_file``) specifically so
    this driver reattaches to the box its own induction phase already
    provisioned (both phases resolve the SAME bare filename against the
    SAME repo root).
``LEAN_RUN_NAME``
    Optional. Overrides ``build_config``'s ``run_name`` (default
    ``f"scaling_{LEAN_MODEL}"``). Read at ``build_config`` call time, not
    at import time.
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
# the repo root. Anchored via __file__, never the cwd -- this file may be
# launched (by the fleet, by a notebook kernel, by a bare shell) from any
# working directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: Same bucket/region ``scripts/run_fleet.py``'s own ``sync_deduction_spool``
#: uses for the induction-phase results store -- this study's whole S3
#: footprint lives in one bucket. Kept as a plain literal (not imported from
#: ``run_fleet``) so this file has no dependency on that off-limits module.
SPOOL_BUCKET: str = "smolbench-results-414266451290"
SPOOL_REGION: str = "us-west-2"
#: Distinct from ``run_fleet.sync_deduction_spool``'s own
#: ``"deduction/runs"`` destination prefix in spelling only -- same value,
#: chosen independently here because this file owns its own spool contract
#: end to end (upload-verify-prune) rather than delegating to that
#: off-limits script.
SPOOL_PREFIX: str = "deduction/runs"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derives this lane's four ``EC2_*``/``SMOLBENCH_LEAN_RESULTS`` defaults.

    A PURE function: reads only its own arguments, performs no filesystem
    or environment I/O, and returns a brand-new ``dict`` on every call.
    Kept pure deliberately so the caller (this module's own top-level code)
    is the ONLY thing that ever touches ``os.environ``, and so tests can
    exercise the derivation logic without any process-environment
    dependency at all.

    Parameters
    ----------
    key : str
        Spec key for the checkpoint this lane serves (e.g. ``"glm-4.7"``).
        NOT validated against ``MODELS`` here -- see the module docstring's
        "MODULE IMPORT ORDER" section for why validation must be deferred
        to ``selected_model``, called later, after ``MODELS`` is loaded.
    repo_root : Path
        Repo root to anchor the derived state-file and results paths
        against. Callers pass ``REPO_ROOT`` in production; tests may pass
        anything.
    state_file : str or None, optional
        Override for the EC2 state-file location. ``None`` (the default)
        derives ``repo_root / f".ec2_state_scaling_{key}.json"``. A
        relative/bare string (e.g. the fleet supervisor's
        ``.ec2_state_scaling_<key>.json``) is resolved AGAINST `repo_root`
        -- not the process's cwd -- which is what lets this lane reattach
        to the exact box its induction phase provisioned (both phases
        anchor the same bare filename to the same repo root). An absolute
        string is used verbatim.

    Returns
    -------
    dict[str, str]
        Exactly four keys:

        - ``"EC2_EXPERIMENT_TAG"``: ``f"scaling-{key}"``.
        - ``"EC2_STATE_FILE"``: absolute path string, derived as described
          above.
        - ``"EC2_VLLM_IMAGE"``: ``"vllm/vllm-openai:nightly"`` -- the image
          build that supports this study's 2026-generation architectures
          (see ``notebooks/induction/run_study.py``'s own module docstring
          for the per-architecture rationale; this driver reattaches to a
          box already serving under that same image during the induction
          phase, so using anything else here would risk a mid-study image
          swap).
        - ``"SMOLBENCH_LEAN_RESULTS"``: ``str(repo_root / "notebooks" /
          "deduction" / "results")`` -- set EXPLICITLY here rather than
          left to ``runner.results_root()``'s own independent default
          (which happens to compute the same path via a different anchor,
          ``smolbench.__file__``) so this file's output location is never
          silently coupled to how the ``smolbench`` package happens to be
          installed in a given environment.

    Notes
    -----
    Every value here is meant to be installed into ``os.environ`` via
    ``os.environ.setdefault`` (never a bare assignment) by this module's
    own top-level code -- see the module docstring's "MODULE IMPORT ORDER"
    section for why ``setdefault`` specifically, and why the four resulting
    ``os.environ`` writes must land before ``smolbench.evals.ec2`` is first
    imported.

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
        "EC2_VLLM_IMAGE": "vllm/vllm-openai:nightly",
        "SMOLBENCH_LEAN_RESULTS": str(repo_root / "notebooks" / "deduction" / "results"),
    }


# ---------------------------------------------------------------------------
# Env setdefaults -- MUST run before smolbench.evals.ec2 is imported by
# anything (directly or transitively). See the module docstring's "MODULE
# IMPORT ORDER" section for the full mechanical justification.
# ---------------------------------------------------------------------------
# Read RAW, unvalidated: the table that would let us validate LEAN_MODEL
# (MODELS, loaded below) is not available yet, and validating it here would
# require loading that table first -- which would import smolbench.evals.ec2
# too early. Validation is deferred to selected_model(), called later from
# main().
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # setdefault, NEVER a bare assignment: a value the fleet supervisor
        # (or an interactive shell) already exported into this process's
        # environment must always win over this file's own default.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value
# else: LEAN_MODEL is unset/empty. Deriving a tag/state-file from an empty
# key (e.g. "scaling-") would be actively misleading, and there is no
# benefit to it: selected_model() (called later, from main()) raises an
# actionable SystemExit for exactly this case before anything else in this
# module's runtime path does real work. So the whole setdefault block is
# simply skipped rather than seeded with a placeholder key.

# ---------------------------------------------------------------------------
# Load notebooks/induction/run_study.py BY FILE PATH -- the single source of
# truth for MODELS / COT_ARGS. Never a bare `import run_study`: this repo's
# own deduction and induction trees each ship a same-named run_study.py, so
# a bare module-name import would be ambiguous the moment both are ever on
# sys.path in the same process (exactly the situation scripts/run_fleet.py
# is already in, and it uses this same by-path pattern for the same reason).
# ---------------------------------------------------------------------------
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# MUST register in sys.modules BEFORE exec_module: on Python 3.14, a
# @dataclass decorator applied inside a module object that is not yet
# present in sys.modules raises `AttributeError: 'NoneType' object has no
# attribute '__dict__'` (some dataclass-machinery introspection resolves
# the defining module by looking it up in sys.modules by name). Skipping
# this line reproduces that error the moment the loaded module hits its
# first @dataclass.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key -> short analysis tag. Imported, never re-declared -- see the
#: module docstring's "WHAT THIS IS" section.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key -> per-request CoT-toggle kwargs, TOTAL over MODELS. Imported,
#: never re-declared.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# ---------------------------------------------------------------------------
# Late imports: only safe now that (a) our own EC2_* setdefaults have landed
# and (b) MODELS/COT_ARGS are bound. noqa: E402 matches
# notebooks/induction/run_study.py's own late-import convention, for the
# same reason (these imports are intentionally not at the top of the file).
# ---------------------------------------------------------------------------
from smolbench.evals import ec2  # noqa: E402
from smolbench.deduction.lean import runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolves and validates this lane's model key from ``LEAN_MODEL``.

    Deferred validation counterpart to the raw, unvalidated read performed
    at module-import time (``_RAW_LEAN_MODEL``) -- by the time this function
    runs, ``MODELS`` is guaranteed to be loaded, so the check that could not
    happen at import time (see the module docstring's "MODULE IMPORT ORDER"
    section) happens here instead.

    Returns
    -------
    str
        The validated spec key, a member of ``MODELS``.

    Raises
    ------
    SystemExit
        If ``LEAN_MODEL`` is unset or empty, or if it does not name a key
        of ``MODELS``. Both messages list every valid key (sorted), so the
        failure is actionable without opening this file to look up the
        roster.
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
    """Builds this lane's ``runner.sweep`` configuration.

    USER-LOCKED values: every key below except ``run_name`` and the
    per-model ``models[0]`` entry is identical across all 21 checkpoints in
    this study, by design -- holding the sweep fixed and varying only the
    served model is what makes a next-tactic success-rate difference
    between two checkpoints attributable to the model rather than to a
    changed sweep. None of these keys are renamed, adapted, or re-derived
    from ``runner.sweep``'s defaults: every one is already accepted
    verbatim by that function (see its own docstring's "Config keys"
    section).

    Parameters
    ----------
    key : str
        Spec key for the checkpoint this lane serves. Expected to already
        be validated (e.g. via ``selected_model()``) -- ``COT_ARGS[key]``
        raises a plain ``KeyError`` for a key outside ``MODELS``, since
        ``COT_ARGS`` is TOTAL over ``MODELS`` by construction (see
        ``notebooks/induction/run_study.py``'s own docstring) and this
        function does not re-validate that invariant.

    Returns
    -------
    dict
        A sweep config with keys ``run_name``, ``seed``, ``temperature``,
        ``max_tokens``, ``request_timeout``, ``max_retries``,
        ``dojo_timeout``, ``concurrent_gen``, ``skip_trivial``, ``k``,
        ``n_replicates``, ``theorems``, ``rungs``, ``theorem_workers``,
        ``max_concurrency``, ``models``. ``theorems`` contains EXACTLY the
        five keys ``source``, ``kind``, ``split``, ``limit``, ``seed`` (the
        ``replay_passing``/``novel_premises``/``val`` pool, 300 of its 805
        theorems, itself seeded 0). ``models`` is a single-element list;
        its ``extra_params`` is a DEEP COPY of ``COT_ARGS[key]`` (see
        Notes), so it is always equal to, but never the same object as,
        ``COT_ARGS[key]``.

    Notes
    -----
    Pure, except for reading ``LEAN_RUN_NAME`` from ``os.environ`` at CALL
    time (not cached, not read at import time) -- so a caller may set
    ``LEAN_RUN_NAME`` any time before calling this function. When unset or
    empty, ``run_name`` falls back to ``f"scaling_{key}"``, matching both
    ``scripts/run_fleet.py``'s ``Lane`` naming convention and
    ``smolbench.deduction.lean.figures``'s documented ``scaling_<model>``
    run-directory convention.

    ``extra_params`` is built with ``copy.deepcopy(COT_ARGS[key])`` rather
    than reused by reference: ``COT_ARGS`` is a shared, imported table (see
    ``MODELS``/``COT_ARGS`` above), and a caller mutating the returned
    config's ``extra_params`` in place (e.g. to layer on an ad hoc
    per-request override before calling ``runner.sweep``) must never be
    able to corrupt that shared table for every OTHER lane still to build
    a config in this same process. A shallow copy would not be enough here,
    since ``COT_ARGS`` values are themselves nested dicts (e.g.
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
    # runner._select_theorems). The shard key is CONDITIONALLY present:
    # LEAN_SHARD unset leaves the theorems block byte-identical to the
    # unsharded study config. When sharding, the DEFAULT run_name gains a
    # _shard<i>of<n> suffix so two concurrently running shards can never
    # share a run directory (concurrent appends to one all_rows.jsonl from
    # separate processes interleave large rows and corrupt the file); an
    # explicit LEAN_RUN_NAME still wins verbatim, so a caller overriding it
    # for a sharded launch owns that uniqueness themselves.
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
    return {
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


def select_verifier() -> Any:
    """Resolves the verifier object to hand to ``runner.sweep``, from ``LEAN_VERIFY``.

    Returns
    -------
    Any
        ``NullVerifier()`` when ``LEAN_VERIFY`` is unset, empty, or
        ``"defer"`` (the default): every cell's proof-checking verdict is
        recorded as ``"unverified"`` rather than replayed against a real
        Dojo session -- see the module docstring's "VERIFIER SELECTION"
        section for why this is the normal path for THIS driver (the main
        venv cannot import the real verifier at all). The
        ``smolbench.deduction.lean.verify`` MODULE object (not an instance
        -- ``runner.sweep`` calls its functions directly, e.g.
        ``verifier.try_tail(...)``) when ``LEAN_VERIFY`` is exactly
        ``"real"`` AND the interpreter is Python 3.12 (``.venv-lean``).

    Raises
    ------
    SystemExit
        - ``LEAN_VERIFY="real"`` under Python >= 3.13: ``verify.py``
          requires ``lean_dojo``, which pins ``python<3.13`` and is only
          installable in the dedicated ``.venv-lean`` environment (Python
          3.12). Checked BEFORE attempting the import (rather than letting
          ``verify.py``'s own ``ImportError`` propagate) so the message can
          name this driver's actual normal path: run with
          ``LEAN_VERIFY=defer`` (generation only) and verify separately,
          later, under ``.venv-lean`` via ``scripts/lean_verify_rows.py``.
        - Any other value: names the two valid values (``"defer"``,
          ``"real"``).

    Notes
    -----
    The ``from smolbench.deduction.lean import verify`` import lives INSIDE
    this function's ``"real"`` branch, not at module scope: importing it at
    module scope would make importing THIS file itself fail under Python
    3.14 (the main venv this driver normally runs on), since ``verify.py``
    unconditionally imports ``lean_dojo`` at its own module top level. The
    version guard above runs BEFORE this import is even attempted, so a
    3.14 interpreter never reaches the import line at all.
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
    """Uploads one lane's run directory to S3, verifies it, then prunes local disk.

    END-OF-RUN ONLY: this function is called exactly once, after
    ``runner.sweep`` has already returned (see ``main``). ``runner.sweep``'s
    full signature and documented config-key list expose no progress hook
    and no per-cell callback -- it is one blocking call from start to
    finish -- so an incremental, every-N-cells sync is not something this
    file can implement without adding such a hook to
    ``smolbench/deduction/lean/runner.py`` itself, which is out of scope
    here (that module is not to be touched by this file). This is a
    documented limitation, not an oversight: a crash mid-sweep means
    whatever ``all_rows.jsonl`` already holds on local disk stays there,
    unspooled, until a relaunch of this same lane reaches this call again.

    Parameters
    ----------
    run_dir : Path
        The sweep's output directory (``runner.results_root() / "runs" /
        run_name``).
    key : str
        Spec key for the checkpoint this run belongs to -- used to build
        the S3 destination prefix, ``f"{SPOOL_PREFIX}/scaling_{key}/"``.
        Deliberately built from `key`, not from ``run_dir.name``: the two
        normally agree (``build_config``'s default ``run_name`` IS
        ``f"scaling_{key}"``), but ``LEAN_RUN_NAME`` can override
        ``run_name`` independently, and the S3 layout must stay keyed on
        the MODEL regardless of what a caller named the run directory.
    client : Any, optional
        A boto3 S3 client exposing ``upload_file`` and ``head_object``.
        ``None`` (the default) lazily imports ``boto3`` INSIDE this
        function and builds a real client against `SPOOL_REGION` -- boto3
        is never imported at module scope, so importing this file needs no
        AWS SDK at all (mirrors ``smolbench.evals.ec2``'s own lazy-import
        convention, and ``scripts/run_fleet.py``'s
        ``sync_deduction_spool``, which follows the same pattern). This
        parameter exists so tests can inject a fake client with no network
        access.

    Returns
    -------
    int
        Number of files uploaded (and verified). ``0``, with nothing
        uploaded or pruned, when `run_dir` is not a directory -- NOT an
        error; a lane whose sweep produced nothing yet (or whose run
        directory was already fully spooled and pruned by a prior call)
        has nothing to sync.

    Raises
    ------
    RuntimeError
        If ANY upload fails verification -- either ``head_object`` itself
        raised (network error, access denied, object briefly not yet
        consistent) or its ``"ContentLength"`` does not match the local
        file's size. The message names the offending S3 key and, when
        available, both the local and remote sizes (see Notes for the one
        case where a "remote size" does not exist to report). Raised
        BEFORE any pruning -- a failed verification must never delete local
        data, so on this path every file uploaded so far (verified or not)
        is left in place on disk exactly as it was before this call.

    Notes
    -----
    Two-phase, upload-verify-ALL before pruning-ANY: the file list is
    collected once, sorted for deterministic ordering, then every file is
    uploaded and verified in that fixed order. Only after every single file
    has passed verification does pruning begin. This ordering is what makes
    the "do NOT prune anything on a failed verification" guarantee correct
    -- if pruning were interleaved with upload+verify, a failure on file 10
    of 20 would already have deleted files 1-9 from local disk with no
    guarantee those uploads were themselves still intact in the bucket.

    Verification failure message ambiguity, resolved conservatively: the
    spec for this function says a RuntimeError on "any mismatch or
    exception" must name "the key and both sizes". For an actual SIZE
    MISMATCH, both sizes are always available and both are reported. For an
    EXCEPTION raised by ``head_object`` itself (e.g. the object briefly not
    found, a throttled call, a permissions error), there IS no "remote
    size" to report -- nothing was successfully retrieved. In that case
    this function reports the key, the local size, and the underlying
    exception's own message in place of a nonexistent remote size, which is
    the closest available reading of "both sizes" when only one exists.

    Pruning deletes every uploaded file EXCEPT ``run_dir / "manifest.json"``
    (the run's config/run-id record, written by ``runner.sweep`` -- see
    that function's "Output layout" docstring section), then removes every
    now-empty subdirectory, deepest-first (by path-segment count, so a
    parent is only attempted once every child under it has already been
    cleared), swallowing ``OSError`` on each ``rmdir()`` (a non-empty
    directory -- e.g. one holding a file this function does not manage --
    is simply left alone). ``run_dir`` itself is never removed, since it
    keeps ``manifest.json``.

    Uses boto3's ``upload_file``/``head_object`` directly, not the ``aws``
    CLI: the CLI is not a declared dependency of this repo, while boto3
    already is.
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

    # Phase 2: every upload verified -- safe to prune. manifest.json is kept
    # so a later resume of this run recognises it already exists without
    # re-downloading the whole spool from S3 first just to check.
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
        Command-line arguments to parse, or ``None`` (the default) to parse
        ``sys.argv`` as ``argparse`` normally would. Exposed as a parameter
        so this function is callable from a test or notebook cell without
        going through a subprocess.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        From argument parsing itself, from ``selected_model()`` (unset or
        unknown ``LEAN_MODEL``), or from ``select_verifier()`` (invalid or
        unsupported ``LEAN_VERIFY``) -- all three checked BEFORE any AWS
        call, so a configuration mistake never lands on a billing box.

    Notes
    -----
    Live AWS calls (``ec2.provision_spot_instance()``, ``ec2.serve_model()``,
    and, with ``--teardown``, ``ec2.shutdown_instance()``) on every path
    except a failing argument parse or an early ``SystemExit`` from
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
            # serve block (the landed box is the one that generates) and
            # write it into run_dir so spool_to_s3 carries it with the
            # rows. One file per run, not per row -- a deduction run serves
            # on one box unless it crashes, and a relaunch APPENDS a fresh
            # timestamped snapshot rather than overwriting, so a resumed
            # run that landed on different hardware is visible in the log.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import datetime

                import yaml

                # mkdir first: runner.sweep creates run_dir itself, but this
                # sidecar writes BEFORE the sweep runs (2026-08-14: the
                # missing mkdir crashed the first gemma deduction relaunch).
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            n = runner.sweep(config, run_dir, verifier=verifier)
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
