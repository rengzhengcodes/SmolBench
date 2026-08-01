# RatFunc.ofFractionRing_one   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [One.one, OfNat.ofNat, RatFunc.one]
```

**True premises at k:** `One.one`, `OfNat.ofNat`, `RatFunc.one`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [FractionRing.coe_one]
rfl
```

**lean_error:** tail step 2/3 ('rw [FractionRing.coe_one]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.2s, verify 0.1s, in=203, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=218, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Subtype.ext
simp
```

**lean_error:** tail step 1/2 ('apply Subtype.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.4s, in=467, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
rw [RatFunc.one]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=433, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.one]
rfl
```

**lean_error:** tail step 1/2 ('rw [RatFunc.one]'): failed to rewrite using equation theorems for 'RatFunc.one'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=456, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_arg (RatFunc.mk) (by simp)
```

**lean_error:** tail step 1/1 ('exact congr_arg (RatFunc.mk) (by simp)'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=629, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
rw [RatFunc.one]
refl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=589, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.one]
rfl
```

**lean_error:** tail step 1/2 ('rw [RatFunc.one]'): failed to rewrite using equation theorems for 'RatFunc.one'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=618, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply One.one
```

**lean_error:** tail step 1/1 ('apply One.one'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=653, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
rw [RatFunc.one]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=639, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.one]
rfl
```

**lean_error:** tail step 1/2 ('rw [RatFunc.one]'): failed to rewrite using equation theorems for 'RatFunc.one'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=642, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact congr_arg (RatFunc.mk) (by simp)
```

**lean_error:** tail step 1/1 ('exact congr_arg (RatFunc.mk) (by simp)'): type mismatch
