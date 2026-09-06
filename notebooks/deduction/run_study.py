"""Per-lane driver for the DEDUCTION side of the family-ladder scaling study.

WHAT THIS IS: one invocation serves exactly ONE checkpoint on one EC2 box and
runs one ``smolbench.deduction.lean.runner.sweep`` against it. The fleet
supervisor (``scripts/fleet/run_fleet.py``) launches up to 21 of these, one per
lane; each reattaches to the box its induction phase already provisioned, by
reusing that phase's ``EC2_EXPERIMENT_TAG`` and state file.
``MODELS``/``COT_ARGS`` are loaded BY FILE PATH from
``notebooks/induction/run_study.py``, the roster's single source of truth.
The sweep's KNOB VALUES are likewise not literals in this file: they live in
``notebooks/deduction/sweep.yaml``, which ``build_config`` loads through
``runner.load_sweep_config`` and whose SHA-256 it stamps into the config, and
so into every run's ``manifest.json``. ``build_config`` stamps a SECOND
digest the same way, over
``smolbench/deduction/lean/decontam_config.toml``: that file's premise
stoplist decides which identifiers resolve to premise references, and so what
the ``hint:3``/``hint:4`` rungs contain, which makes it as much a part of a
run's provenance as the sweep knobs. What stays here is lane IDENTITY --
``run_name``, seeds, the served model, the optional shard and cell whitelist
-- overlaid on the loaded knobs.

MODULE IMPORT ORDER is load-bearing. ``smolbench.evals.providers.ec2`` freezes
``EC2_EXPERIMENT_TAG``, ``EC2_VLLM_IMAGE``, ``EC2_INSTANCE_TYPES`` and
``EC2_REGIONS`` into module constants at import time, so this file's
``os.environ.setdefault`` calls (from ``lane_env_defaults``) must land before
that module is first imported -- including transitively, via the induction
module's ``load_dotenv`` (no ``override=True``, so it never beats an already-set
value). Get the order wrong and nothing raises: this lane's tag, state file and
vLLM image silently drift, and two lanes swap served checkpoints on a live
billing box. ``setdefault``, never assignment, is what lets a fleet-exported
value win. The two ``smolbench`` imports that sit ABOVE that setdefault block
(``smolbench.evals.study_config``, for ``SPOOL_BUCKET``/``SPOOL_REGION``, and
``smolbench.evals.experiment``, for the GUARD's shared tag validation) are
allowed there only because both were VERIFIED ``ec2``-free: importing each in a
fresh interpreter leaves ``"smolbench.evals.providers.ec2"`` absent from
``sys.modules``. The comment beside them records each import's exact closure
and the two-line check; re-run it before adding a third.

Import raises ``SystemExit`` when ``EC2_EXPERIMENT_TAG`` is unsafe, applying
TWO complementary checks in this order (see the GUARD below). First the shared
``experiment.validate_experiment_tag``, which catches a tag that is empty or
whitespace-only, names a RETIRED study, or is the bare shared fleet prefix
naming every lane in the fleet at once. Then this driver's own EXACT
comparison against ``f"scaling-{LEAN_MODEL}"``, which is the only one of the
two that catches a well-formed tag belonging to a DIFFERENT live lane. Import
can also raise ``FileNotFoundError``, ``ValueError`` or
``tomllib.TOMLDecodeError`` out of the ``load_study_config()`` call behind
``SPOOL_BUCKET``/``SPOOL_REGION``: a missing or malformed committed study
config is a hard stop, never something to fall back from.

LIFECYCLE, in ``main`` order: (1) parse arguments; (2) resolve ``LEAN_MODEL``
and build the sweep config, loading ``notebooks/deduction/sweep.yaml`` and
overlaying this lane's identity on it -- this ALSO validates the corpus (see
``build_config``'s post-cutoff gate) and that sweep file (its reserved-key and
missing-key refusals) before any AWS call; (3) resolve
``LEAN_VERIFY`` -- steps 1-3 run BEFORE any AWS call, so a configuration
mistake never lands on a billing box; (4) compute this lane's outstanding-cell
set (see :func:`outstanding_cell_keys`) -- skipped, and treated as
unconditionally non-empty, under ``--force-rerun`` or when ``all_rows.jsonl``
does not exist yet -- and return NORMALLY, still BEFORE any AWS call, when it
is empty, so a lane with nothing left to do never provisions a box for
nothing; (5) provision (idempotent: reattaches); (6) serve the checkpoint;
(7) sweep, then spool to S3 once at the end; (8) tear down, from a
``finally`` and only under ``--teardown``, which is for STANDALONE runs
(under the fleet the supervisor owns instance lifecycle).
COST: steps 5-7 make live AWS calls, billed for as long as the box stays up.

Environment: ``LEAN_MODEL`` (required; one key of ``MODELS``);
``LEAN_STATE_FILE`` (optional EC2 state file, default
``.ec2_state_scaling_<LEAN_MODEL>.json`` -- a bare or relative name resolves
against ``REPO_ROOT``, which is how both phases find the same box);
``LEAN_RUN_NAME``, ``LEAN_SHARD`` (requires ``--no-s3``), ``LEAN_CELL_WHITELIST``
(optional, read at ``build_config`` call time, not at import); ``LEAN_CORPUS_KIND``
(default ``"random"``) and ``LEAN_CORPUS_SPLIT`` (default ``"val"``), also read
at ``build_config`` call time, select the split family within the active
post-cutoff corpus; ``LEAN_SEED`` (default ``0``, read at ``build_config``
call time -- see :func:`resolve_lean_seed`) drives BOTH theorem selection and
decoding from one knob, where they used to be two independent literals with
disagreeing library defaults; setting it to anything other than ``0``
re-draws the pinned 300-theorem sample and makes the run INCOMPARABLE with
the published lanes -- see that function's WARNING before touching it;
``LEAN_VERIFY`` -- ``"defer"`` (the
default) records every verdict ``"unverified"``, leaving real checking to the
later ``scripts/deduction/lean_verify_rows.py`` pass, while ``"real"`` verifies
inline (see :func:`select_verifier`).

Run (repo root)::

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

# These two `smolbench` imports MUST stay above the `os.environ.setdefault`
# block further down, because the constants and the GUARD that follow it both
# need them; they are deliberately NOT in the late `# noqa: E402` block, which
# sits below their consumers. Placing them here rather than lower also keeps
# them visually apart from that block: these carry no ordering hazard, and a
# reader must not mistake them for imports that do.
#
# VERIFIED ``ec2``-free, which is the only reason they may precede the
# setdefaults at all (module docstring, "MODULE IMPORT ORDER"). Check one
# module per fresh interpreter, since a shared one proves nothing about which
# import pulled what::
#
#     import sys, smolbench.evals.study_config   # then again for .experiment
#     assert "smolbench.evals.providers.ec2" not in sys.modules
#
# It passes for both. `study_config` pulls in only `smolbench`,
# `smolbench.evals`, `smolbench.evals.quiz` and `smolbench.evals.study_config`;
# `experiment` additionally pulls `smolbench.evals.{_aws,provider,replicates,
# results_store}` -- and `providers.ec2` from neither. Re-run that check before
# adding a THIRD smolbench import here: one that reached `ec2` would freeze
# this lane's EC2_* constants from the still-unseeded environment, and nothing
# would raise.
from smolbench.evals.experiment import validate_experiment_tag
from smolbench.evals.study_config import load_study_config

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Anchoring + S3-spool constants. No environment reads and no AWS calls, but
# NOT filesystem-free: the SPOOL_* pair parses the committed study config off
# disk at import time (see the note on those constants).
# ---------------------------------------------------------------------------
# parents[2] of <repo>/notebooks/deduction/run_study.py is the repo root.
# Anchored via __file__, never the cwd: the fleet, a notebook kernel or a bare
# shell may launch this file from anywhere.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: The bucket and region this lane spools its run directory to -- the study's
#: whole S3 footprint lives in one bucket, shared with the induction-phase
#: results store.
#:
#: These used to be hand-typed literals, justified by a comment saying they
#: were deliberately not imported from ``scripts/fleet/run_fleet.py`` so this
#: file would not depend on that module. That concern is still respected:
#: nothing here imports ``scripts/fleet``. The value simply comes from a
#: different place now -- the committed ``smolbench/evals/study_config.toml``,
#: which is shared CONFIG, not the fleet module. What the literal actually
#: cost was correctness rather than coupling: it was a second copy of a fact
#: with an owner elsewhere, and it could go stale in total silence.
#:
#: This is the same ``[results]`` section ``smolbench.evals.results_store``
#: reads -- VERIFIED: its ``default_results_uri`` and ``resolve_store`` both
#: call ``load_study_config().results`` -- so this driver can no longer spool
#: to a bucket the rest of the study does not read back. That config file's own
#: header additionally names ``smolbench/evals/providers/ec2.py``,
#: ``notebooks/induction/run_study.py`` and
#: ``notebooks/induction/analysis/power_analysis.py`` as consumers. It does NOT
#: name the fleet supervisor, so whether ``scripts/fleet/run_fleet.py`` reads
#: this same file is not something established here.
#:
#: Two ``load_study_config()`` calls rather than one bound temporary: that
#: loader is memoized on the RESOLVED config path, so the second call parses
#: nothing, and this leaves no import-time temporary needing a ``del`` (which
#: is what the guard below has to do with ``_TAG``).
SPOOL_BUCKET: str = load_study_config().results.bucket
SPOOL_REGION: str = load_study_config().results.region
#: The destination key prefix comes from ``runner.spool_prefix()``, resolved
#: at CALL time inside ``spool_to_s3`` and the GUARD in ``main`` below -- not
#: a module constant here, so a late ``LEAN_SPOOL_PREFIX`` override (or the
#: legacy-prefix refusal) takes effect per-invocation rather than at import.

#: The latest date any served checkpoint's WEIGHTS were published: the last
#: Hugging Face commit touching a weight file at the pinned `--revision` of
#: each roster lane (resolved 2026-08-30 via the HF tree API's per-file
#: lastCommit; gemma-4-12b's safetensors, revision 707f0a3b, is the max --
#: its later 07-20 commit only changed tokenizer_config.json). Weights cannot
#: encode data published after they were written, so this bounds every
#: knowledge cutoff from above and is the floor a post-cutoff corpus's
#: `target_date` must clear. See `build_config`'s corpus gate.
ROSTER_LATEST_RELEASE: str = "2026-06-03"


def lane_env_defaults(
    key: str, *, repo_root: Path, state_file: str | None = None
) -> dict[str, str]:
    """Derive this lane's four ``EC2_*``/``SMOLBENCH_LEAN_RESULTS`` defaults.

    Pure, so this module's top-level code stays the only thing touching
    ``os.environ`` (via ``setdefault``, before the first import of
    ``smolbench.evals.providers.ec2``). Does NOT validate `key` against
    ``MODELS``: that table is not loaded yet here -- see the module docstring's
    "MODULE IMPORT ORDER" section.

    Parameters
    ----------
    state_file : str or None
        ``None`` derives ``repo_root / f".ec2_state_scaling_{key}.json"``; a
        bare or relative name resolves against `repo_root`, NOT the process cwd
        -- both phases anchoring the same bare name to the same root is how
        this lane reattaches to induction's box. Absolute names are used as-is.

    Returns
    -------
    dict[str, str]
        ``EC2_EXPERIMENT_TAG`` (``f"scaling-{key}"``), ``EC2_STATE_FILE``
        (absolute), ``EC2_VLLM_IMAGE`` (digest-pinned; must match the image the
        induction phase serves under, or reattaching swaps images mid-study) and
        ``SMOLBENCH_LEAN_RESULTS`` (``repo_root/notebooks/deduction/results``,
        explicit so output location does not depend on how ``smolbench`` is
        installed).
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
# Env setdefaults -- MUST run before smolbench.evals.providers.ec2 is imported by
# anything (directly or transitively). See the module docstring's "MODULE
# IMPORT ORDER" section for the full mechanical justification.
# ---------------------------------------------------------------------------
# Read RAW, unvalidated: MODELS (loaded below) is the table that would validate
# LEAN_MODEL, and loading it here would import smolbench.evals.providers.ec2 too
# early. Validation waits for selected_model(), called later from main().
_RAW_LEAN_MODEL: str = os.environ.get("LEAN_MODEL", "").strip()
_RAW_LEAN_STATE_FILE: str | None = os.environ.get("LEAN_STATE_FILE") or None

