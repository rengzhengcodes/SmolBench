# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✓ ✘ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=291, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.algebraMap_eq]
congr
```

**lean_error:** tail step 1/2 ('rw [RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=291, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [RatFunc.ofFractionRing]
simp
```

**lean_error:** tail step 2/3 ('rw [RatFunc.ofFractionRing]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=291, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.algebraMap_eq],
congr,
ext,
simp only [FractionRing.algebraMap_apply]
```

**lean_error:** tail step 1/4 ('rw [RatFunc.algebraMap_eq],'): <stdin>:1:26: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=291, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.algebraMap_eq]
rw [IsLocalization.algebraMap_eq K[X] (nonZeroDivisors K[X])]
congr
```

**lean_error:** tail step 1/3 ('rw [RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=291, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=291, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=291, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=291, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=660, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one x, RatFunc.mk_one' x]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one x, RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=660, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one x, RatFunc.mk_one' x]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one x, RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 1.1s, verify 0.2s, in=660, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=660, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=660, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=660, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=660, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_one', mk_one]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=660, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ofFractionRing, mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [ofFractionRing, mk_one', mk_one]"): tactic 'rewrite' failed, equality or iff proof expected
