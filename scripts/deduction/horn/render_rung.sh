#!/usr/bin/env bash
# Render one rung (10 seeds in parallel).
# usage: NC=1 OF=1.0 M=12 H=2 ARMS="lem both pad ax" render_rung.sh <out_dir> <lemma_tokens> <unfold_tokens>
# SEED0 / NSEEDS pick the seed range (default 0..9). Use a fresh SEED0 for a confirmatory run:
# every rung rendered from the same seeds shares chains, facts and goals.
set -e
out=$1; lt=$2; ut=$3
# REPO: the checkout to run from (default: the repo this script sits in).
cd "${REPO:-$(dirname "$0")/../../..}"
PY=${PYTHON:-.venv/bin/python}
seq ${SEED0:-0} $(( ${SEED0:-0} + ${NSEEDS:-10} - 1 )) | xargs -P 10 -I{} $PY -m smolbench.deduction.horn.cli render --seeds {} --m ${M:-12} --height ${H:-2} --n-constants ${NC:-3} --n-unused-facts ${NUF:-0} --open-frac ${OF:-0.25} --lemma-tokens $lt --unfold-tokens $ut --max-steps-x ${CAPX:-0} --arms ${ARMS:-lem both pad} --out $out > /dev/null
echo "$out done: $(ls -d $out/s* | wc -l) seeds"
