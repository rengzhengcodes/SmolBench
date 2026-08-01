# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=308, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
rw [stdBasis_apply, LinearMap.comp_apply, proj_apply],
by_cases h : x = j,
simp only [h, if_true, eq_self_iff_true],
simp only [h, if_false]
```

**lean_error:** tail step 1/5 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=278, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [LinearMap.comp_apply, stdBasis_apply, proj_apply, diag_apply, Function.update]
split_ifs with h h <;> simp_all [h]
```

**lean_error:** tail step 2/3 ('simp only [LinearMap.comp_apply, stdBasis_apply, proj_apply, diag_apply, Function.update]'): unknown identifier 'diag_apply'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=297, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ext
intro x
apply dfinsupp.ext
simp [stdBasis, proj, LinearMap.comp_apply, diag]
```

**lean_error:** tail step 3/4 ('apply dfinsupp.ext'): unknown identifier 'dfinsupp.ext'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=687, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=646, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearMap.stdBasis_eq_pi_diag j]
simp [LinearMap.proj_pi]
```

**lean_error:** tail step 1/2 ('rw [← LinearMap.stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=676, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=1102, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1065, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.proj_pi (diag R φ) i, LinearMap.stdBasis_eq_pi_diag j]
```

**lean_error:** tail step 1/1 ('rw [← LinearMap.proj_pi (diag R φ) i, LinearMap.stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1091, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1126, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1133, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.proj_pi (diag R φ) i, LinearMap.stdBasis_eq_pi_diag j]
rfl
```

**lean_error:** tail step 1/2 ('rw [← LinearMap.proj_pi (diag R φ) i, LinearMap.stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=1115, out=304)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```
