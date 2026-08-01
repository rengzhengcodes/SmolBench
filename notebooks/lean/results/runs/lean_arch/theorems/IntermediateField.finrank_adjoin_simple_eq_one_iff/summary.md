# IntermediateField.finrank_adjoin_simple_eq_one_iff   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Adjoin.lean`  

**Ground-truth tail (from k):**
```lean
exact Set.singleton_subset_iff
```

**True premises at k:** `Set.singleton_subset_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | · |
| `hint:3` | ✓ | ✘ | · |
| `noise:3` | ✓ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=275, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff, Set.mem_coe]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('rw [Set.singleton_subset_iff, Set.mem_coe]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=243, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff, Subalgebra.mem_bot]
exact iff_of_eq (congr_arg (· ∈ (⊥ : Subalgebra F E)) (Algebra.algebraMap_eq F E α).symm)
```

**lean_error:** tail step 1/2 ('rw [Set.singleton_subset_iff, Subalgebra.mem_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=264, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Set.singleton_subset_iff, SetLike.coe_bot]
```

**lean_error:** tail step 1/1 ('simp [Set.singleton_subset_iff, SetLike.coe_bot]'): unknown constant 'SetLike.coe_bot'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=464, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=427, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Subalgebra.mem_toSubmodule, IntermediateField.toSubmodule_bot]
simp only [Set.singleton_subset_iff, Subalgebra.mem_toSubmodule]
```

**lean_error:** tail step 1/2 ('rw [← Subalgebra.mem_toSubmodule, IntermediateField.toSubmodule_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.4s, verify 0.1s, in=453, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff]
```

**final state (truncated):**
```
F : Type u_1
inst✝² : Field F
E : Type u_2
inst✝¹ : Field E
inst✝ : Algebra F E
α : E
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=577, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=540, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Subalgebra.mem_toSubalgebra]
simp only [Set.singleton_subset_iff, bot_toSubalgebra]
```

**lean_error:** tail step 1/2 ('rw [← Subalgebra.mem_toSubalgebra]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.4s, verify 0.1s, in=566, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff]
```

**final state (truncated):**
```
F : Type u_1
inst✝² : Field F
E : Type u_2
inst✝¹ : Field E
inst✝ : Algebra F E
α : E
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=601, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=576, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Subalgebra.mem_toSubmodule, IntermediateField.bot_toSubmodule, Set.singleton_subset_iff]
```

**lean_error:** tail step 1/1 ('rw [← Subalgebra.mem_toSubmodule, IntermediateField.bot_toSubmodule, Set.singleton_subset_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.5s, verify 0.1s, in=590, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff]
```

**final state (truncated):**
```
F : Type u_1
inst✝² : Field F
E : Type u_2
inst✝¹ : Field E
inst✝ : Algebra F E
α : E
...
```
