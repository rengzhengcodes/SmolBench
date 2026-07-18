# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 97.3s, verify 0.1s, in=236, out=4144)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
rintro rfl,
refl,
intro h,
apply_fun pred at h,
rw [pred_succ ha] at h,
rw [pred_succ hb] at h,
exact h
```

**lean_error:** tail step 1/8 ('split,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 117.6s, verify 0.1s, in=236, out=5033)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
have h1 : a < succ b := by rw [h]; exact ha.lt_succ
have h2 : b < succ a := by rw [h]; exact hb.lt_succ
have a_le_b := (lt_succ_iff_le α).mp h1
have b_le_a := (lt_succ_iff_le α).mp h2
exact le_antisymm a_le_b b_le_a
intro h
rw h
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 181.2s, verify 0.1s, in=236, out=8050)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  intros h
  have : a ≤ b := (lt_succ_iff : a < succ b ↔ a ≤ b).1 (by rw [h]; exact lt_succ_self b hb)
  have : b ≤ a := (lt_succ_iff : b < succ a ↔ b ≤ a).1 (by rw [←h]; exact lt_succ_self a ha)
  exact le_antisymm this this
  rintro rfl
  exact congr_arg succ
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 193.1s, verify 0.1s, in=236, out=8542)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h
  apply le_antisymm
  · apply le_of_lt_succ
    rw [h]
    exact lt_succ a
  · apply le_of_lt_succ
    exact lt_succ b
· intro h
  rw [h]
```

**lean_error:** tail step 1/10 ('split'): tactic 'split' failed

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

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 62.9s, verify 0.1s, in=907, out=2711)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 84.8s, verify 0.1s, in=907, out=3608)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
refl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 128.0s, verify 0.2s, in=907, out=5487)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt]
rw [and_congr (succ_le_succ_iff_of_not_isMax ha hb) (not_congr (succ_lt_succ_iff_of_not_isMax ha hb))]
rw [← eq_iff_le_not_lt]
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 140.0s, verify 0.2s, in=907, out=6108)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
apply and_congr (Order.succ_le_succ_iff_of_not_isMax ha hb) (not_iff_not_of_iff (Order.succ_lt_succ_iff_of_not_isMax ha hb))
```

**lean_error:** tail step 2/2 ('apply and_congr (Order.succ_le_succ_iff_of_not_isMax ha hb) (not_iff_not_of_iff (Order.succ_lt_succ_iff_of_not_isMax ha hb))'): unknown identifier 'not_iff_not_of_iff'

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

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 158.9s, verify 0.2s, in=1618, out=4960)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
exact Iff.rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 173.8s, verify 0.1s, in=1618, out=4095)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 176.7s, verify 0.1s, in=1618, out=5068)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 226.0s, verify 0.3s, in=1618, out=6326)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb]
rw [Order.succ_lt_succ_iff_of_not_isMax ha hb]
rw [eq_iff_le_not_lt]
```

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

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 47.2s, verify 0.2s, in=1645, out=2066)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 86.7s, verify 0.1s, in=1645, out=3680)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb, succ_lt_succ_iff_of_not_isMax ha hb]
trivial
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 107.8s, verify 0.2s, in=1645, out=4616)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [succ_le_succ_iff_of_not_isMax ha hb]
rw [succ_lt_succ_iff_of_not_isMax ha hb]
trivial
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 145.7s, verify 0.2s, in=1645, out=6395)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb]
rw [Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

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
