# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✘ ✘ |
| `noise:3` | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=271, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [csSup_of_le, csInf_of_le, h]
```

**lean_error:** tail step 1/1 ('simp [csSup_of_le, csInf_of_le, h]'): unknown identifier 'csSup_of_le'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=271, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_csInf, csInf_cSup h hs]
```

**lean_error:** tail step 1/1 ('rw [sInf_eq_csInf, csInf_cSup h hs]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=271, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sSup_eq_csSup_of_bddAbove_of_nonempty h hs]
```

**lean_error:** tail step 1/1 ('simp [sSup_eq_csSup_of_bddAbove_of_nonempty h hs]'): unknown identifier 'sSup_eq_csSup_of_bddAbove_of_nonempty'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=271, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact sInf_Ici_eq_cSup s
```

**lean_error:** tail step 1/1 ('exact sInf_Ici_eq_cSup s'): unknown identifier 'sInf_Ici_eq_cSup'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.8s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=529, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=854, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=854, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=854, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=854, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [sInf_eq_csInf, sSup_eq_csSup, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [sInf_eq_csInf, sSup_eq_csSup, csInf_upper_bounds_eq_csSup h hs]'): unknown identifier 'sInf_eq_csInf'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.0s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=879, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=879, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]
```

**lean_error:** tail step 1/1 ('simp only [upperBounds, csInf_upper_bounds_eq_csSup h hs]'): simp made no progress
