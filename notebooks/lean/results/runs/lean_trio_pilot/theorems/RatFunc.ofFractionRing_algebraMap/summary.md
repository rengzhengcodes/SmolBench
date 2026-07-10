# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=291, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [RatFunc.algebraMap_eq]
```

**lean_error:** tail step 2/2 ('rw [RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=291, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 52.1s, verify 0.1s, in=280, out=3977)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=271, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply AlgebraHom.toFun_inj
refl
```

**lean_error:** tail step 1/2 ('apply AlgebraHom.toFun_inj'): unknown identifier 'AlgebraHom.toFun_inj'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 12.8s, verify 0.1s, in=265, out=345)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=265, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.5s, in=660, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=660, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=649, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=640, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one', Algebra.ofFractionRing_algebraMap]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', Algebra.ofFractionRing_algebraMap]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 29.6s, verify 0.1s, in=634, out=1241)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=634, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("simp only [mk_one, mk_one']"): simp made no progress

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1848, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one', RatFunc.mk_one]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', RatFunc.mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=1848, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1837, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1828, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 69.9s, verify 0.1s, in=1825, out=3227)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one', RatFunc.mk_one]
```

**lean_error:** tail step 1/1 ("rw [RatFunc.mk_one', RatFunc.mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **success**  (gen 8.8s, verify 0.1s, in=1825, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1873, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one' x]
rw [RatFunc.mk_one x]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_one' x]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=1873, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1862, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one', algebraMap_eq]
```

**lean_error:** tail step 1/1 ("rw [mk_one', algebraMap_eq]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1853, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one', mk_one]
```

**lean_error:** tail step 1/1 ("rw [mk_one', mk_one]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 48.8s, verify 0.1s, in=1850, out=2208)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_one, mk_one']
```

**lean_error:** tail step 1/1 ("rw [mk_one, mk_one']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **success**  (gen 8.9s, verify 0.1s, in=1850, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← mk_one', mk_one]
```
