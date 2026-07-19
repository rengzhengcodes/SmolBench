# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.3s, in=296, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_antisymm _ _
rw [sInf_le]
intros a ha
exact ha _ hs
rw [le_sInf]
intros b hb
exact hb _ h
```

**lean_error:** tail step 2/7 ('rw [sInf_le]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.6s, verify 0.2s, in=296, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_antisymm _ _
rw sInf_le
rintro a ha
exact ha _ hs.some (hs.some_mem)
rw le_sInf
rintro x hx
exact hx _ (le_sSup hs h hx)
```

**lean_error:** tail step 2/7 ('rw sInf_le'): <stdin>:1:3: expected '['

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.8s, verify 0.2s, in=296, out=58)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_antisymm _ _
rw sInf_le_iff
intro a ha
exact ha _ hs.some (hs.some_mem s)
rw le_sInf_iff
intro b hb
exact hb _ hs.some (hs.some_mem s)
exact sSup_le h hb
```

**lean_error:** tail step 2/8 ('rw sInf_le_iff'): <stdin>:1:3: expected '['

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 4.0s, verify 0.3s, in=296, out=59)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_antisymm _ _
rw [sInf_le]
intro a ha
exact ha _ hs.some (hs.some_mem _)
rw [le_sInf]
intro b hb
exact hb (sSup s) (λ x hx, le_sSup hs hx)
```

**lean_error:** tail step 2/7 ('rw [sInf_le]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=296, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isGLB_sInf, isLUB_sSup]
```

**lean_error:** tail step 1/1 ('rw [isGLB_sInf, isLUB_sSup]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=296, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isLUB_sSup hs h, isLUB_le_iff]
```

**lean_error:** tail step 1/1 ('rw [isLUB_sSup hs h, isLUB_le_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=296, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isLUB_sSup h, IsLUB.sInf_eq]
```

**lean_error:** tail step 1/1 ('rw [isLUB_sSup h, IsLUB.sInf_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=296, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← iSup_eq_sSup h, iSup, iInf_eq_sInf, iInf]
```

**lean_error:** tail step 1/1 ('rw [← iSup_eq_sSup h, iSup, iInf_eq_sInf, iInf]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.6s, verify 0.1s, in=554, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=554, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds_def],
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds_def],'): <stdin>:1:20: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=554, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds_def]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds_def]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.0s, verify 0.1s, in=554, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('rw [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=554, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=554, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 0.9s, verify 0.1s, in=554, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=554, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```
