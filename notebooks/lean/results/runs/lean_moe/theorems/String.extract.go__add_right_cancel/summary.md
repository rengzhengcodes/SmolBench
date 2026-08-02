# String.extract.go₁_add_right_cancel   (k=7, 8 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact ih
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.3s, verify 0.4s, in=451, out=155)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ih
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 2.9s, verify 0.1s, in=396, out=280)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ih
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.6s, verify 0.1s, in=396, out=180)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ih
```
