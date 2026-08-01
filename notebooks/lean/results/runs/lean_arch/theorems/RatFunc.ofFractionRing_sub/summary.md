# RatFunc.ofFractionRing_sub   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Sub.sub, HSub.hSub, RatFunc.sub]
```

**True premises at k:** `Sub.sub`, `HSub.hSub`, `RatFunc.sub`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=263, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [Subtype.coe_mk]
rfl
```

**lean_error:** tail step 2/3 ('rw [Subtype.coe_mk]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=237, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [SubNegMonoid.sub_eq_add_neg, neg_toFractionRing, add_toFractionRing]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=252, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Subtype.ext
simpa using Sub.sub_apply
```

**lean_error:** tail step 1/2 ('apply Subtype.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=542, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
rw [RatFunc.sub]
refl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=508, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
simp only [RatFunc.sub, Sub.sub, HSub.hSub, RatFunc.mk_eq_mk, Subtype.mk.injEq]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=531, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Sub.sub
apply HSub.hSub
apply RatFunc.sub
```

**lean_error:** tail step 1/3 ('apply Sub.sub'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.2s, in=704, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
rw [RatFunc.sub]
congr
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=664, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
  simp [RatFunc.sub]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=693, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Sub.sub
apply HSub.hSub
apply RatFunc.sub
```

**lean_error:** tail step 1/3 ('apply Sub.sub'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=728, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
rw [RatFunc.sub]
congr
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=714, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
simp only [RatFunc.sub, RatFunc.mk_eq_mk, Sub.sub, HSub.hSub]
rfl
```

**lean_error:** tail step 1/3 ('ext'): no applicable extensionality theorem found for

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 65.5s, verify 0.1s, in=717, out=4113)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold RatFunc.sub
rfl
```

**lean_error:** tail step 1/2 ('unfold RatFunc.sub'): tactic 'unfold' failed to unfold 'RatFunc.sub' at
