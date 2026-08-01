# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.9s, in=262, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨λ h, _, λ h, _⟩
· exact (le_of_succ_le_succ h).antisymm (le_of_succ_le_succ h.symm)
· exact congr_arg succ h
```

**lean_error:** tail step 1/3 ("refine' ⟨λ h, _, λ h, _⟩"): <stdin>:1:12: expected '↦', '=>'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=236, out=61)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← succ_le_iff, ← succ_le_iff, le_antisymm_iff]
simp only [succ_le_iff, le_succ]
exact ⟨fun h => le_antisymm (le_of_not_lt h.2) (le_of_not_lt h.1), congr_arg _⟩
```

**lean_error:** tail step 1/3 ('rw [← succ_le_iff, ← succ_le_iff, le_antisymm_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=251, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
swap
. intro h
. exact succ_inj h
swap
. intro h
. exact congr_arg _ h
```

**lean_error:** tail step 3/7 ('. intro h'): unsolved goals

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 4.2s, verify 0.2s, in=933, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.3s, in=919, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
simp_rw [Order.succ_le_succ_iff_of_not_isMax ha hb]
simp_rw [Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=922, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=1640, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1640, out=46)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
simp_rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.4s, verify 0.2s, in=1629, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.8s, verify 1.4s, in=1668, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.4s, verify 0.4s, in=1735, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
simp_rw [Order.succ_le_succ_iff_of_not_isMax ha hb]
simp_rw [Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.5s, verify 0.2s, in=1657, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```
