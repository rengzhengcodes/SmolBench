# OrderEmbedding.birkhoffSet_apply   (k=1, 2 tactics total)

file: `Mathlib/Order/Birkhoff.lean`  

**Ground-truth tail (from k):**
```lean
convert rfl
```

**True premises at k:** `rfl`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=328, out=57)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=282, out=55)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=273, out=63)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=639, out=78)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=595, out=96)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=590, out=119)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1132, out=73)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=1089, out=324)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1095, out=139)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1101, out=94)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1195, out=84)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1104, out=102)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```
