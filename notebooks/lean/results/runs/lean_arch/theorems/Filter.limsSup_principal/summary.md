# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=296, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' (csupₛ_le hs _).antisymm (le_cinfₛ _ _)
· exact fun x hx => h hx
· exact fun y hy x hx => hy x hx
```

**lean_error:** tail step 1/3 ("refine' (csupₛ_le hs _).antisymm (le_cinfₛ _ _)"): unknown identifier 'csupₛ_le'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=269, out=64)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_ciInf, ciInf_eq_of_forall_ge_of_forall_gt_exists_lt h (fun a => mem_upperBounds) hs]
  simp_rw [upperBounds, le_def]
  simp only [ciInf_le_iff hs, exists_prop, mem_setOf_eq]
  rfl
```

**lean_error:** tail step 1/4 ('rw [sInf_eq_ciInf, ciInf_eq_of_forall_ge_of_forall_gt_exists_lt h (fun a => mem_upperBounds) hs]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=285, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sSup_def, sInf_def]
simp [h, hs]
```

**lean_error:** tail step 1/2 ('rw [sSup_def, sInf_def]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=554, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.2s, in=525, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← csInf_upper_bounds_eq_csSup h hs]
simp [upperBounds]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=543, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=877, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=850, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← csInf_upper_bounds_eq_csSup h hs]
simp only [upperBounds, sInf]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=866, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): failed to rewrite using equation theorems for 'upperBounds'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=901, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [upperBounds_def]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds_def]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=909, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← csInf_upper_bounds_eq_csSup h hs]
congr
ext a
simp [upperBounds, le_def]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=890, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'
