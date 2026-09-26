#!/usr/bin/env bash
# Render one rung: the four arms of NSEEDS theories at chain length M, 10 seeds in parallel.
# usage: M=12 SEED0=100 NSEEDS=30 render_rung.sh <out_dir>
# A rung is defined by M alone (M chain lemmas + 5 M open alternatives, depth-2 trees).
# Every rung rendered from the same seeds shares nothing beyond the recipe; use a fresh
# SEED0 for a confirmatory run. REPO / PYTHON select the checkout and interpreter; ARMS
# restricts the arms (calibration rungs: ARMS=lem).
set -e
out=$1
cd "${REPO:-$(dirname "$0")/../../..}"
PY=${PYTHON:-.venv/bin/python}
seq ${SEED0:-100} $(( ${SEED0:-100} + ${NSEEDS:-30} - 1 )) | xargs -P 10 -I{} $PY -m smolbench.deduction.horn.cli render --seeds {} --m ${M:-12} --arms ${ARMS:-lem pad disc both} --out $out > /dev/null
echo "$out done: $(ls -d $out/s* | wc -l) seeds"
