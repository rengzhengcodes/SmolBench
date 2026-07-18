# Filter.HasBasis.tendsto_left_iff   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 96.9s, verify 0.1s, in=354, out=3881)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [MapsTo_iff_subset_preimage]
```

**lean_error:** tail step 1/1 ('simp [MapsTo_iff_subset_preimage]'): unknown identifier 'MapsTo_iff_subset_preimage'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 125.4s, verify 0.1s, in=354, out=5027)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
{ intros H t ht
  obtain ⟨i, hpi, hsi⟩ := H t ht
  use i
  exact ⟨hpi, (image_subset_iff.2 hsi)⟩ }
{ intros H t ht
  obtain ⟨i, hpi, hsi⟩ := H t ht
  use i
  exact ⟨hpi, (image_subset_iff.1 hsi)⟩ }
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 130.3s, verify 0.1s, in=354, out=5229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply forall_congr', intro t, apply exists_congr, intro i, exact and_congr iff.rfl (image_subset_iff t (sa i)).symm
```

**lean_error:** tail step 1/1 ("apply forall_congr', intro t, apply exists_congr, intro i, exact and_congr iff.rfl (image_subset_iff t (sa i)).symm"): <stdin>:1:19: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 137.6s, verify 0.1s, in=354, out=5522)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply forall_congr' (λ t => exists_congr (λ i => and_congr iff.rfl (MapsTo.image_subset_iff (sa i) t).symm)))
```

**lean_error:** tail step 1/1 ("apply forall_congr' (λ t => exists_congr (λ i => and_congr iff.rfl (MapsTo.image_subset_iff (sa i) t).symm)))"): <stdin>:1:108: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=354, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=354, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.6s, verify 0.1s, in=354, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [MapsTo, Set.subset_def]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=354, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [MapsTo, Set.subset_def]
```
