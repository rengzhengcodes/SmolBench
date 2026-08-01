# RatFunc.ofFractionRing_zero   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Zero.zero, OfNat.ofNat, RatFunc.zero]
```

**True premises at k:** `Zero.zero`, `OfNat.ofNat`, `RatFunc.zero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=229, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [FractionRing.zero]
```

**lean_error:** tail step 2/2 ('rw [FractionRing.zero]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=203, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [Zero.zero, RatFunc.zero_def, RatFunc.coe_zero]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=218, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ext
simp
```

**lean_error:** tail step 1/2 ('apply ext'): unknown identifier 'ext'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 2.6s, verify 0.2s, in=464, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
rw [RatFunc.zero]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=431, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
simp [RatFunc.zero]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=453, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_arg (λ x, { toFractionRing := x }) (show 0 = 0, from rfl)
```

**lean_error:** tail step 1/1 ('exact congr_arg (λ x, { toFractionRing := x }) (show 0 = 0, from rfl)'): <stdin>:1:20: expected '↦', '=>'

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.8s, verify 0.2s, in=626, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
rw [RatFunc.zero]
refl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=587, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
simp [RatFunc.zero]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=615, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact congr_arg (RatFunc.mk) (show 0 = 0, by rfl)
```

**lean_error:** tail step 1/1 ('exact congr_arg (RatFunc.mk) (show 0 = 0, by rfl)'): <stdin>:1:40: expected 'by' or 'from'

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.9s, verify 0.2s, in=650, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
rw [RatFunc.zero]
refl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 1.2s, in=637, out=5)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=639, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply RatFunc.zero
```

**lean_error:** tail step 1/1 ('apply RatFunc.zero'): tactic 'apply' failed, failed to unify
