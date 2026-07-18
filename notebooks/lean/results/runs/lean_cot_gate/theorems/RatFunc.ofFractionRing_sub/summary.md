# RatFunc.ofFractionRing_sub   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Sub.sub, HSub.hSub, RatFunc.sub]
```

**True premises at k:** `Sub.sub`, `HSub.hSub`, `RatFunc.sub`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 31.4s, verify 0.1s, in=238, out=1237)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext; rfl
```

**lean_error:** tail step 1/1 ('ext; rfl'): <stdin>:1:3: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 43.8s, verify 0.1s, in=238, out=1762)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 57.5s, verify 0.1s, in=238, out=2398)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 58.6s, verify 0.1s, in=238, out=2447)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=238, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=238, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=238, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=238, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 17.8s, verify 0.1s, in=517, out=702)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 21.4s, verify 0.1s, in=517, out=840)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 21.9s, verify 0.1s, in=517, out=859)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 115.4s, verify 0.1s, in=517, out=5126)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=517, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=517, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=517, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=517, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 28.5s, verify 0.1s, in=682, out=527)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 46.0s, verify 0.1s, in=682, out=901)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 84.0s, verify 0.1s, in=682, out=2877)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 93.7s, verify 0.1s, in=682, out=3193)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=682, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=682, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=682, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=682, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 15.1s, verify 0.1s, in=706, out=600)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 28.4s, verify 0.1s, in=706, out=1129)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 36.6s, verify 0.1s, in=706, out=1461)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 51.3s, verify 0.1s, in=706, out=2116)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext
rfl
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=706, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=706, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=706, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.3s, verify 0.1s, in=706, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch
