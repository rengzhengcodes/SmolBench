# CategoryTheory.isLocallySurjective_of_surjective   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Sites/Surjective.lean`  

**Ground-truth tail (from k):**
```lean
exact J.top_mem _
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=329, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply J.top_mem_sieves
```

**lean_error:** tail step 1/1 ('apply J.top_mem_sieves'): invalid field 'top_mem_sieves', the environment does not contain 'CategoryTheory.GrothendieckTopology.top_mem_sieves'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=299, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← J.top_mem_iff_mem_sieves_top]
exact J.top_mem U.unop
```

**lean_error:** tail step 1/2 ('rw [← J.top_mem_iff_mem_sieves_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=318, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply J.top_mem
```
