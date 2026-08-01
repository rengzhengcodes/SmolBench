# OrderEmbedding.birkhoffSet_apply   (k=1, 2 tactics total)

file: `Mathlib/Order/Birkhoff.lean`  

**Ground-truth tail (from k):**
```lean
convert rfl
```

**True premises at k:** `rfl`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=290, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.1s, verify 0.1s, in=263, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=279, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=596, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.2s, verify 0.1s, in=570, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.0s, in=585, out=2)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1078, out=3)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=1054, out=3)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1067, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1102, out=3)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=1131, out=3)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1091, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```