if _RAW_LEAN_MODEL:
    for _env_name, _env_value in lane_env_defaults(
        _RAW_LEAN_MODEL, repo_root=REPO_ROOT, state_file=_RAW_LEAN_STATE_FILE
    ).items():
        # setdefault, NEVER a bare assignment: a value the fleet supervisor (or
        # an interactive shell) already exported must win over this default.
        os.environ.setdefault(_env_name, _env_value)
    del _env_name, _env_value

    # GUARD -- cross-lane box adoption. setdefault above lets an already-set
    # EC2_EXPERIMENT_TAG WIN, correct when a fleet supervisor overrides it per
    # lane but catastrophic when the value is SHARED: boxes are discovered by
    # tag whenever a state file is absent (`_recover_tagged_instance`), so a
    # second lane under the same tag ADOPTS the first's instance, serves its own
    # model on top of it, and every row after the swap is attributed to the
    # wrong model. keys.env's standalone `EC2_EXPERIMENT_TAG=scaling-standalone`
    # exported by a `set -a` launcher is how lanes end up sharing one; the raise
    # below spells out that cause and the fix.
    #
    # Two checks run below, and the ORDER is load-bearing rather than a style
    # choice. `validate_experiment_tag` is the shared structural validation the
    # induction leg already gets: it refuses an empty or whitespace-only tag, a
    # RETIRED study's tag, and the bare shared fleet prefix ("scaling-", or
    # "scaling" with the trailing dash dropped). It does NOT do the exact
    # lane-identity compare below -- read its body, not just its name: it
    # cannot, since it does not know this lane's model key.
    #
    # Every one of those three conditions would ALSO fail the exact compare,
    # which is precisely why the shared check must go first. Take the bare
    # prefix: the exact compare would reject it with a message about this
    # lane's tag, when the real condition is both different and far more
    # dangerous -- that tag names EVERY lane in the fleet at once, and fleet
    # teardown terminates BY TAG, so a run under it can take the whole fleet
    # down rather than collide with one box. The more specific diagnosis has to
    # be the one the operator sees.
    #
    # lane=None because this driver never appends a lane suffix to its tag: its
    # shard support goes into `run_name` (build_config's `shard_suffix`), never
    # into EC2_EXPERIMENT_TAG, so there is no suffix for the validator to
    # strip. No `retired=` override either -- the default already names the one
    # retired study, and overriding it here could only re-admit a tag that list
    # exists to refuse.
    _TAG = os.environ.get("EC2_EXPERIMENT_TAG", "")
    try:
        validate_experiment_tag(_TAG, None)
    except ValueError as exc:
        # Translated, never propagated. `main`'s docstring states this driver's
        # contract: a configuration mistake surfaces as SystemExit BEFORE any
        # AWS call, which is what every other guard here does (selected_model,
        # select_verifier, build_config's corpus gate, main's shard guard). The
        # shared validator is library code and signals with ValueError, which
        # would reach an operator as a traceback instead of a message. The
        # original text is re-raised verbatim and chained with `from exc`, so
        # the cause survives, plus the same actionable Fix line the exact-match
        # guard below already gives.
        #
        # The `except` cannot mis-label a CONFIG failure as a tag failure, even
        # though `validate_experiment_tag` internally loads the study config
        # (for the fleet tag prefix) and that load raises ValueError on a
        # malformed file. SPOOL_BUCKET above already forced that same memoized
        # load, on the same resolved path, to succeed -- and the loader
        # validates every section before returning -- so the validator's call
        # is a cache hit that cannot raise. Every ValueError arriving here is
        # one of the validator's own three refusals.
        raise SystemExit(
            f"{exc}\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        ) from exc

    # EXACT compare, never a substring test: spec keys nest ("glm-4.7" is a
    # prefix of "glm-4.7-flash"), so a containment check would accept the
    # NEIGHBOURING lane's tag and re-open exactly the adoption hole it guards.
    # This is also the check the shared validation above cannot make: a
    # neighbouring lane's tag is perfectly well-formed and passes it cleanly.
    if _TAG != f"scaling-{_RAW_LEAN_MODEL}":
        raise SystemExit(
            f"EC2_EXPERIMENT_TAG={_TAG!r} is not this lane's tag "
            f"('scaling-{_RAW_LEAN_MODEL}').\n"
            "Two lanes sharing a tag will adopt each other's EC2 instance and "
            "generate rows under the wrong model.\n"
            "Most likely cause: a launcher sourced notebooks/deduction/keys.env "
            "with `set -a`, exporting its standalone default and overriding the "
            "per-lane value this driver would otherwise install.\n"
            f"Fix: export EC2_EXPERIMENT_TAG=scaling-{_RAW_LEAN_MODEL} for this "
            "lane (or stop sourcing keys.env in the launcher)."
        )
    del _TAG
# else: LEAN_MODEL is unset/empty, so the whole setdefault block is skipped
# rather than seeded with a placeholder -- a tag like "scaling-" would be
# actively misleading, and selected_model() raises for this case before any real
# work happens.

# ---------------------------------------------------------------------------
# Load notebooks/induction/run_study.py BY FILE PATH -- the single source of
# truth for MODELS / COT_ARGS. A bare `import run_study` is ambiguous the moment
# both trees' same-named modules are on sys.path in one process, which is
# already scripts/fleet/run_fleet.py's situation (it uses this same pattern).
# ---------------------------------------------------------------------------
_INDUCTION_RUN_STUDY_PATH: Path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
_induction_spec = importlib.util.spec_from_file_location(
    "deduction_induction_run_study", _INDUCTION_RUN_STUDY_PATH
)
_induction = importlib.util.module_from_spec(_induction_spec)
# MUST register in sys.modules BEFORE exec_module: a @dataclass applied inside a
# module not yet in sys.modules raises `AttributeError: 'NoneType' object has no
# attribute '__dict__'`, because dataclass introspection resolves the defining
# module by sys.modules name lookup.
sys.modules[_induction_spec.name] = _induction
_induction_spec.loader.exec_module(_induction)  # runs that file's own load_dotenv(...) etc.

#: Spec key -> short analysis tag. Imported, never re-declared -- see the
#: module docstring's "WHAT THIS IS" section.
MODELS: dict[str, str] = _induction.MODELS
#: Spec key -> per-request CoT-toggle kwargs, TOTAL over MODELS. Imported, never
#: re-declared.
COT_ARGS: dict[str, dict] = _induction.COT_ARGS

# ---------------------------------------------------------------------------
# Late imports: safe only now that (a) our own EC2_* setdefaults have landed,
# and (b) MODELS/COT_ARGS are bound. Hence the noqa: E402 markers, as in
# notebooks/induction/run_study.py.
# ---------------------------------------------------------------------------
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.deduction.lean import corpus, decontam_config, runner  # noqa: E402
from smolbench.deduction.lean.nullverify import NullVerifier  # noqa: E402


def selected_model() -> str:
    """Resolve and validate this lane's model key from ``LEAN_MODEL``.

    Deferred counterpart to the raw, unvalidated import-time read: ``MODELS`` is
    guaranteed loaded by the time this runs. Raises ``SystemExit``, listing every
    valid key, if ``LEAN_MODEL`` is unset, empty or unknown.
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


def resolve_lean_seed() -> int:
    """Resolve the ONE seed shared by theorem selection and decoding, from ``LEAN_SEED``.

    Before this function existed, ``build_config`` wrote two independent seed
    literals with two different library defaults -- ``theorems["seed"]``
    (``runner._select_theorems``'s own default, 0) and ``cfg["seed"]``
    (``runner.sweep``'s own default, also 0, though it was 1776 when this
    study's config was first written) -- and neither was overridable although
    five neighbouring knobs (``LEAN_SHARD``, ``LEAN_RUN_NAME``,
    ``LEAN_CELL_WHITELIST``, ``LEAN_CORPUS_KIND``, ``LEAN_CORPUS_SPLIT``) were.
    This function is the single knob both now read, so "the experiment's seed"
    means one thing.

    Read at CALL time, like ``LEAN_CORPUS_KIND``/``LEAN_CORPUS_SPLIT`` --
    never at import and never cached -- so a caller can flip ``LEAN_SEED``
    between ``build_config`` calls within one process (as the test suite
    does) without re-importing this module.

    These two seeds do two DIFFERENT things, coupled only by sharing this one
    value:

    - ``theorems["seed"]`` feeds ``random.Random(seed).sample(pool, limit)``
      inside ``runner._select_theorems`` -- it decides WHICH theorems this
      lane measures.
    - ``cfg["seed"]`` is the decode seed ``runner.sweep`` puts on the wire;
      replicate ``i`` decodes at ``seed + i`` (see that function's "Seed
      threading" docstring paragraph).

    WARNING -- what changing this away from the default costs: a non-zero
    ``LEAN_SEED`` re-draws ``theorems["seed"]``'s sample, so the lane no
    longer measures ``notebooks/deduction/pinned_theorems.json``'s pinned 300
    theorems (that manifest's ``sha256_of_sorted_full_names`` was computed at
    seed 0, and ``tests/deduction/test_lean_pinning_audit.py`` pins that
    digest) and its results are NOT comparable with the published lanes that
    used the default. Do not set ``LEAN_SEED`` for anything other than a
    deliberate, clearly-labelled re-sampling experiment.

    Returns
    -------
    int
        ``0`` when ``LEAN_SEED`` is unset or blank (matching both
        ``runner._select_theorems``'s and ``runner.sweep``'s own defaults);
        otherwise the parsed integer, whatever sign or magnitude.

    Raises
    ------
    SystemExit
        ``LEAN_SEED`` is set to a non-integer string -- fails loudly rather
        than silently falling back to 0, since a typo here would otherwise
        look identical to an intentional, comparable run.
    """
    raw = os.environ.get("LEAN_SEED", "").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(
            f"LEAN_SEED={raw!r} is not a valid integer. This seed drives BOTH "
            "theorem selection (theorems.seed) and decoding (cfg.seed); unset "
            "it to use the pinned default (0), or set it to an integer."
        ) from None


# ---------------------------------------------------------------------------
# Sweep-config schema. This study's sweep KNOBS live in
# `notebooks/deduction/sweep.yaml`; what lives here is only the set of key
# NAMES `build_config` expects that file to define, and the set it refuses to
# let that file define at all.
# ---------------------------------------------------------------------------
#: This study's committed sweep-knob file. Anchored to `REPO_ROOT` like every
#: other path in this driver, never the cwd: the fleet, a notebook kernel or a
#: bare shell may launch this file from anywhere.
SWEEP_CONFIG_PATH: Path = REPO_ROOT / "notebooks" / "deduction" / "sweep.yaml"

#: SCHEMA guard, NOT a config table: only key NAMES live here, every VALUE
#: lives in `SWEEP_CONFIG_PATH`. `build_config` refuses a sweep file that is
#: missing any of these, because an absent key would instead fall through to
#: ``runner.sweep``'s own library default -- precisely the silent drift these
#: explicit values exist to prevent. ``runner.DEFAULT_DOJO_TIMEOUT``'s Design
#: comment spells out the worked example: this study's ``dojo_timeout: 300``
#: stays pinned at 300, independently of wherever that shared default moves,
#: ONLY because the config states it explicitly.
REQUIRED_SWEEP_KEYS: frozenset[str] = frozenset(
    {
        "temperature",
        "max_tokens",
        "request_timeout",
        "max_retries",
        "dojo_timeout",
        "concurrent_gen",
        "skip_trivial",
        "k",
        "n_replicates",
        "rungs",
        "theorem_workers",
        "max_concurrency",
        "theorems",
    }
)

#: The same SCHEMA guard one level down, inside the sweep file's ``theorems``
#: block. ``seed`` and ``shard`` are deliberately NOT here: they are lane
#: identity, and appear in `RESERVED_SWEEP_THEOREM_KEYS` instead.
REQUIRED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset(
    {"source", "kind", "split", "limit", "require_postcutoff"}
)

#: Keys the sweep file must NOT define, at top level. Each is per-lane
#: IDENTITY that `build_config` resolves from the environment at CALL time and
#: overlays on top of the loaded document, so a value written in the file
#: would be silently overwritten and have no effect whatsoever. Refusing them
#: is the difference between "the sweep file IS the config" and "the sweep
#: file is decoration": without this check a maintainer could set ``seed: 7``
#: there and get seed 0, with nothing raised and nothing logged.
RESERVED_SWEEP_KEYS: frozenset[str] = frozenset(
    {"run_name", "seed", "models", "cell_whitelist"}
)

#: The same refusal inside the sweep file's ``theorems`` block: ``seed`` comes
#: from `resolve_lean_seed` and ``shard`` from ``LEAN_SHARD``.
RESERVED_SWEEP_THEOREM_KEYS: frozenset[str] = frozenset({"seed", "shard"})


def _stamp_path(path: Path) -> str:
    """Spell `path` the way a manifest provenance stamp records it.

    REPO-RELATIVE whenever possible, never absolute: an absolute path would
    embed this box's checkout location in every archived manifest and make two
    boxes' manifests differ over nothing.

    Parameters
    ----------
    path : Path
        Any path, resolved or not; it is resolved here, so a caller need not.

    Returns
    -------
    str
        `path` relative to `REPO_ROOT` in POSIX form. A path OUTSIDE the repo
        has no repo-relative spelling at all, so it is returned as an absolute
        POSIX path instead -- reachable only through `build_config`'s
        ``sweep_config_path`` test seam, never in production.

    Notes
    -----
    Shared by both of `build_config`'s provenance stamps (``sweep_config`` and
    ``decontam_config``) so the two cannot drift apart in how they spell a
    path; that is the whole reason it is a function rather than two copies of
    a ``try``/``except ValueError`` block.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def build_config(key: str, *, sweep_config_path: Path | None = None) -> dict:
    """Build this lane's ``runner.sweep`` configuration: load the knobs, overlay the lane.

    TWO LAYERS. The study's sweep KNOBS are loaded from the committed
    ``notebooks/deduction/sweep.yaml`` (`SWEEP_CONFIG_PATH`) through
    ``runner.load_sweep_config`` -- the same loader ``cli.cmd_run_sweep``'s
    ``--config`` goes through, so this schema has one reader, not two. This
    lane's IDENTITY is then overlaid on a DEEP COPY of what was loaded:
    ``run_name``, ``seed``, ``models``, the ``theorems`` block's ``seed``,
    ``kind``/``split`` and optional ``shard``, an optional ``cell_whitelist``,
    and the ``sweep_config`` / ``decontam_config`` provenance stamps described
    under "Returns".

    USER-LOCKED: every key is identical across all 21 checkpoints except
    ``run_name`` and the single ``models[0]`` entry, which is what lets a
    next-tactic success-rate difference point to the model rather than a changed
    sweep. The sweep file is what now RECORDS that lock: its SHA-256 is stamped
    into every run's ``manifest.json``, so an archived run states which knob
    values it ran under, instead of that being recoverable only by diffing
    driver source at the matching commit. ``runner.sweep`` accepts every key
    verbatim. Callers must validate `key` first (e.g. ``selected_model()``):
    ``COT_ARGS`` is total over ``MODELS``, so any other key raises a bare
    ``KeyError``.

    Two refusals guard the loaded file, in this order -- the more dangerous
    condition is checked first, so a file that both adds a reserved key AND
    drops a knob is diagnosed by the reserved key:

    1. RESERVED keys -- any of `RESERVED_SWEEP_KEYS` at top level, or any of
       `RESERVED_SWEEP_THEOREM_KEYS` inside ``theorems`` -- raise
       ``SystemExit`` naming every offender. Each is resolved per-lane from the
       environment and would be silently overwritten by the overlay.
    2. MISSING keys -- any of `REQUIRED_SWEEP_KEYS`, then any of
       `REQUIRED_SWEEP_THEOREM_KEYS` -- raise ``SystemExit`` listing exactly
       which. A missing knob would fall through to ``runner.sweep``'s own
       library default instead of this study's pinned value.

    Performs corpus I/O (via `corpus.postcutoff_metadata`) and reads the sweep
    file, and can ``SystemExit`` -- see the "Post-cutoff corpus gate" paragraph
    below and the two refusals above. This makes `build_config` no longer a
    pure function of `key` and the environment already documented for the
    pre-existing knobs; it is still called BEFORE any AWS call (module
    docstring, LIFECYCLE step 2).

    Parameters
    ----------
    key : str
        Model spec key; must be one of ``MODELS``/``COT_ARGS`` (see above).
    sweep_config_path : Path or None, keyword-only
        TEST SEAM, used by nothing in production: ``None`` (the default) reads
        the committed `SWEEP_CONFIG_PATH`. It exists so a test can point this
        at a modified COPY of that file and exercise the two refusals above
        without editing the committed one. A path OUTSIDE the repo is stamped
        into ``sweep_config["path"]`` as an absolute path, since no
        repo-relative spelling of it exists.

    Post-cutoff corpus gate
    ------------------------
    Run at CALL time, not at import (importing this file must stay free of
    corpus I/O), and BEFORE the config dict is built:

    1. ``corpus.postcutoff_metadata()`` is None for an ordinary, pre-cutoff
       corpus (e.g. the original 2024-03-24 LeanDojo Benchmark 4 snapshot) --
       ``SystemExit``, naming `corpus.data_root()` and the corpus's traced
       commit (``corpus.metadata()["from_repo"]["commit"]``), pointing at
       ``scripts/deduction/build_postcutoff_corpus.py`` (Package B) as the fix.
    2. Otherwise the block's ``target_date`` is compared against
       `ROSTER_LATEST_RELEASE` with a plain string ``>=`` -- correct for ISO
       ``YYYY-MM-DD`` dates, where lexicographic order matches chronological
       order. Equality PASSES: a corpus targeted at exactly the roster's
       latest release date is compliant. A target date EARLIER than
       `ROSTER_LATEST_RELEASE` means some roster checkpoint may have already
       seen the corpus's "post-cutoff" theorems during training --
       ``SystemExit``, naming both dates.

    Returns
    -------
    dict
        A fresh dict, safe to mutate: the sweep file's 13 knob keys
        (`REQUIRED_SWEEP_KEYS`) DEEP-copied, plus the five this function
        always overlays -- ``run_name``, ``seed``, ``models``,
        ``sweep_config`` and ``decontam_config`` -- for 18 keys. The ``theorems`` block selects up to
        300 of the active post-cutoff corpus's
        ``replay_passing``/``<LEAN_CORPUS_KIND>``/``<LEAN_CORPUS_SPLIT>``
        pool's theorems at seed 0, with ``require_postcutoff: True`` so
        `runner._select_theorems` re-checks the corpus and every selected
        theorem at sweep time. ``models[0]["extra_params"]`` DEEP-copies
        ``COT_ARGS[key]``, so a caller's in-place mutation cannot corrupt that
        shared nested table for other lanes. ``sweep_config`` and
        ``decontam_config`` are the two provenance stamps, both spelled
        ``{"path": <repo-relative POSIX path>, "sha256": <digest of the
        file's raw bytes>}`` (see `_stamp_path`): the first fingerprints
        ``notebooks/deduction/sweep.yaml``, the second
        ``smolbench/deduction/lean/decontam_config.toml``, whose premise
        stoplist decides what the ``hint:3``/``hint:4`` rungs contain.
        ``decontam_config`` is COMPUTED here from a file the package ships,
        not read from the sweep file, which is why it is in neither
        `REQUIRED_SWEEP_KEYS` nor `RESERVED_SWEEP_KEYS`. Two further keys are
        conditional:
        ``theorems["shard"]`` under ``LEAN_SHARD`` and top-level
        ``cell_whitelist`` under ``LEAN_CELL_WHITELIST``.

    Notes
    -----
    ``LEAN_SHARD``, ``LEAN_RUN_NAME``, ``LEAN_CELL_WHITELIST``,
    ``LEAN_CORPUS_KIND``, ``LEAN_CORPUS_SPLIT`` and ``LEAN_SEED`` (the shared
    theorem-selection/decode seed; see :func:`resolve_lean_seed`) are all read
    at CALL time, never at import
    and never cached. ``run_name`` defaults to ``f"scaling_{key}"`` plus a
    ``_shard<i>of<n>`` suffix when sharding (matching
    ``scripts/fleet/run_fleet.py``'s ``Lane`` naming); an explicit
    ``LEAN_RUN_NAME`` wins verbatim. ``LEAN_CORPUS_KIND``/``LEAN_CORPUS_SPLIT``
    override the sweep file's ``theorems.kind``/``theorems.split``, which are
    the DEFAULTS a blank override falls back to. With ``LEAN_CELL_WHITELIST``
    set this also does file I/O and can raise ``ValueError`` from
    ``runner.load_cell_whitelist`` -- before any AWS call.

    The sweep file is re-read on EVERY call (``load_sweep_config`` is not
    memoized) and the result is deep-copied before anything is overlaid, so
    two calls share no nested structure: mutating one call's ``theorems``
    block or ``models[0]`` cannot reach the next call's.

    Raises
    ------
    SystemExit
        The active corpus is not post-cutoff, or its ``target_date`` is
        earlier than `ROSTER_LATEST_RELEASE` -- see "Post-cutoff corpus gate"
        above; or the sweep file defines a RESERVED key or is missing a
        REQUIRED one -- see the two refusals above.
    FileNotFoundError, ValueError, yaml.YAMLError
        Propagated from ``runner.load_sweep_config``: the sweep file is
        absent, is not a YAML mapping, or does not parse. Deliberately NOT
        translated into ``SystemExit`` -- these say the committed config is
        broken or gone, not that this lane was configured wrongly, and they
        reach an operator with the standard type and message.
    ValueError
        Also propagated from ``runner.load_cell_whitelist`` under
        ``LEAN_CELL_WHITELIST``.
    """
    # --- Post-cutoff corpus gate -- see the docstring above. Runs BEFORE the
    # config dict below is built, and before any AWS call anywhere in this
    # driver's lifecycle (module docstring, LIFECYCLE step 2).
    block = corpus.postcutoff_metadata()
    if block is None:
        raise SystemExit(
            f"{corpus.data_root()} (traced at commit "
            f"{corpus.metadata()['from_repo']['commit']}) is not a post-cutoff "
            "corpus. This study will not run on a pre-cutoff corpus -- every "
            "roster checkpoint's knowledge cutoff postdates the original "
            "LeanDojo Benchmark 4 snapshot, so its theorems are not a valid "
            "held-out set. Build a post-cutoff corpus with "
            "scripts/deduction/build_postcutoff_corpus.py (Package B) and "
            "point SMOLBENCH_LEAN_DATA at it."
        )
    # Plain string comparison is correct here: ISO YYYY-MM-DD dates sort
    # lexicographically in chronological order, so this needs no date parsing.
    if not (block["target_date"] >= ROSTER_LATEST_RELEASE):
        raise SystemExit(
            f"corpus target_date={block['target_date']!r} is earlier than "
            f"ROSTER_LATEST_RELEASE={ROSTER_LATEST_RELEASE!r}: a target date "
            "before the roster's latest release means some checkpoint may "
            "have already seen the corpus's \"post-cutoff\" theorems during "
            "training."
        )

    # --- Sweep knobs. This study's 13 knob values live in the committed
    # notebooks/deduction/sweep.yaml, not in this function: one reviewable
    # file, whose SHA-256 this function stamps into the config below so an
    # archived run records WHICH knob values it ran under. Loaded through the
    # SAME runner.load_sweep_config that cli.cmd_run_sweep's `--config` uses,
    # so the schema has exactly one reader.
    config_path = SWEEP_CONFIG_PATH if sweep_config_path is None else Path(sweep_config_path)
    loaded, sweep_config_sha256 = runner.load_sweep_config(config_path)

    # REFUSAL 1 -- RESERVED keys. Checked BEFORE the missing-key refusal, so a
    # file that both adds a reserved key and drops a knob is diagnosed by the
    # more dangerous of the two. `theorems` may be absent or not a mapping at
    # this point (that is the next refusal's business), so its sub-keys are
    # read defensively rather than indexed.
    loaded_theorems = loaded.get("theorems")
    loaded_theorem_keys = set(loaded_theorems) if isinstance(loaded_theorems, dict) else set()
    reserved = sorted(
        {name for name in RESERVED_SWEEP_KEYS if name in loaded}
        | {f"theorems.{name}" for name in RESERVED_SWEEP_THEOREM_KEYS & loaded_theorem_keys}
    )
    if reserved:
        raise SystemExit(
            f"{config_path}: reserved key(s) {', '.join(reserved)}.\n"
            "Each is per-lane IDENTITY, resolved at build_config call time from "
            "LEAN_RUN_NAME / LEAN_SEED / LEAN_MODEL / LEAN_SHARD / "
            "LEAN_CELL_WHITELIST and overlaid on top of this file, so a value "
            "set here would be SILENTLY OVERWRITTEN and have no effect at all.\n"
            "Fix: delete the key(s) from the file and set the matching "
            "environment variable instead."
        )

    # REFUSAL 2 -- MISSING knobs. Top level first: `theorems` is itself in
    # REQUIRED_SWEEP_KEYS, so by the time the sub-key check below runs, that
    # block is known to be present. A `theorems` block that IS present but is
    # not a mapping contributes no keys, and so reports all five sub-keys as
    # missing rather than raising an opaque AttributeError -- the message
    # still names exactly what the file has to state. Both lists are sorted,
    # so the message is reproducible.
    missing = sorted(REQUIRED_SWEEP_KEYS - set(loaded))
    if not missing:
        missing = sorted(
            f"theorems.{name}" for name in REQUIRED_SWEEP_THEOREM_KEYS - loaded_theorem_keys
        )
    if missing:
        raise SystemExit(
            f"{config_path}: missing required key(s) {', '.join(missing)}.\n"
            "Every knob this study pins must be stated explicitly: an absent key "
            "falls through to runner.sweep's own library default instead of this "
            "study's value, silently and with nothing recorded (see "
            "runner.DEFAULT_DOJO_TIMEOUT's Design comment for the worked example)."
        )

    # Optional theorem-stride shard ("i/n", passed to runner._select_theorems).
    # The key is CONDITIONALLY present, so an unsharded theorems block stays
    # byte-identical to the study config. Sharding also suffixes the DEFAULT
    # run_name, keeping two concurrent shards out of one run directory:
    # concurrent appends to one all_rows.jsonl from separate processes
    # interleave large rows and corrupt the file. An explicit LEAN_RUN_NAME
    # still wins verbatim, and then owns that uniqueness itself.
    shard = os.environ.get("LEAN_SHARD", "").strip()
    shard_suffix = ""
    if shard:
        shard_suffix = "_shard" + shard.replace("/", "of")
    run_name = os.environ.get("LEAN_RUN_NAME", "").strip() or f"scaling_{key}{shard_suffix}"
    # Theorem-selection seed and decode seed are the SAME knob -- see
    # resolve_lean_seed()'s docstring for the coupling and the cost of moving
    # it off its pinned default (0).
    seed = resolve_lean_seed()

    # DEEP copy, never the loader's return value itself and never a shallow
    # copy: every nested structure in it (`theorems`, `k`, `rungs`) has to be
    # private to THIS call, so a caller that mutates one returned config
    # cannot reach into the next call's. `models[0]["extra_params"]` below
    # applies the same rule to the shared COT_ARGS table.
    cfg: dict[str, Any] = copy.deepcopy(loaded)

    # --- Lane identity, overlaid on the loaded knobs. Each key assigned below
    # is either one the sweep file is REFUSED for defining (REFUSAL 1 above),
    # so the assignment cannot be quietly discarding a value a maintainer
    # meant to pin there, or -- theorems.kind/split -- one whose loaded value
    # is documented in that file as the DEFAULT an environment override
    # replaces.
    cfg["run_name"] = run_name
    # LEAN_SEED (default 0) -- the SAME value as theorems["seed"] below,
    # but a different role: this is the decode seed runner.sweep puts on
    # the wire (replicate `i` decodes at `seed + i`). One env var drives
    # both so "the experiment's seed" means one thing; see
    # resolve_lean_seed()'s docstring for the full
    # coupling and the WARNING about changing it.
    cfg["seed"] = seed

    theorems: dict[str, Any] = cfg["theorems"]
    # LEAN_SEED (default 0) -- see resolve_lean_seed(). This is the seed
    # `runner._select_theorems` feeds to `random.Random(seed).sample(pool,
    # limit)`, so it decides WHICH theorems this lane measures; changing
    # it off 0 desyncs from the pinned 300 in
    # notebooks/deduction/pinned_theorems.json (its digest is asserted in
    # tests/deduction/test_lean_pinning_audit.py).
    theorems["seed"] = seed
    # kind/split: the sweep file's values are the DEFAULTS that
    # LEAN_CORPUS_KIND/LEAN_CORPUS_SPLIT override, and that a BLANK override
    # falls back to (see the paragraph above that file's `theorems` block for
    # why they are "random"/"val"). Each loaded default is bound to a local
    # FIRST, because the assignment overwrites the very value it falls back to.
    yaml_kind = theorems["kind"]
    theorems["kind"] = os.environ.get("LEAN_CORPUS_KIND", yaml_kind).strip() or yaml_kind
    yaml_split = theorems["split"]
    theorems["split"] = os.environ.get("LEAN_CORPUS_SPLIT", yaml_split).strip() or yaml_split
    if shard:
        theorems["shard"] = shard

    # The single per-lane entry -- see the USER-LOCKED paragraph above.
    # `extra_params` DEEP-copies the shared COT_ARGS table, so no caller can
    # corrupt it for the other lanes.
    cfg["models"] = [
        {
            "provider": "ec2",
            "model": key,
            "display_name": key,
            "extra_params": copy.deepcopy(COT_ARGS[key]),
        }
    ]

    # Sweep-file provenance stamp, following the LEAN_CELL_WHITELIST sidecar's
    # precedent below exactly: `runner.sweep` writes this whole `config` dict
    # verbatim into the run's manifest.json (runner.py's module docstring,
    # "Output layout"), so stamping the digest HERE is the entire mechanism --
    # there is no matching change inside `runner.sweep`, and no reader should
    # go looking for one. The digest covers the file's RAW BYTES, so it
    # fingerprints the rationale comments that make that file reviewable too,
    # not just the parsed values.
    #
    # REPO-RELATIVE, never absolute: an absolute path would embed this box's
    # checkout location in every archived manifest and make two boxes'
    # manifests differ over nothing. A file OUTSIDE the repo has no
    # repo-relative spelling at all, and is stamped as an absolute path
    # instead -- reachable only through the `sweep_config_path` test seam,
    # never in production.
    cfg["sweep_config"] = {
        "path": _stamp_path(config_path),
        "sha256": sweep_config_sha256,
    }

    # Decontamination-policy provenance stamp, alongside the sweep-file stamp
    # above and recorded the same way. `premises._LEAN_NOISE` -- which lives in
    # this file's `decontam_config.toml` -- decides which identifiers resolve to
    # premise references, and therefore what the `hint:3` and `hint:4` rungs
    # actually CONTAIN. Two of the four rungs this study sweeps are that file's
    # output, so a run's manifest has to record WHICH stoplist produced its
    # prompts, exactly as it now records which sweep knobs it ran under.
    #
    # NOT a sweep knob and deliberately absent from sweep.yaml and from the
    # reserved/required key sets: this is a stamp the driver COMPUTES from a
    # file the package ships, not a value the sweep file supplies. The digest
    # covers that file's RAW BYTES, so it fingerprints the rationale comments
    # that make the policy reviewable, not just the parsed values.
    #
    # Path and digest both come off the SAME loaded config object, never from a
    # path re-spelled here: a second spelling could drift and let the stamp
    # name a different file from the one whose bytes were hashed. The file
    # ships inside the package, so it is not anchored to `REPO_ROOT` the way
    # `SWEEP_CONFIG_PATH` is; `_stamp_path` still renders it repo-relatively
    # for an editable checkout.
    decontam = decontam_config.load_decontam_config()
    cfg["decontam_config"] = {
        "path": _stamp_path(decontam.path),
        "sha256": decontam.sha256,
    }

    # Optional LEAN_CELL_WHITELIST sidecar stamp -- CONDITIONALLY present, like
    # the shard key above, but purely informational: `runner.sweep` reads
    # `LEAN_CELL_WHITELIST` itself. The key exists so the run's `manifest.json`
    # (`sweep` stamps `{"config": config, ...}` verbatim -- see runner.py's
    # module docstring, "Output layout") records WHICH whitelist was in effect,
    # without re-embedding the possibly large key list. The path alone is not
    # enough, since the file can be edited after a run starts, so
    # `runner.hash_cell_keys` fingerprints its SORTED content: a reader diffs
    # `sha256` against a fresh `hash_cell_keys(load_cell_whitelist(path))` to
    # confirm the file on disk is the one this run used. `load_cell_whitelist`
    # raises loudly on a missing or malformed file -- see this function's Notes.
    whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    if whitelist_path:
        cfg["cell_whitelist"] = {
            "path": whitelist_path,
            "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(whitelist_path)),
        }

    return cfg


def select_verifier() -> Any:
    """Resolve the verifier object to hand to ``runner.sweep``, from ``LEAN_VERIFY``.

    ``NullVerifier()`` when ``LEAN_VERIFY`` is unset, empty or ``"defer"`` (the
    default; every verdict is then recorded ``"unverified"`` rather than replayed
    against a real Dojo); the ``smolbench.deduction.lean.verify`` MODULE object
    -- not an instance, since ``runner.sweep`` calls its functions directly --
    when it is exactly ``"real"``. That import is local to the ``"real"`` branch,
    so importing this file never requires ``lean_dojo`` (``"real"`` without it
    raises ``ImportError``). Any other value raises ``SystemExit``.
    """
    choice = os.environ.get("LEAN_VERIFY", "defer").strip() or "defer"
    if choice == "defer":
        return NullVerifier()
    if choice == "real":
        # Local import: verify.py needs lean_dojo (the `lean` extra) at its own
        # module top level, and its ImportError names the fix if it is missing.
        from smolbench.deduction.lean import verify

        return verify
    raise SystemExit(f"LEAN_VERIFY={choice!r} is not valid; expected 'defer' or 'real'.")


def spool_to_s3(run_dir: Path, key: str, *, client: Any = None) -> int:
    """Upload one lane's run directory to S3, verify it, then prune local disk.

    END-OF-RUN ONLY: called once, after ``runner.sweep`` returns (`run_dir` is
    that sweep's output, ``runner.results_root() / "runs" / run_name``).
    ``sweep`` exposes no progress hook, so a crash mid-sweep leaves the rows
    unspooled on local disk until a relaunch reaches this call again.

    Two-phase, and the ordering is load-bearing: upload and verify EVERY file
    (in sorted, deterministic order) before pruning ANY, so a part-way failure
    cannot already have deleted files whose uploads are unconfirmed. Pruning
    keeps ``run_dir / "manifest.json"``, ``run_dir / "all_rows.jsonl"`` and any
    sibling row-archive file matching ``runner.RETIRED_MARKERS`` by name (the
    ``all_rows_SUPERSEDED-<stamp>.jsonl`` files ``--force-rerun`` creates) --
    see "Why all_rows.jsonl survives the prune" below -- then removes now-empty
    subdirectories deepest-first, swallowing ``OSError``; ``run_dir`` is never
    removed.

    Why all_rows.jsonl survives the prune
    --------------------------------------
    A relaunched lane's resume path (``runner.sweep``'s
    ``resume=True`` branch, via ``runner._existing_keys`` and
    ``runner._sanity_done``) reads ONLY ``all_rows.jsonl`` to decide what is
    already recorded -- ``manifest.json`` carries `config`/`run_name`/counts,
    never per-cell state, and resume does not consult it. An earlier version
    of this function pruned everything but ``manifest.json``, so a lane that
    reached this call once (crashed or not, it does not matter) had its ONLY
    resume input deleted: the next relaunch's ``_existing_keys`` and
    ``_sanity_done`` both saw an empty file, `runner.sweep` provisioned a
    fresh box, re-served the checkpoint, and regenerated every cell -- on
    different hardware, and at real additional spend -- even though the
    original rows were already durably uploaded to S3 moments earlier. The
    ``kind: "sanity"`` rows recording each theorem's ground-truth replay
    verdict live INSIDE this same ``all_rows.jsonl`` (there is no separate
    sanity file), so keeping this one file is what keeps them too. Do not
    "optimise" this into uploading a cells-only file later -- the sanity gate
    depends on ``all_rows.jsonl`` surviving exactly as much as cell resume
    does.

    Parameters
    ----------
    key : str
        Model spec key. The destination prefix
        ``f"{runner.spool_prefix()}/scaling_{key}/"`` is built from this, NOT
        from ``run_dir.name``, so the S3 layout stays keyed on the MODEL even
        when ``LEAN_RUN_NAME`` renamed the run directory.
    client : Any, optional
        S3 client with ``upload_file`` and ``head_object``; ``None`` lazily
        builds a boto3 one against `SPOOL_REGION`, so importing this file needs
        no AWS SDK and tests can inject a fake.

    Returns
    -------
    int
        Files uploaded and verified; ``0``, nothing uploaded or pruned, when
        `run_dir` is not a directory -- not an error, since a lane that produced
        nothing (or was already spooled) has nothing to sync.

    Raises
    ------
    RuntimeError
        If any upload fails verification (``head_object`` raised, or its
        ``"ContentLength"`` differs from the local size) -- raised BEFORE any
        pruning, naming the S3 key and both sizes.
    """
    if not run_dir.is_dir():
        logging.info(f"spool_to_s3[{key}]: no run directory at {run_dir}; nothing to sync.")
        return 0

    if client is None:
        import boto3  # lazy -- see docstring

        client = boto3.client("s3", region_name=SPOOL_REGION)

    dest_prefix = f"{runner.spool_prefix()}/scaling_{key}/"
    files = sorted(p for p in run_dir.rglob("*") if p.is_file())

    # Phase 1: upload + verify EVERY file before deleting anything -- see the
    # docstring's "Two-phase" paragraph.
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

    # Phase 2: every upload is verified, so pruning is safe.
    # KEEP manifest.json (run metadata) AND all_rows.jsonl plus any
    # RETIRED_MARKERS-named sibling (all_rows_SUPERSEDED-<stamp>.jsonl etc.) --
    # see the docstring's "Why all_rows.jsonl survives the prune" section.
    # `manifest.json` alone is NOT enough: resume reads all_rows.jsonl, never
    # manifest.json, so deleting the former (as this used to) silently blinds
    # every future resume even though the upload above already durably copied
    # it to S3.
    manifest_path = run_dir / "manifest.json"
    all_rows_path = run_dir / "all_rows.jsonl"
    for path in files:
        if path == manifest_path or path == all_rows_path:
            continue
        if any(marker in path.name for marker in runner.RETIRED_MARKERS):
            continue
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


def outstanding_cell_keys(config: dict, run_dir: Path) -> set[tuple]:
    """Return the cell keys `runner.sweep(config, run_dir, resume=True, ...)` would still write.

    Before ``main`` spends real money provisioning a box and serving a
    checkpoint, it needs to know whether there is anything left for this
    lane to do. This function answers that WITHOUT any AWS call, by
    enumerating the same "would this cell be skipped on resume?" predicate
    ``runner.sweep`` applies internally, and diffing it against what
    ``runner._existing_keys`` already finds recorded on disk.

    DEPENDS ON ``spool_to_s3`` keeping ``all_rows.jsonl`` across its
    end-of-run prune (see that function's docstring): an earlier version of
    ``spool_to_s3`` deleted ``run_dir / "all_rows.jsonl"`` at the end of every
    successful spool, so this function would have seen an empty file after
    every completed lane and always returned "everything is outstanding" --
    the check this function exists for would never have anything to compare
    against, and would never come back empty. Keeping ``all_rows.jsonl``
    across the prune is what makes this function's answer meaningful at all;
    it is not an independent tidy-up.

    Algorithm -- mirrors ``runner.sweep``'s own nesting exactly, by calling
    the SAME functions that sweep calls (not a re-implementation of their
    logic):

    1. ``runner._select_theorems(config["theorems"], cell_whitelist=...)`` for
       the theorem pool -- the same ``LEAN_CELL_WHITELIST`` env var
       ``runner.sweep`` itself reads, loaded here the same way.
    2. Drop any theorem whose RECORDED sanity verdict (from
       ``runner._sanity_done`` over ``all_rows.jsonl``) is in
       ``runner.SANITY_FAILURE_VERDICTS`` -- ``sweep``'s per-theorem worker
       skips cell generation entirely for such a theorem on resume (see its
       ``elif prev_sanity in SANITY_FAILURE_VERDICTS`` branch), so no cell of
       its would ever be written even if attempted. A theorem with NO
       recorded sanity row is KEPT (sweep would still replay its sanity gate
       and, on success, generate its cells): only a *recorded failure*
       removes a theorem here.
    3. For each surviving theorem, ``runner._k_indices(theorem, k_strategy)``.
    4. For each ``k``, each configured rung, skipped when
       ``config["skip_trivial"]`` and ``runner.is_trivial_rung(theorem, k,
       chain, level)`` -- exactly ``sweep``'s own trivial-rung skip.
    5. For each surviving rung, each model entry's ``display_name``, each
       ``replicate_idx`` in ``range(n_replicates)``, filtered by the cell
       whitelist when one is active -- exactly
       ``_run_cells_at_step[_concurrent]``'s own per-cell loop.
    6. Build the row key with ``runner._row_key`` (so it compares equal to
       ``runner._existing_keys``' keys) and collect it into `expected`.

    `outstanding` is then ``expected - runner._existing_keys(all_rows_path)``.

    Parameters
    ----------
    config : dict
        A ``build_config``-shaped sweep config (or an equivalent dict for
        testing); must contain ``theorems``, ``rungs``, ``models`` and,
        optionally, ``k``, ``skip_trivial`` and ``n_replicates`` (all default
        exactly as ``runner.sweep`` defaults them).
    run_dir : Path
        The run directory whose ``all_rows.jsonl`` records what is already
        done; need not exist (an absent file reads as "nothing done", so
        `expected` itself is returned unchanged as `outstanding`).

    Returns
    -------
    set of tuple
        Row keys (``runner._row_key``-shaped) that are in `expected` but not
        yet recorded. Empty exactly when this lane has nothing left to
        generate.

    Raises
    ------
    ValueError
        Propagated from ``runner._select_theorems`` (an invalid
        ``theorems.source``/``theorems.shard``, or a ``require_postcutoff``
        refusal) or from ``runner.load_cell_whitelist`` under
        ``LEAN_CELL_WHITELIST`` -- the same conditions that would make
        ``runner.sweep`` itself raise before doing any work.

    Notes
    -----
    Performs corpus I/O (via ``runner._select_theorems``) and reads
    ``run_dir / "all_rows.jsonl"`` from disk; makes no AWS call, so it is
    callable from an offline test.

    DRIFT RISK -- read before touching either this function or
    ``runner.sweep``'s skip logic: this enumerates ``sweep``'s cell predicate
    at a SECOND site, by calling the same ``runner`` functions ``sweep``
    calls rather than importing one shared predicate function (none exists
    today). A future change to ``sweep``'s own skip logic (trivial-rung
    rules, sanity-failure handling, cell-whitelist filtering, or the
    rung/model/replicate nesting itself) that is not mirrored here would make
    this function's `expected` set UNDER-count what `sweep` would actually
    attempt -- the UNSAFE direction: this check would then conclude a lane
    has nothing outstanding and skip provisioning it, when `sweep` would in
    fact still have written real cells. There is no test that can catch this
    class of drift other than an end-to-end comparison against a live
    `sweep` run; treat any change to `sweep`'s cell-selection logic as
    requiring a matching review of this function.
    """
    all_rows_path = run_dir / "all_rows.jsonl"

    # Same LEAN_CELL_WHITELIST env read runner.sweep itself performs, loaded
    # the same way (see that function's Notes) -- a whitelist narrows BOTH
    # which theorems survive step 1 (via _select_theorems) and which
    # individual cells survive step 5 below.
    cell_whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    cell_whitelist: frozenset[tuple] | None = (
        runner.load_cell_whitelist(cell_whitelist_path) if cell_whitelist_path else None
    )

    theorems = runner._select_theorems(config["theorems"], cell_whitelist=cell_whitelist)
    sanity_done = runner._sanity_done(all_rows_path)
    k_strategy = config.get("k", {}).get("strategy", "last")
    rungs: list[str] = list(config.get("rungs", []))
    models_cfg: list[dict] = list(config["models"])
    n_replicates = int(config.get("n_replicates", 1))
    skip_trivial = bool(config.get("skip_trivial", True))

    expected: set[tuple] = set()
    for theorem in theorems:
        # Step 2: a RECORDED sanity failure means sweep's per-theorem worker
        # returns before generating any cell for this theorem on resume (see
        # runner.sweep's `elif prev_sanity in SANITY_FAILURE_VERDICTS`
        # branch) -- no recorded verdict at all is NOT a failure, and falls
        # through to cell enumeration below exactly as sweep would still
        # attempt it.
        if sanity_done.get(theorem.full_name) in runner.SANITY_FAILURE_VERDICTS:
            continue
        for k in runner._k_indices(theorem, k_strategy):
            for rung in rungs:
                chain, level_str = rung.split(":", 1)
                level = int(level_str)
                # Step 4: identical to runner.sweep's own trivial-rung skip.
                if skip_trivial and runner.is_trivial_rung(
                    theorem, k, chain, level  # type: ignore[arg-type]
                ):
                    continue
                for mc in models_cfg:
                    display_name = mc.get("display_name", mc["model"])
                    for replicate_idx in range(n_replicates):
                        key = runner._row_key(
                            display_name, theorem.full_name, k, rung, replicate_idx
                        )
                        if cell_whitelist is not None and key not in cell_whitelist:
                            continue
                        expected.add(key)

    done = runner._existing_keys(all_rows_path)
    outstanding = expected - done
    logging.info(
        f"outstanding_cell_keys[{config.get('run_name', run_dir.name)}]: "
        f"{len(expected)} expected, {len(expected & done)} done, "
        f"{len(outstanding)} outstanding"
    )
    return outstanding


def main(argv: list[str] | None = None) -> None:
    """Entry point: resolve the lane, provision/serve/sweep, spool, maybe teardown.

    ``SystemExit`` comes from argument parsing, ``selected_model()`` (unset or
    unknown ``LEAN_MODEL``), ``LEAN_SHARD`` without ``--no-s3`` (see the GUARD)
    or ``select_verifier()`` (invalid ``LEAN_VERIFY``) -- all BEFORE any AWS call.

    Also before any AWS call, and NOT a ``SystemExit``: unless
    ``--force-rerun`` was passed or ``all_rows.jsonl`` does not exist yet, this
    calls :func:`outstanding_cell_keys` to recompute ``runner.sweep``'s own
    cell-selection predicate against what is already recorded, and returns
    NORMALLY -- no provisioning, no serving, no sweep, no spool -- when that
    set is empty. A lane with nothing left to generate no longer provisions a
    box just to immediately tear it down having done nothing.

    Past those checks every path makes live, billable AWS calls
    (``ec2.provision_spot_instance()``, ``ec2.serve_model()``, and
    ``ec2.shutdown_instance()`` under ``--teardown``). The sweep runs with
    ``resume=not --force-rerun``, so a relaunched lane picks up from the
    on-disk ``all_rows.jsonl`` whether or not the crashed attempt reached the
    S3 spool -- true BECAUSE ``spool_to_s3`` (see its docstring) now keeps
    ``all_rows.jsonl`` across its end-of-run prune.
    Before that fix the prune deleted the file on every completed spool,
    silently discarding resume's only input, so this same claim used to be
    false for any lane that had already reached the spool once.
    `argv` is a parameter so tests can call this without a subprocess.
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
    # This line is the corpus gate (build_config's "Post-cutoff corpus gate")
    # for EVERY path through main, including --no-s3 and --force-rerun: it
    # runs before provisioning, serving or any other AWS call below.
    config = build_config(key)
    run_dir = runner.results_root() / "runs" / config["run_name"]

    # GUARD -- sharded lanes must not spool. `spool_to_s3`'s destination prefix
    # is keyed on the MODEL, so every shard of a lane would upload its PARTIAL
    # all_rows.jsonl over the canonical `{runner.spool_prefix()}/scaling_<key>/`
    # object that scripts/deduction/lean_verify_rows.py and the analysis read:
    # last writer wins and the lane silently reports one shard's cells as the
    # whole run. Shards stay local until scripts/deduction/merge_lean_shards.py
    # folds them into the canonical run and spools that. Read off the config
    # (which owns the LEAN_SHARD read) rather than the environment a second
    # time.
    if config["theorems"].get("shard") and not args.no_s3:
        raise SystemExit(
            f"LEAN_SHARD={config['theorems']['shard']!r} requires --no-s3: a shard "
            f"would overwrite the canonical "
            f"s3://{SPOOL_BUCKET}/{runner.spool_prefix()}/scaling_{key}/ objects "
            "with its partial rows.\n"
            "Fix: re-run this shard with --no-s3, then merge and spool with "
            "`scripts/deduction/merge_lean_shards.py <key> --n <n> --spool`."
        )

    # Resolved -- and any SystemExit raised -- BEFORE provisioning: see the
    # module docstring's "LIFECYCLE" step 3.
    verifier = select_verifier()

    # Module docstring "LIFECYCLE" step 4: before spending real money (a
    # fresh box, a served checkpoint, a whole sweep), check whether this lane
    # has anything LEFT to do. Two cases bypass the check entirely rather
    # than computing it:
    #   - --force-rerun exists specifically to regenerate every cell, so the
    #     answer would always be "provision anyway"; computing it first would
    #     just be wasted corpus I/O.
    #   - No all_rows.jsonl yet means nothing has ever been recorded for this
    #     run_dir, so every expected cell is trivially outstanding -- there is
    #     nothing on disk for outstanding_cell_keys to read, and calling it
    #     would do a full theorem-selection pass just to reach that same
    #     conclusion the hard way.
    # DEPENDS ON spool_to_s3 keeping all_rows.jsonl across its prune (see that
    # function's docstring): before that fix, a completed lane's
    # all_rows.jsonl was deleted at the end of every successful spool, so
    # this branch would ALWAYS have taken the "nothing recorded yet" path and
    # ALWAYS provisioned -- that fix is what makes this check reachable at all.
    all_rows_path = run_dir / "all_rows.jsonl"
    if args.force_rerun:
        logging.info(
            f"main[{key}]: --force-rerun set; skipping the outstanding-cell "
            "check and provisioning unconditionally to regenerate every cell."
        )
    elif not all_rows_path.exists():
        logging.info(
            f"main[{key}]: no {all_rows_path} yet; nothing recorded for this "
            "run, so the whole lane is outstanding -- provisioning."
        )
    else:
        outstanding = outstanding_cell_keys(config, run_dir)
        if not outstanding:
            logging.info(
                f"main[{key}]: 0 cells outstanding in {run_dir} -- every "
                "expected cell is already recorded. Nothing to do; exiting "
                "WITHOUT provisioning, serving, sweeping or spooling."
            )
            return
        logging.info(
            f"main[{key}]: {len(outstanding)} cell(s) outstanding in "
            f"{run_dir}; provisioning to generate them."
        )

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
            # Provenance sidecar: snapshot the serving stack INSIDE the serve
            # block (the landed box is the one that generates) into run_dir, so
            # spool_to_s3 carries it with the rows. One file per run; a relaunch
            # APPENDS a fresh timestamped snapshot rather than overwriting, so a
            # resume that landed on different hardware stays visible in the log.
            cfg = ec2.server_config(key)
            if cfg is not None:
                import datetime

                import yaml

                # mkdir first: runner.sweep creates run_dir itself, but this
                # sidecar writes BEFORE the sweep runs.
                run_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                with (run_dir / "server_config.yaml").open("a") as sink:
                    yaml.safe_dump([{"captured_utc": stamp, **cfg}],
                                   sink, default_flow_style=False, indent=4)
            if args.force_rerun:
                # Move the old rows aside rather than appending on top of them:
                # with resume=False the sweep regenerates every cell but still
                # APPENDS to all_rows.jsonl, leaving superseded and fresh rows
                # for each key in one file, generated on different hardware,
                # with only line order to tell them apart. The archive stays
                # inside run_dir, so spool_to_s3 carries it to S3 under its own
                # key -- superseded data is labelled, never silently dropped.
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
        # In the finally block so a lane launched with --teardown still tears
        # its box down even if the sweep raised -- module docstring, LIFECYCLE
        # step 7.
        if args.teardown:
            logging.info(f"main[{key}]: --teardown set; shutting down this lane's instance.")
            ec2.shutdown_instance()

    print(f"DEDUCTION LANE COMPLETE: {key} ({n} cell row(s)) run_dir={run_dir}", flush=True)


if __name__ == "__main__":
    main()
