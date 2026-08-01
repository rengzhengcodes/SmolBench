# Array.getElem_map   (k=4, 5 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp_all
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=293, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eq] at h,
exact h
```

**lean_error:** tail step 1/2 ('rw [eq] at h,'): <stdin>:1:12: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.2s, verify 0.2s, in=267, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← eq]
assumption
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.3s, verify 0.2s, in=282, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eq] at h
exact h
```
