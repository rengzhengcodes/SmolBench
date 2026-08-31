#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Trace mathlib4 with LeanDojo v2 on a throwaway EC2 box.
#
# WHAT THIS DOES
#   Produces the `generate_benchmark` export that
#   scripts/deduction/build_postcutoff_corpus.py consumes: it installs a Lean
#   toolchain and a *deliberately dependency-starved* lean-dojo-v2, clones
#   mathlib4 at $COMMIT, fetches the prebuilt oleans, traces the whole library,
#   and uploads the tarball to S3. Tracing all of mathlib4 takes hours and
#   hundreds of GiB of scratch, which is why it runs on its own instance and
#   ships its result to S3 rather than running anywhere near a laptop.
#
# THIS IS A RUNBOOK, NOT CI
#   Nothing here runs in the test suite or on a dev box except `--dry-run`,
#   which only PRINTS the plan: it creates no files, probes no binaries, needs
#   no network, no root and no credentials. Read the plan, then run the script
#   for real on the target host.
#
# PRECONDITIONS (real runs only)
#   * Ubuntu 24.04 on r7i.8xlarge (32 vCPU / 256 GiB RAM), with a 300 GB gp3
#     volume mounted at /mnt/data and writable by the invoking user. $HOME is
#     NOT used: the root volume is too small for a trace.
#   * GITHUB_ACCESS_TOKEN exported (lean-dojo-v2 resolves the repo through the
#     GitHub API and gets rate-limited to uselessness without one). Its value is
#     never echoed. A DEAD token is worse than none -- it fails late, mid-trace.
#   * Passwordless sudo (or root): phase 1 apt-get installs the Python and git
#     packages the trace needs.
#   * Ambient AWS credentials with write access to $S3_PREFIX (instance role).
#   * Outbound network to github.com, pypi.org, the elan and Mathlib caches.
#
# IDEMPOTENCY
#   Every phase self-skips, with a log line, when its output already exists:
#   clone dir present, `lake exe cache get` marker present, export dir
#   non-empty, tarball present. A killed run is resumed by re-invoking the same
#   command line; only the phase that died repeats. The probes are themselves
#   skipped under --dry-run (see `already`), so the printed plan is always the
#   full, unconditional sequence.
#
# USAGE
#   scripts/deduction/trace_mathlib_ec2.sh --dry-run
#   GITHUB_ACCESS_TOKEN=ghp_... scripts/deduction/trace_mathlib_ec2.sh
# ---------------------------------------------------------------------------
set -euo pipefail

COMMIT="2ca39e62989124794bd8405bb2e60805f63d37bc"
WORKDIR="/mnt/data"
# LeanDojo forks one Lean process per worker and each needs ~4 GiB resident, so
# 256 GiB would nominally allow ~60. Capped at 48 for headroom: the tail of the
# trace hits a few pathological files whose workers spike well past 4 GiB, and
# an OOM-kill loses the whole run, not just that file.
NUM_PROCS=48
S3_PREFIX="s3://smolbench-results-414266451290/deduction_postcutoff/corpus/"
DRY_RUN=0

usage() {
    cat <<'USAGE'
Usage: trace_mathlib_ec2.sh [options]

  --commit SHA       mathlib4 commit to trace
                     (default 2ca39e62989124794bd8405bb2e60805f63d37bc)
  --workdir DIR      scratch root; holds the checkout, the export and the log
                     (default /mnt/data)
  --num-procs N      LeanDojo worker processes (default 48)
  --s3-prefix URI    destination prefix; the tarball lands under <URI><COMMIT>/
                     (default s3://smolbench-results-414266451290/deduction_postcutoff/corpus/)
  --dry-run          print the plan and exit 0; touch nothing
  -h, --help         this message
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --commit)    COMMIT="$2"; shift 2 ;;
        --workdir)   WORKDIR="$2"; shift 2 ;;
        --num-procs) NUM_PROCS="$2"; shift 2 ;;
        --s3-prefix) S3_PREFIX="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=1; shift ;;
        -h|--help)   usage; exit 0 ;;
        *)           echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

CHECKOUT="$WORKDIR/mathlib4"
VENV="$WORKDIR/venv"
CACHE_DIR="$WORKDIR/cache"
TMP_DIR="$WORKDIR/tmp"
EXPORT_DIR="$WORKDIR/export-$COMMIT"
TARBALL="$WORKDIR/mathlib4-leandojo-$COMMIT.tar.gz"
CACHE_MARKER="$CHECKOUT/.smolbench-lake-cache-get-done"
LOG="$WORKDIR/trace_mathlib_ec2.log"

# --------------------------------------------------------------------------
# Helpers. Every side effect in this script goes through `run`/`run_python`, so
# --dry-run is enforced in exactly two places instead of at every call site.
# --------------------------------------------------------------------------

