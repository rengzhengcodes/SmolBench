# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.2s, in=308, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext k
by_cases hk : k = j
· subst hk
  simp
· simp [stdBasis_ne _ _ _ hk]
```

**lean_error:** tail step 2/5 ('by_cases hk : k = j'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=308, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
  simp only [LinearMap.comp_apply, proj_apply, stdBasis_apply],
  split_ifs with h,
  { subst h, simp },
  { simp [diag] }
```

**lean_error:** tail step 1/5 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=308, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
rw [stdBasis_apply, LinearMap.comp_apply, proj_apply],
by_cases h : x = j,
simp only [h, Function.update_same, if_true],
simp only [Function.update_noteq h, if_false]
```

**lean_error:** tail step 1/5 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=308, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
rw [stdBasis_apply, LinearMap.comp_apply, proj_apply],
by_cases h : x = j,
simp only [h, if_true, Function.update_same],
simp only [if_false, Function.update_noteq h],
```

**lean_error:** tail step 1/5 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=308, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext; simp [Function.update_apply, stdBasis_apply]
```

**lean_error:** tail step 1/1 ('ext; simp [Function.update_apply, stdBasis_apply]'): <stdin>:1:3: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=308, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext k c; simp [Function.update_apply]
```

**lean_error:** tail step 1/1 ('ext k c; simp [Function.update_apply]'): <stdin>:1:7: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=308, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext k c; simp [stdBasis_apply, diag]
```

**lean_error:** tail step 1/1 ('ext k c; simp [stdBasis_apply, diag]'): <stdin>:1:7: expected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=308, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext; simp [Function.update_apply, stdBasis_apply]
```

**lean_error:** tail step 1/1 ('ext; simp [Function.update_apply, stdBasis_apply]'): <stdin>:1:3: expected end of input

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 0.7s, verify 0.2s, in=687, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.9s, verify 0.2s, in=687, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=687, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=687, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j]
rw [proj_pi (diag j) i]
```

**lean_error:** tail step 1/2 ('rw [stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=687, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=687, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=687, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=687, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [stdBasis_eq_pi_diag, proj_pi]
```
