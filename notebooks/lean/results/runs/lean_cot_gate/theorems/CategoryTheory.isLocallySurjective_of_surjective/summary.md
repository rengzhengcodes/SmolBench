# CategoryTheory.isLocallySurjective_of_surjective   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Sites/Surjective.lean`  

**Ground-truth tail (from k):**
```lean
exact J.top_mem _
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✓ ✓ ✘ | ✓ ✓ ✓ ✘ | ✘ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 10.3s, verify 0.1s, in=295, out=435)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply J.top_mem_sieves
```

**lean_error:** tail step 1/1 ('apply J.top_mem_sieves'): invalid field 'top_mem_sieves', the environment does not contain 'CategoryTheory.GrothendieckTopology.top_mem_sieves'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 17.2s, verify 0.1s, in=295, out=728)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 18.1s, verify 0.1s, in=295, out=775)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 28.3s, verify 0.1s, in=295, out=1271)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply J.top_mem_sieves U
```

**lean_error:** tail step 1/1 ('apply J.top_mem_sieves U'): invalid field 'top_mem_sieves', the environment does not contain 'CategoryTheory.GrothendieckTopology.top_mem_sieves'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.7s, verify 0.1s, in=295, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=295, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=295, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=295, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.sieves.top_mem
```

**lean_error:** tail step 1/1 ('exact J.sieves.top_mem'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=295, out=109)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem
```

**lean_error:** tail step 1/1 ('exact J.top_mem'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 3.8s, verify 0.1s, in=295, out=116)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact J.top_mem U
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.9s, verify 0.1s, in=295, out=153)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 5.2s, verify 0.1s, in=295, out=162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply J.top_mem
```
