#!/usr/bin/env bash
# Regenerate the example prompts (run from the repo root).
set -e
python -m smolbench.deduction.horn.cli render --seeds 7 --m 6 --height 2 --n-constants 1 \
  --lemma-tokens 1500 --unfold-tokens 3000 --fact-height 2 --fact-tokens 3000 \
  --arms lem pad both junk disc deep dpad ax --out /tmp/horn_examples
for arm in lem pad both junk disc deep dpad ax; do
  cp /tmp/horn_examples/s0007/$arm/prompt.md smolbench/deduction/horn/examples/$arm.prompt.md
done
