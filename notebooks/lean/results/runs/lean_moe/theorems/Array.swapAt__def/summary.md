# Array.swapAt!_def   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [swapAt!, h]
```

**True premises at k:** `Array.swapAt!`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.6s, in=307, out=1250)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=557, out=708)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Array.swapAt!, h, Array.swapAt]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=2101, out=428)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Array.swapAt!, h, swapAt]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=1967, out=672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Array.swapAt!, Array.swapAt, h]
```
