# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · · ✘ |
| `hint:2` | · ✘ ✘ ✓ |
| `hint:3` | ✓ ✓ ✘ ✘ |
| `noise:3` | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=378, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [det_apply_basis]
```

**lean_error:** tail step 1/1 ('simp [det_apply_basis]'): unknown identifier 'det_apply_basis'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 4.4s, verify 0.2s, in=378, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 4.6s, verify 0.2s, in=378, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

**final state (truncated):**
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 4.8s, verify 0.1s, in=378, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.det_apply_eq, det_isAlternatingMap, Equiv.Perm.coe_ofBijective]
```

**lean_error:** tail step 1/1 ('simp [Basis.det_apply_eq, det_isAlternatingMap, Equiv.Perm.coe_ofBijective]'): unknown constant 'Basis.det_apply_eq'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.5s, verify 0.2s, in=871, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [f.map_perm, e.det_self]
```

**final state (truncated):**
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=871, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map_perm, det_apply, Equiv.Perm.sign_apply, Basis.det_self]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_apply, Equiv.Perm.sign_apply, Basis.det_self]'): unknown constant 'Equiv.Perm.sign_apply'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=871, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [f.map_perm, e.det.map_perm, e.det_self, mul_smul]
```

**lean_error:** tail step 1/1 ('simp [f.map_perm, e.det.map_perm, e.det_self, mul_smul]'): ambiguous, possible interpretations 

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.3s, verify 0.1s, in=871, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [e.det_self, map_perm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.1s, verify 0.2s, in=2001, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map_perm, Basis.det_self]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.3s, verify 0.2s, in=2001, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map_perm, det_apply, Basis.det_self]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=2001, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map_perm, det_apply, det_self, Equiv.Perm.sign_apply, smul_smul, mul_comm]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_apply, det_self, Equiv.Perm.sign_apply, smul_smul, mul_comm]'): unknown identifier 'det_self'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=2001, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map_perm, Basis.det_self, sign]
```

**lean_error:** tail step 1/1 ('simp [map_perm, Basis.det_self, sign]'): unknown identifier 'sign'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.4s, in=2029, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [e.det_apply, map_perm]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=2029, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map_perm, det_apply, Basis.det_self]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=2029, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map_perm, det_apply, det_self, ← smul_assoc, ← map_perm]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_apply, det_self, ← smul_assoc, ← map_perm]'): unknown identifier 'det_self'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=2029, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map_perm, e.det_self, f.map_perm, Equiv.Perm.sign_apply]
```

**lean_error:** tail step 1/1 ('simp [map_perm, e.det_self, f.map_perm, Equiv.Perm.sign_apply]'): unknown constant 'Equiv.Perm.sign_apply'
