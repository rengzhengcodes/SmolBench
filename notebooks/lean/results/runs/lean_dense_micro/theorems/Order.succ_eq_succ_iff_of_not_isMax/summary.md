# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.2s, verify 0.1s, in=262, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨λ h, _, λ h, _⟩
· exact succ_inj ha hb h
· exact congr_arg succ h
```

**lean_error:** tail step 1/3 ("refine' ⟨λ h, _, λ h, _⟩"): <stdin>:1:12: expected '↦', '=>'

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 4.0s, verify 0.2s, in=262, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  have := le_of_succ_le_succ h.le
  have := le_of_succ_le_succ h.symm.le
  exact le_antisymm this this
· exact congr_arg succ
```

**lean_error:** tail step 2/6 ('· intro h'): unsolved goals

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 1.1s, in=262, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨λ h, _, λ h, _⟩
· exact (le_antisymm (succ_le_succ_iff.2 (le_of_succ_le_succ h)) (succ_le_succ_iff.2 (le_of_succ_le_succ h.symm)))
· exact congr_arg succ h
```

**lean_error:** tail step 1/3 ("refine' ⟨λ h, _, λ h, _⟩"): <stdin>:1:12: expected '↦', '=>'

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 5.3s, verify 0.2s, in=262, out=82)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  have h' := succ_le_succ_iff_le.mp (le_of_eq h)
  cases' le_iff_lt_or_eq.mp h' with hlt heq
  · exfalso
    exact ha (is_max_iff_not_lt.mpr (not_lt_of_le hlt))
  · exact heq
· intro h
  exact congr_arg succ h
```

**lean_error:** tail step 2/9 ('· intro h'): unsolved goals

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.9s, in=262, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsMax.succ_eq hb, ← IsMax.succ_eq ha]
```

**lean_error:** tail step 1/1 ('rw [← IsMax.succ_eq hb, ← IsMax.succ_eq ha]'): tactic 'rewrite' failed, pattern is a metavariable

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.1s, in=262, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsMax.succ_eq_iff (not_isMax_iff.mp ha) (not_isMax_iff.mp hb)]
```

**lean_error:** tail step 1/1 ('rw [← IsMax.succ_eq_iff (not_isMax_iff.mp ha) (not_isMax_iff.mp hb)]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=262, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← isMax_iff_succ_eq.mpr ha, ← isMax_iff_succ_eq.mpr hb, isMax_iff_succ_eq]
```

**lean_error:** tail step 1/1 ('rw [← isMax_iff_succ_eq.mpr ha, ← isMax_iff_succ_eq.mpr hb, isMax_iff_succ_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=262, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, succ_le_succ_iff_of_not_is_max hb, succ_lt_succ_iff_of_not_is_max ha,
  not_lt]
```

**lean_error:** tail step 1/2 ('rw [eq_iff_le_not_lt, succ_le_succ_iff_of_not_is_max hb, succ_lt_succ_iff_of_not_is_max ha,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 3.3s, verify 0.1s, in=933, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 3.5s, verify 0.2s, in=933, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 3.7s, verify 0.2s, in=933, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 3.8s, verify 0.2s, in=933, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 2.6s, verify 0.1s, in=933, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 2.6s, verify 0.1s, in=933, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.1s, in=933, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:76: unexpected end of input; expected ']'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=933, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:76: unexpected end of input; expected ']'
