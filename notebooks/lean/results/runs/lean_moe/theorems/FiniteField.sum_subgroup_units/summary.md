# FiniteField.sum_subgroup_units   (k=4, 5 tactics total)

file: `Mathlib/FieldTheory/Finite/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact sum_subgroup_units_eq_zero G_bot
```

**True premises at k:** `FiniteField.sum_subgroup_units_eq_zero`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.1s, verify 0.4s, in=341, out=3977)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using G.sum_eq_zero_of_ne_bot G_bot
```

**lean_error:** tail step 1/1 ('simpa using G.sum_eq_zero_of_ne_bot G_bot'): invalid field 'sum_eq_zero_of_ne_bot', the environment does not contain 'Subgroup.sum_eq_zero_of_ne_bot'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.5s, verify 1.0s, in=1085, out=551)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.5s, verify 0.1s, in=3031, out=1061)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot)
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=2799, out=858)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using FiniteField.sum_subgroup_units_eq_zero (K:=K) (G:=G) G_bot
```
