# Basis.coe_dualBasis   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply dualBasis_apply
```

**True premises at k:** `Basis.dualBasis_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.2s, in=364, out=923)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Basis.dualBasis, Basis.coord]
```

**lean_error:** tail step 1/1 ('simpa [Basis.dualBasis, Basis.coord]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 86.2s, verify 0.1s, in=314, out=11873)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualBasis, Pi.basisSingle_apply, coord]
```

**lean_error:** tail step 1/1 ('simp [dualBasis, Pi.basisSingle_apply, coord]'): unknown identifier 'Pi.basisSingle_apply'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.3s, verify 0.1s, in=309, out=470)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualBasis]
```

**final state (truncated):**
```
case h.h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.0s, verify 0.1s, in=554, out=813)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Basis.dualBasis_apply, Basis.coord_apply]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 8.4s, verify 0.2s, in=525, out=1104)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply]
<;> simp [coord]
```

**lean_error:** tail step 2/2 ('<;> simp [coord]'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.9s, verify 0.2s, in=512, out=873)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply]
rfl
```
