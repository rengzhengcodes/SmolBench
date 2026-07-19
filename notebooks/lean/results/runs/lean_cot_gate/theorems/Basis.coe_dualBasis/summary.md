# Basis.coe_dualBasis   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply dualBasis_apply
```

**True premises at k:** `Basis.dualBasis_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✓ ✘ | ✓ · ✓ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ | ✓ · · ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 11.3s, verify 0.1s, in=301, out=498)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 20.4s, verify 0.1s, in=301, out=950)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 47.4s, verify 0.1s, in=301, out=2299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 93.3s, verify 0.1s, in=301, out=4599)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply linear_map.ext_basis b
intros j
rw dualBasis_apply
rw Basis.coord_self
```

**lean_error:** tail step 1/4 ('apply linear_map.ext_basis b'): unknown identifier 'linear_map.ext_basis'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=301, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.7s, verify 0.1s, in=301, out=12)

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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=301, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.dualBasis_apply]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=301, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualBasis, dualBasis_apply_left_finite]
```

**lean_error:** tail step 1/1 ('simp [dualBasis, dualBasis_apply_left_finite]'): unknown identifier 'dualBasis_apply_left_finite'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.8s, verify 0.1s, in=301, out=174)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualBasis_apply]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 5.8s, verify 0.1s, in=301, out=175)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.6s, verify 0.1s, in=301, out=211)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.dualBasis_apply]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.6s, verify 0.1s, in=301, out=369)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [dualBasis, coord_apply, equivFun_symm_apply, Pi.single_apply,
  Finsupp.single_eq_pi_single]
```

**lean_error:** tail step 1/2 ('simp only [dualBasis, coord_apply, equivFun_symm_apply, Pi.single_apply,'): <stdin>:1:72: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 20.8s, verify 0.1s, in=499, out=982)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply dualBasis_apply
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 41.2s, verify 0.1s, in=499, out=2020)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply dualBasis_apply
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 81.2s, verify 0.2s, in=499, out=3915)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply]
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 99.8s, verify 0.2s, in=499, out=5006)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [dualBasis_apply]
refl
```

**lean_error:** tail step 2/2 ('refl'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=499, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [dualBasis_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=499, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Basis.dualBasis_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=499, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Basis.coord, dualBasis_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=499, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [dualBasis_apply, LinearEquiv.coe_coe]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 5.1s, verify 0.1s, in=499, out=155)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Basis.dualBasis_apply]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 5.3s, verify 0.1s, in=499, out=158)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coord, dualBasis_apply]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 5.5s, verify 0.1s, in=499, out=156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.7s, verify 0.1s, in=499, out=218)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [dualBasis_apply]
```
