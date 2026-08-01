# ciSup_partialSups_eq   (k=3, 4 tactics total)

file: `Mathlib/Order/PartialSups.lean`  

**Ground-truth tail (from k):**
```lean
rwa [bddAbove_range_partialSups]
```

**True premises at k:** `bddAbove_range_partialSups`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=265, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' (csupr_le_iff $ h.isBounded (partialSups f)).mpr h
exact (partialSups_le f).trans h
```

**lean_error:** tail step 1/2 ("refine' (csupr_le_iff $ h.isBounded (partialSups f)).mpr h"): unknown identifier 'csupr_le_iff'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=238, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [partialSups_eq_cSup_range, BddAbove, ← image_univ]
exact (image_mono (range_mono Nat.mono_le_of_le_succ) h)
```

**lean_error:** tail step 1/2 ('rw [partialSups_eq_cSup_range, BddAbove, ← image_univ]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.1s, in=254, out=467)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply h_bdd_above_partial_sups
```

**lean_error:** tail step 1/1 ('apply h_bdd_above_partial_sups'): unknown identifier 'h_bdd_above_partial_sups'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=535, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.2s, in=509, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [bddAbove_range_partialSups]
exact h
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=524, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply bddAbove_range_partialSups.mpr
assumption
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1191, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.2s, in=1167, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [bddAbove_range_partialSups]
exact h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=1180, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply bddAbove_range_partialSups.mpr
exact h
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1218, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (bddAbove_range_partialSups.2 h)
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=1269, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1207, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```
