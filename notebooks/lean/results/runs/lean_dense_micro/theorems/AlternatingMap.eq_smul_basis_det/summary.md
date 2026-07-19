# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.2s, in=408, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_apply]
rw [Basis.det_self]
rw [mul_one]
rw [AlternatingMap.comp]
congr
```

**lean_error:** tail step 1/5 ('rw [Basis.det_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=408, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_apply, Basis.equivFun]
simp only [Equiv.coe_ofBijective, Equiv.Perm.coe_ofBijective]
```

**lean_error:** tail step 1/2 ('rw [Basis.det_apply, Basis.equivFun]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.8s, verify 0.2s, in=408, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_apply, Basis.equivFun]
congr
rw [Equiv.Perm.coe_mul, Equiv.Perm.coe_inv]
ext
simp
```

**lean_error:** tail step 1/5 ('rw [Basis.det_apply, Basis.equivFun]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=408, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_comp]
rw [Equiv.Perm.coe_comp]
rw [Basis.comp_perm]
rw [Basis.det_comp]
rw [comp_comp]
rw [comp_id]
congr
exact Basis.det_perm e σ
```

**lean_error:** tail step 1/8 ('rw [Basis.det_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=408, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Basis.det_apply e f σ
```

**lean_error:** tail step 1/1 ('exact Basis.det_apply e f σ'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **incomplete**  (gen 1.0s, verify 0.2s, in=408, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.det_apply]
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

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=408, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact f.map_basis_leibniz e σ
```

**lean_error:** tail step 1/1 ('exact f.map_basis_leibniz e σ'): invalid field 'map_basis_leibniz', the environment does not contain 'AlternatingMap.map_basis_leibniz'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=408, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Equiv.Perm.coe_mul, Basis.det_apply, Basis.det_apply, Basis.equivDet_apply,
  Basis.equivDet_apply, ← f.map_smul, Basis.det_comp, Basis.det_comp, mul_inv_rev]
```

**lean_error:** tail step 1/2 ('rw [Equiv.Perm.coe_mul, Basis.det_apply, Basis.det_apply, Basis.equivDet_apply,'): <stdin>:1:79: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=892, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, Basis.det_self]
simp
```

**lean_error:** tail step 1/2 ('rw [AlternatingMap.map_perm, Basis.det_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.9s, verify 0.2s, in=892, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, Basis.det_self, one_smul]
```

**lean_error:** tail step 1/1 ('rw [map_perm, Basis.det_self, one_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.1s, verify 0.2s, in=892, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm e σ]
simp [Basis.det_self]
```

**lean_error:** tail step 1/2 ('rw [AlternatingMap.map_perm e σ]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.3s, verify 0.2s, in=892, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm e σ, Basis.det_self, one_smul]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.map_perm e σ, Basis.det_self, one_smul]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=892, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [f.map_perm e σ, Basis.det_self, mul_one]
```

**lean_error:** tail step 1/1 ('simp_rw [f.map_perm e σ, Basis.det_self, mul_one]'): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=892, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, Basis.det_self, mul_one, smul_one]
```

**lean_error:** tail step 1/1 ('rw [map_perm, Basis.det_self, mul_one, smul_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=892, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [f.map_perm e σ, Basis.det_self, mul_one]
```

**lean_error:** tail step 1/1 ('simp_rw [f.map_perm e σ, Basis.det_self, mul_one]'): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=892, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [AlternatingMap.map_perm, Basis.det_self, mul_one, one_smul]
```

**lean_error:** tail step 1/1 ('simp_rw [AlternatingMap.map_perm, Basis.det_self, mul_one, one_smul]'): simp made no progress