# Echo a command line under --dry-run, otherwise execute it. `eval` rather than
# "$@" so that one helper covers pipelines, redirections and `cd &&` chains --
# the printed plan then IS the executed text, with no second quoting dialect for
# a reader to translate.
run() {
    if (( DRY_RUN )); then
        printf '  $ %s\n' "$1"
    else
        eval "$1"
    fi
}

# Same contract for an inline Python program. The plan prints the SOURCE, not a
# variable name: the trace call is the one step a reviewer actually has to read.
run_python() {
    if (( DRY_RUN )); then
        printf '  $ %s/bin/python - <<%s\n' "$VENV" "'PY'"
        printf '%s\n' "$1"
        printf 'PY\n'
    else
        printf '%s\n' "$1" | "$VENV/bin/python" -
    fi
}

note() { printf '  # %s\n' "$1"; }

# Idempotency probe. Always returns "not done yet" under --dry-run: probing the
# filesystem there would both make the printed plan depend on this box and
# suppress the phases the plan exists to show.
already() {
    if (( DRY_RUN )); then
        return 1
    fi
    [[ -e "$1" ]]
}

phase_start() {
    PHASE_NAME="$1"
    PHASE_T0=$SECONDS
    printf '\n===== phase %s =====\n' "$PHASE_NAME"
}

phase_end() {
    printf '===== phase %s: done in %ds =====\n' "$PHASE_NAME" "$(( SECONDS - PHASE_T0 ))"
}

skip_phase() {
    printf '===== phase %s: SKIPPED (%s already exists) =====\n' "$PHASE_NAME" "$1"
}

# --------------------------------------------------------------------------
# Logging. The log lives under $WORKDIR, never $HOME (root volume, too small)
# and never cwd (which is wherever the operator happened to be). Opening it is
# itself a file creation, so it is gated on the dry-run check like everything
# else.
# --------------------------------------------------------------------------
if (( ! DRY_RUN )); then
    mkdir -p "$WORKDIR"
    exec > >(tee -a "$LOG") 2>&1
fi

printf 'trace_mathlib_ec2.sh%s\n' "$( (( DRY_RUN )) && printf ' --dry-run (PLAN ONLY, nothing is executed)' || printf '' )"
printf 'commit=%s workdir=%s num_procs=%s\n' "$COMMIT" "$WORKDIR" "$NUM_PROCS"
printf 'log=%s\n' "$LOG"
if (( DRY_RUN )); then
    note "each phase self-skips when its output already exists; probes are not run here"
fi

# --------------------------------------------------------------------------
# Toolchain PATH. Unconditional and outside every phase conditional: elan is
# installed by phase 1, but phase 1 SKIPS itself on a resumed run, and phase 5's
# `lake exe cache get` needs elan's shims regardless of which phase actually
# runs. Exporting this only where elan is installed would break exactly the
# resume path the idempotency design exists to serve.
# --------------------------------------------------------------------------
run "export PATH=\"\$HOME/.elan/bin:\$PATH\""

# --------------------------------------------------------------------------
# Phase 1: deps
# --------------------------------------------------------------------------
phase_start deps
if already "$VENV/bin/python"; then
    skip_phase "$VENV"
else
    note "elan installs the toolchain pinned by mathlib4's lean-toolchain file"
    run "curl --proto '=https' --tlsv1.2 -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none"
    run "sudo apt-get update -y"
    run "sudo apt-get install -y git curl unzip python3.12 python3.12-venv"
    run "python3.12 -m venv '$VENV'"
    run "'$VENV/bin/pip' install --upgrade pip"
    # --no-deps is deliberate, not a shortcut: lean-dojo-v2's declared
    # dependencies pull a full training stack (torch, deepspeed,
    # pytorch_lightning, ...) that conflicts with itself on a CPU box and is
    # never touched by tracing. The next line installs the handful actually
    # imported on the trace path; the `shim` phase covers the two that are
    # hard-imported but unused.
    run "'$VENV/bin/pip' install lean-dojo-v2==1.0.9 --no-deps"
    run "'$VENV/bin/pip' install loguru tqdm networkx lxml gitpython PyGithub python-dotenv toml"
    phase_end
fi

# --------------------------------------------------------------------------
# Phase 2: shim
# --------------------------------------------------------------------------
# lean_dojo/utils/__init__.py hard-imports `deepspeed` and `pytorch_lightning`
# at module import time -- before any tracing code runs and although the trace
# path never calls into either. Installing them for real would drag in the
# conflicting ML stack --no-deps exists to avoid, so two empty stub modules on
# the venv's site-packages path satisfy the import and nothing else.
SHIM_PY=$(cat <<'EOF'
import pathlib
import sysconfig

site_packages = pathlib.Path(sysconfig.get_paths()["purelib"])
banner = (
    "# SmolBench stub: lean_dojo.utils hard-imports this module at import time\n"
    "# but tracing never uses it. Installing the real package would pull the\n"
    "# heavy, self-conflicting ML stack that `pip install --no-deps` avoids.\n"
)
for module in ("deepspeed", "pytorch_lightning"):
    (site_packages / f"{module}.py").write_text(banner)
    print(f"shimmed {site_packages / (module + '.py')}")
EOF
)

