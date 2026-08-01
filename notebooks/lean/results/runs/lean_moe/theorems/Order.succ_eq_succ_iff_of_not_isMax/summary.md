# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.7s, verify 0.2s, in=304, out=1951)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact succ_injective h
· intro h
  simpa [h]
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=1055, out=1156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [eq_iff_le_not_lt,
  succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/3 ('simpa [eq_iff_le_not_lt,'): <stdin>:1:24: unexpected end of input; expected '*' or '-'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.2s, in=1830, out=1480)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  have h₁ : succ a ≤ succ b := by
    simpa [h]
  have h₂ : succ b ≤ succ a := by
    simpa [h]
  have ha_le : a ≤ b := (succ_le_succ_iff_of_not_isMax ha hb).1 h₁
  have hb_le : b ≤ a := (succ_le_succ_iff_of_not_isMax hb ha).1 h₂
  exact le_antisymm ha_le hb_le
· intro h
  simpa [h]
```

**lean_error:** tail step 2/11 ('· intro h'): unsolved goals

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=1727, out=958)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
    succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simpa [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:61: unexpected end of input; expected '*' or '-'
