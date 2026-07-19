# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · · ✘ | ✘ · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✓ | ✓ ✘ ✘ ✘ |
| `hint:3` | ✓ ✘ ✘ · | ✓ ✓ ✘ ✘ | ✘ ✘ ✓ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 91.3s, verify 0.2s, in=378, out=4091)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [f.map_perm σ e, Basis.det_perm σ e]
rw smul_eq_mul
apply mul_comm
```

**lean_error:** tail step 1/3 ('rw [f.map_perm σ e, Basis.det_perm σ e]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 112.9s, verify 0.1s, in=378, out=4937)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [e.alternating_map_apply]
```

**lean_error:** tail step 1/1 ('rw [e.alternating_map_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 149.6s, verify 0.1s, in=378, out=6529)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [f.map_permute σ, Basis.det_permute σ]
rw [smul_eq_mul]
rw [mul_comm]
```

**lean_error:** tail step 1/3 ('rw [f.map_permute σ, Basis.det_permute σ]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 184.0s, verify 0.1s, in=378, out=7890)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.Alternating.map_perm σ]
rw [Basis.det_apply_compose_perm σ]
simp only [smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/3 ('rw [LinearMap.Alternating.map_perm σ]'): tactic 'rewrite' failed, equality or iff proof expected

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.7s, verify 0.1s, in=378, out=371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← map_smul, det_apply]
```

**lean_error:** tail step 1/1 ('rw [← map_smul, det_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 22.8s, verify 0.2s, in=378, out=662)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.smul_apply]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 31.3s, verify 0.1s, in=378, out=955)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.smul_apply, Basis.det_apply]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.smul_apply, Basis.det_apply]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 37.0s, verify 0.1s, in=378, out=1164)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.smul_apply, Basis.det_apply_self, smul_eq_mul]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.smul_apply, Basis.det_apply_self, smul_eq_mul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 112.0s, verify 0.1s, in=871, out=4925)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm f e σ], 
rw [map_perm e.det e σ, Basis.det_self], 
simp, 
rw [smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/4 ('rw [map_perm f e σ],'): <stdin>:1:19: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 142.6s, verify 0.1s, in=871, out=6238)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, map_perm, det_self], simp [smul_eq_mul], rw [mul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm, map_perm, det_self], simp [smul_eq_mul], rw [mul_comm]'): <stdin>:1:33: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 152.9s, verify 0.2s, in=871, out=6660)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm f σ]
rw [smul_apply]
rw [map_perm e.det σ, det_self]
simp
rw [smul_eq_mul]
rfl
```

**lean_error:** tail step 1/6 ('rw [map_perm f σ]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 173.5s, verify 0.2s, in=871, out=7499)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, map_perm, Basis.det_self, smul_eq_mul, mul_one, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm, map_perm, Basis.det_self, smul_eq_mul, mul_one, mul_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 11.3s, verify 0.1s, in=871, out=322)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map_perm, smul_comm, Basis.det_self]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.9s, verify 0.2s, in=871, out=340)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, LinearMap.smul_apply, Basis.det.map_perm, det_self, smul_one, smul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm, LinearMap.smul_apply, Basis.det.map_perm, det_self, smul_one, smul_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.1s, verify 0.2s, in=871, out=414)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [smul_apply, map_perm, Basis.det_self, smul_comm, smul_one_smul]
```

**lean_error:** tail step 1/1 ('simp only [smul_apply, map_perm, Basis.det_self, smul_comm, smul_one_smul]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.4s, verify 0.1s, in=871, out=421)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map_perm, det_self]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_self]'): unknown identifier 'det_self'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 184.5s, verify 0.3s, in=2001, out=2985)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, AlternatingMap.smul_apply, AlternatingMap.map_perm, Basis.det_self]
simp [smul_eq_mul]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 194.9s, verify 0.1s, in=2001, out=3583)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [map_perm f, map_perm (det e), det_self, mul_one], simp [smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm f, map_perm (det e), det_self, mul_one], simp [smul_eq_mul, mul_comm]'): <stdin>:1:52: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 236.2s, verify 0.2s, in=2001, out=5569)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, smul_apply, AlternatingMap.map_perm, Basis.det_self, mul_one, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.map_perm, smul_apply, AlternatingMap.map_perm, Basis.det_self, mul_one, mul_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 257.0s, verify 0.1s, in=2001, out=6735)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [map_perm, smul_apply, map_perm, Basis.det_self, smul_eq_mul, mul_comm]
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 21.9s, verify 0.1s, in=2001, out=308)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map_perm, det_self]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_self]'): unknown identifier 'det_self'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 23.0s, verify 0.1s, in=2001, out=316)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [map_perm, map_perm, det_self]
```

**lean_error:** tail step 1/1 ('simp only [map_perm, map_perm, det_self]'): unknown identifier 'det_self'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 24.5s, verify 0.1s, in=2001, out=343)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [map_perm, e.det_self] using f.map_perm e σ
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 29.4s, verify 0.1s, in=2001, out=585)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [*, Basis.det_self, AlternatingMap.map_perm] using h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 100.3s, verify 0.1s, in=2029, out=4462)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm f σ, map_perm (e.det) σ, det_self], rw [smul_eq_mul]
```

**lean_error:** tail step 1/1 ('rw [map_perm f σ, map_perm (e.det) σ, det_self], rw [smul_eq_mul]'): <stdin>:1:47: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 106.3s, verify 0.2s, in=2029, out=4694)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm, map_perm e.det, det_self, smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm, map_perm e.det, det_self, smul_eq_mul, mul_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 127.5s, verify 0.2s, in=2029, out=5541)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm, map_perm, det_self, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [map_perm, map_perm, det_self, mul_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 139.2s, verify 0.1s, in=2029, out=6078)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm f σ, LinearMap.smul_apply, map_perm det e σ, det_self, smul_eq_mul]
apply mul_comm
```

**lean_error:** tail step 1/2 ('rw [map_perm f σ, LinearMap.smul_apply, map_perm det e σ, det_self, smul_eq_mul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.1s, verify 0.4s, in=2029, out=292)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_smul_basis_det]
```

**lean_error:** tail step 1/1 ('rw [eq_smul_basis_det]'): tactic 'rewrite' failed, pattern is a metavariable

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.5s, verify 0.3s, in=2029, out=397)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [e.det_self] using (map_perm f e σ).trans ((smul_smul _ _ _).trans (map_perm _ e σ).symm)
```

**lean_error:** tail step 1/1 ('simpa [e.det_self] using (map_perm f e σ).trans ((smul_smul _ _ _).trans (map_perm _ e σ).symm)'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 14.5s, verify 0.1s, in=2029, out=430)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map_perm, det_self]
```

**lean_error:** tail step 1/1 ('simp [map_perm, det_self]'): unknown identifier 'det_self'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.8s, verify 0.2s, in=2029, out=454)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [smul_apply, e.det.map_perm e σ, e.det_self, smul_comm] using f.map_perm e σ
```

**lean_error:** tail step 1/1 ('simpa only [smul_apply, e.det.map_perm e σ, e.det_self, smul_comm] using f.map_perm e σ'): tactic 'simp' failed, nested error:
