# CategoryTheory.isLocallySurjective_of_surjective   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Sites/Surjective.lean`  

**Ground-truth tail (from k):**
```lean
exact J.top_mem _
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.8s, verify 0.9s, in=373, out=398)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using J.top_mem U
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 33.8s, verify 0.1s, in=320, out=3871)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.maximal
```

**lean_error:** tail step 1/1 ('exact J.maximal'): invalid field 'maximal', the environment does not contain 'CategoryTheory.GrothendieckTopology.maximal'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=316, out=283)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```
