#!/usr/bin/env bash
# Regenerate the example prompts (run from the repo root): the m = 6 rung of seed 7.
set -e
out=$(mktemp -d)
python -m smolbench.deduction.horn.cli render --seeds 7 --m 6 --out $out
dst=smolbench/deduction/horn/examples
cp $out/s0007/theory.json $dst/theory.json
cp $out/s0007/lem/system.md $dst/system.md
for arm in lem pad disc both; do
  cp $out/s0007/$arm/prompt.md $dst/$arm.prompt.md
  python - $out/s0007 $arm $dst <<'PY'
import json, sys
from pathlib import Path
from smolbench.deduction.horn.checker import designed_proof
from smolbench.deduction.horn.theory import Theory
sd, arm, dst = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
th = Theory.from_json((sd / "theory.json").read_text())
(dst / f"{arm}.proof.txt").write_text("\n".join(designed_proof(th, "short")) + "\n")
if arm == "both":
    (dst / "both.tree_proof.txt").write_text("\n".join(designed_proof(th, "long")) + "\n")
PY
done
rm -rf $out
