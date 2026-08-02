# RatFunc.ofFractionRing_sub   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Sub.sub, HSub.hSub, RatFunc.sub]
```

**True premises at k:** `Sub.sub`, `HSub.hSub`, `RatFunc.sub`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=301, out=697)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 74.6s, verify 0.1s, in=246, out=10844)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases p
cases q
<;> rfl
```

**lean_error:** tail step 1/3 ('cases p'): tactic 'induction' failed, major premise type is not an inductive type 

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=249, out=398)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=604, out=601)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.6s, verify 0.1s, in=531, out=1094)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.sub]
<;> rfl
```

**lean_error:** tail step 1/2 ('rw [RatFunc.sub]'): failed to rewrite using equation theorems for 'RatFunc.sub'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=541, out=485)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [RatFunc.sub]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.sub]'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=763, out=340)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [RatFunc.sub]
```

**lean_error:** tail step 1/1 ('simpa [RatFunc.sub]'): tactic 'assumption' failed

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.8s, verify 0.1s, in=692, out=2074)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
<;> simp [RatFunc.sub]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=713, out=723)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=777, out=441)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 34.5s, verify 0.1s, in=753, out=4390)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [RatFunc.sub]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.sub]'): simp made no progress

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 299.5s, verify 0.0s, in=731, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
