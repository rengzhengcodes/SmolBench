# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 1.1s, in=291, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [RatFunc.algebraMap_eq]
```

**lean_error:** tail step 2/2 ('rw [RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=259, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.coe_algebraMap]
simp only [RingHom.toFun_eq_coe, FractionRing.algebraMap_mk']
rfl
```

**lean_error:** tail step 1/3 ('rw [RatFunc.coe_algebraMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=280, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Algebra.toFractionRing_eq_algebraMap
```

**lean_error:** tail step 1/1 ('apply Algebra.toFractionRing_eq_algebraMap'): unknown constant 'Algebra.toFractionRing_eq_algebraMap'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=660, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=615, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x, RatFunc.mk_one x]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=649, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=1848, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one', RatFunc.mk_one]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', RatFunc.mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.6s, in=1788, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x, RatFunc.mk_one]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1837, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=1873, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1964, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x, RatFunc.mk_one x]
rfl
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1862, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one', RatFunc.mk_one]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', RatFunc.mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
