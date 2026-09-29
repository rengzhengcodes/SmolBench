#!/usr/bin/env bash
# One-time setup of a packed deduction box (see packed_box.py). Run on the box
# as the ssh user after the repo and the corpus have been copied to $W:
#
#   W=/opt/dlami/nvme/sb bash $W/repo/scripts/deduction/packed_box_setup.sh
#
# Starts the long steps in the background (image pull, weight downloads) and
# runs the Lean install in the foreground. Logs go to $W/logs/setup_*.log.
set -euo pipefail
W=${W:-/opt/dlami/nvme/sb}
REPO=$W/repo
MATHLIB_COMMIT=2ca39e62989124794bd8405bb2e60805f63d37bc
LEAN_TAG=v4.34.0-rc2
mkdir -p "$W/logs" "$W/hf-cache"
cd "$REPO"

# 1. vLLM image, in the background: it is tens of GB.
IMAGE=$(python3 - <<'EOF'
import re
src = open("smolbench/evals/providers/ec2.py").read()
print(re.search(r'EC2_VLLM_IMAGE: str = os.getenv\("EC2_VLLM_IMAGE", "([^"]+)"\)', src).group(1))
EOF
)
nohup docker pull "$IMAGE" > "$W/logs/setup_docker_pull.log" 2>&1 &

# 2. Python environment for the driver, the lanes and the verifier.
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=$HOME/.local/bin:$PATH
uv sync --extra lean --extra aws > "$W/logs/setup_uv.log" 2>&1
uv pip install "huggingface_hub[hf_xet]" >> "$W/logs/setup_uv.log" 2>&1

# 3. Weights for every planned model, in queue order, in the background.
#    PREFETCH_MODELS=a,b restricts the download to those plan entries (a box
#    that runs only part of the roster).
PATH=$REPO/.venv/bin:$PATH nohup .venv/bin/python scripts/deduction/packed_box.py \
    --prefetch-only --spool-prefix unused --lean-data unused --work "$W" \
    ${PREFETCH_MODELS:+--models "$PREFETCH_MODELS"} \
    > "$W/logs/setup_prefetch.log" 2>&1 &

# 4. Lean toolchain and Mathlib at the corpus commit, with its build cache.
command -v elan >/dev/null || curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain none > "$W/logs/setup_elan.log" 2>&1
export PATH=$HOME/.elan/bin:$PATH
if [ ! -d "$W/mathlib4/.git" ]; then
    git clone --filter=blob:none https://github.com/leanprover-community/mathlib4 "$W/mathlib4" \
        > "$W/logs/setup_mathlib.log" 2>&1
fi
cd "$W/mathlib4"
git checkout -q "$MATHLIB_COMMIT"
lake exe cache get >> "$W/logs/setup_mathlib.log" 2>&1
# Lean core sources: corpus premises in Init/Std point under .lake/packages/lean4.
if [ ! -d .lake/packages/lean4/src ]; then
    git clone --depth 1 --branch "$LEAN_TAG" https://github.com/leanprover/lean4 .lake/packages/lean4 \
        >> "$W/logs/setup_mathlib.log" 2>&1
fi
# premises.py reads sources through the LeanDojo cache path for the corpus commit.
mkdir -p "$HOME/.cache/lean_dojo/leanprover-community-mathlib4-$MATHLIB_COMMIT"
ln -sfn "$W/mathlib4" "$HOME/.cache/lean_dojo/leanprover-community-mathlib4-$MATHLIB_COMMIT/mathlib4"
echo "setup: Lean + Mathlib ready at $W/mathlib4"
