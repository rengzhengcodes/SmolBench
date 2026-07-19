# Filter.mem_inf_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✘ ✘ ✘ | ✓ ✘ ✓ · | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 48.8s, verify 0.1s, in=269, out=2466)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 68.3s, verify 0.1s, in=269, out=3672)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply filter.mem_congr,
ext x,
simp [mem_compl_iff, mem_union],
refl,
```

**lean_error:** tail step 1/4 ('apply filter.mem_congr,'): <stdin>:1:22: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 130.0s, verify 0.1s, in=269, out=6400)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have : tᶜ ∪ s = {x | x ∉ t ∨ x ∈ s} := by { ext x; simp [mem_union, mem_compl_iff]; tauto }
rw this
refl
```

**lean_error:** tail step 1/3 ('have : tᶜ ∪ s = {x | x ∉ t ∨ x ∈ s} := by { ext x; simp [mem_union, mem_compl_iff]; tauto }'): no goals to be solved

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 149.5s, verify 0.1s, in=269, out=7293)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Set.compl_eq, Set.union_eq]
```

**lean_error:** tail step 1/1 ('simp [Set.compl_eq, Set.union_eq]'): unknown constant 'Set.compl_eq'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.2s, verify 0.1s, in=269, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.6s, in=269, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [mem_union_eq, mem_compl_eq]
```

**lean_error:** tail step 1/1 ('simp only [mem_union_eq, mem_compl_eq]'): unknown identifier 'mem_union_eq'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=269, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.5s, verify 0.1s, in=269, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [compl_eq_univ_diff]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
f✝ g : Filter α
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.6s, verify 0.1s, in=269, out=179)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.3s, verify 0.1s, in=269, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.6s, verify 0.1s, in=269, out=215)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=269, out=259)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
