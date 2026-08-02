# IntermediateField.finrank_adjoin_simple_eq_one_iff   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Adjoin.lean`  

**Ground-truth tail (from k):**
```lean
exact Set.singleton_subset_iff
```

**True premises at k:** `Set.singleton_subset_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✘ |
| `hint:2` | ✓ | ✘ | · |
| `hint:3` | ✓ | ✓ | · |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=321, out=1298)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (singleton_subset_iff (a:=α) (s:= (↑(⊥ : IntermediateField F E))))
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 8.9s, verify 0.1s, in=266, out=1004)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=260, out=406)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [singleton_subset_iff]
```

**lean_error:** tail step 1/1 ('rw [singleton_subset_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=528, out=800)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Set.singleton_subset_iff]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 15.1s, verify 0.1s, in=477, out=1831)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff]
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.6s, verify 0.1s, in=459, out=528)

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

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.3s, verify 0.2s, in=649, out=1088)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (Set.singleton_subset_iff : {α} ⊆ (↑(⊥ : IntermediateField F E)) ↔ α ∈ (⊥ : IntermediateField F E))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 85.4s, verify 0.2s, in=600, out=12057)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.singleton_subset_iff]
rfl
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.2s, verify 0.1s, in=576, out=492)

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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.3s, verify 0.1s, in=657, out=820)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (Set.singleton_subset_iff : ({α} ⊆ (↑⊥ : Set E)) ↔ α ∈ (↑⊥ : Set E))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 9.6s, verify 0.1s, in=638, out=1102)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=600, out=581)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.singleton_subset_iff
```
