# wcovBy_iff_covBy_or_eq   (k=0, 1 tactics total)

file: `Mathlib/Order/Cover.lean`  

**Ground-truth tail (from k):**
```lean
rw [le_antisymm_iff, wcovBy_iff_covBy_or_le_and_le]
```

**True premises at k:** `le_antisymm_iff`, `wcovBy_iff_covBy_or_le_and_le`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=252, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  cases' h with h h
  · left
    assumption
  · right
    assumption
· intro h
  cases' h with h h
  · constructor
    assumption
  · constructor
    assumption
```

**lean_error:** tail step 2/13 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=224, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [⋖, le_antisymm_iff, or_comm]
simp [eq_comm]
```

**lean_error:** tail step 1/2 ('rw [⋖, le_antisymm_iff, or_comm]'): <stdin>:1:4: expected ']'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 42.8s, verify 0.1s, in=241, out=2681)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ intro h,
  cases eq_or_ne a b with heq hne,
  { right, exact heq },
  { left, exact hne.lt_of_le h } },
{ intro h,
  cases h with hlt heq,
  { exact hlt.le },
  { exact heq.le } }
```

**lean_error:** tail step 1/9 ('split,'): <stdin>:1:5: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=665, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.2s, in=634, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
simp_rw [← le_antisymm_iff]
aesop
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=654, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=804, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=774, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
simp_rw [le_antisymm_iff]
tauto
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=793, out=457)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=828, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff] 
simp only [or_and_right, or_assoc, or_self]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=813, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
simp_rw [le_antisymm_iff]
tauto!
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=817, out=357)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```
