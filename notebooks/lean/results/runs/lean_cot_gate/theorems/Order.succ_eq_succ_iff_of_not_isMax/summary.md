# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ ✘ ✓ ✘ |
| `noise:3` | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.3s, in=236, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [succ_ne_succ_iff ha hb, and_self_iff]
```

**lean_error:** tail step 1/1 ('rw [succ_ne_succ_iff ha hb, and_self_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=236, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [succ_inj_of_not_isMax_of_not_isMax ha hb]
```

**lean_error:** tail step 1/1 ('simp [succ_inj_of_not_isMax_of_not_isMax ha hb]'): unknown identifier 'succ_inj_of_not_isMax_of_not_isMax'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=236, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [succ_le_succ_iff, ha, hb]
```

**lean_error:** tail step 1/1 ('simp [succ_le_succ_iff, ha, hb]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=236, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← pred_succ a, ← pred_succ b, pred_inj (succ_ne_min _)]
```

**lean_error:** tail step 1/1 ('rw [← pred_succ a, ← pred_succ b, pred_inj (succ_ne_min _)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=907, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=907, out=40)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [eq_iff_le_not_lt, Order.succ_le_succ_iff_of_not_isMax ha hb,
  Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp [eq_iff_le_not_lt, Order.succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:66: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.9s, verify 0.1s, in=907, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.4s, verify 0.1s, in=907, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.1s, verify 0.1s, in=1618, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=1618, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.3s, verify 0.1s, in=1618, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=1618, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.6s, verify 0.1s, in=1645, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1645, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1645, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp only [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:65: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=1645, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simp_rw [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:63: unexpected end of input; expected ']'