phase_start shim
if already "$VENV/lib/python3.12/site-packages/deepspeed.py"; then
    skip_phase "deepspeed.py stub"
else
    run_python "$SHIM_PY"
    phase_end
fi

# --------------------------------------------------------------------------
# Phase 3: env
# --------------------------------------------------------------------------
phase_start env
if (( DRY_RUN )); then
    note "GITHUB_ACCESS_TOKEN must already be exported; its value is never printed"
    printf '  $ export GITHUB_ACCESS_TOKEN=<redacted, read from the environment>\n'
else
    if [[ -z "${GITHUB_ACCESS_TOKEN:-}" ]]; then
        echo "ERROR: GITHUB_ACCESS_TOKEN is unset." >&2
        echo "  lean-dojo-v2 resolves mathlib4 through the GitHub API and is" >&2
        echo "  rate-limited to failure without a token. Mint one at" >&2
        echo "  https://github.com/settings/tokens (public_repo scope is enough)," >&2
        echo "  then re-run:  export GITHUB_ACCESS_TOKEN=ghp_..." >&2
        exit 2
    fi
    export GITHUB_ACCESS_TOKEN
fi
run "mkdir -p '$CACHE_DIR' '$TMP_DIR'"
run "export CACHE_DIR=$CACHE_DIR"
run "export TMP_DIR=$TMP_DIR"
run "export NUM_PROCS=$NUM_PROCS"
phase_end

# --------------------------------------------------------------------------
# Phase 4: clone
# --------------------------------------------------------------------------
phase_start clone
if already "$CHECKOUT/.git"; then
    skip_phase "$CHECKOUT"
else
    # Full history, not --depth 1: the checkout is pinned to a specific commit
    # and lean-dojo inspects the repo's git metadata.
    run "git clone https://github.com/leanprover-community/mathlib4 '$CHECKOUT'"
    run "git -C '$CHECKOUT' checkout $COMMIT"
    phase_end
fi

# --------------------------------------------------------------------------
# Phase 5: cache
# --------------------------------------------------------------------------
phase_start cache
if already "$CACHE_MARKER"; then
    skip_phase "$CACHE_MARKER"
else
    # A PRECONDITION, not an optimisation. Without Mathlib's prebuilt oleans the
    # trace rebuilds the entire library from source underneath itself, which
    # turns a several-hour job into a multi-day one.
    run "cd '$CHECKOUT' && lake exe cache get"
    run "touch '$CACHE_MARKER'"
    phase_end
fi

# --------------------------------------------------------------------------
# Phase 6: trace
# --------------------------------------------------------------------------
# The repo argument is the LOCAL checkout path, using lean-dojo-v2's
# local-checkout support: passing the GitHub URL would make LeanDojo clone and
# build its own copy, discarding the `lake exe cache get` done above.
# build_deps=True so that premises defined in mathlib4's dependencies (std,
# aesop, Qq, ...) appear in corpus.jsonl -- the deduction eval's premise lookup
# resolves against the whole library, not just Mathlib/.
TRACE_PY=$(cat <<EOF
from lean_dojo import LeanGitRepo, generate_benchmark

repo = LeanGitRepo("$CHECKOUT", "$COMMIT")
generate_benchmark(repo, "$EXPORT_DIR", build_deps=True)
print("export written to $EXPORT_DIR")
EOF
)

phase_start trace
if already "$EXPORT_DIR/metadata.json"; then
    skip_phase "$EXPORT_DIR"
else
    note "hours; NUM_PROCS=$NUM_PROCS workers, watch RSS in another shell"
    run_python "$TRACE_PY"
    phase_end
fi

# --------------------------------------------------------------------------
# Phase 7: upload
# --------------------------------------------------------------------------
phase_start upload
if already "$TARBALL"; then
    skip_phase "$TARBALL"
else
    # -C $WORKDIR so the tarball unpacks to a single self-naming directory.
    run "tar czf '$TARBALL' -C '$WORKDIR' '${EXPORT_DIR##*/}'"
    run "aws s3 cp '$TARBALL' '$S3_PREFIX$COMMIT/'"
    phase_end
fi

printf '\nALL PHASES COMPLETE (commit %s)\n' "$COMMIT"
if (( DRY_RUN )); then
    printf 'DRY RUN: nothing above was executed and no file was created.\n'
fi
exit 0
