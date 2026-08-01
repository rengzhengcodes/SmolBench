# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 1.6s, in=408, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_apply, Basis.equivFun]
simp only [Equiv.toFun_as_coe, Equiv.Perm.coe_mul]
rw [Basis.det_perm e σ]
simp only [Equiv.toFun_as_coe]
```

**lean_error:** tail step 1/4 ('rw [Basis.det_apply, Basis.equivFun]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.5s, in=372, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
conv_lhs => rw [← Basis.comp_alternatingMap_apply, Basis.det_comp_basis]
rw [Basis.alternatingMap_smul_apply, smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/2 ('conv_lhs => rw [← Basis.comp_alternatingMap_apply, Basis.det_comp_basis]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=397, out=129)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=892, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm e σ, Basis.det_self]
simp [MulAction.one_smul]
```

**lean_error:** tail step 1/2 ('rw [AlternatingMap.map_perm e σ, Basis.det_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=832, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, Basis.det_self, one_smul, ← AlternatingMap.comp_right_apply, ←
  AlternatingMap.comp_right_apply, Basis.comp]
simp [h]
```

**lean_error:** tail step 1/3 ('rw [AlternatingMap.map_perm, Basis.det_self, one_smul, ← AlternatingMap.comp_right_apply, ←'): <stdin>:1:91: unexpected end of input

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=881, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_perm, Basis.det_self, smul_comp, comp_smul, smul_smul, one_smul]
```

**lean_error:** tail step 1/1 ('rw [map_perm, Basis.det_self, smul_comp, comp_smul, smul_smul, one_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2022, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm e σ, Basis.det_self]
simp
rfl
```

**lean_error:** tail step 1/3 ('rw [AlternatingMap.map_perm e σ, Basis.det_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=1959, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, Basis.det_comp σ, Basis.det_self, one_smul, Equiv.Perm.sign_ofBijective _ h.bijective]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.map_perm, Basis.det_comp σ, Basis.det_self, one_smul, Equiv.Perm.sign_ofBijective _ h.bijective]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2011, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply AlternatingMap.map_perm (e ∘ σ) σ
rw [Equiv.Perm.sign_self σ, Basis.det_self, smul_one]
```

**lean_error:** tail step 1/2 ('apply AlternatingMap.map_perm (e ∘ σ) σ'): application type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=2047, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm, Basis.det_self, mul_one]
simp
```

**lean_error:** tail step 1/2 ('rw [map_perm, Basis.det_self, mul_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.6s, in=2119, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm, Basis.det_comp σ, Basis.det_self, mul_one, smul_eq_mul, mul_comm]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.map_perm, Basis.det_comp σ, Basis.det_self, mul_one, smul_eq_mul, mul_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=2036, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_perm, Basis.det_self, smul_comp, comp_smul, smul_smul, one_smul]
```

**lean_error:** tail step 1/1 ('rw [map_perm, Basis.det_self, smul_comp, comp_smul, smul_smul, one_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
