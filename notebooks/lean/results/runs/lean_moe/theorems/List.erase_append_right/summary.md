# List.erase_append_right   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact h h'
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=312, out=85)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (h h')
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=256, out=129)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h h'
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=251, out=219)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h h'
```
