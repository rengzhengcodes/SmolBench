# Lagrange.interpolate_eq_add_interpolate_erase   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact insert_subset_iff.mpr ⟨hi, singleton_subset_iff.mpr hj⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=293, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Finset.insert_subset.2 (Finset.singleton_subset_iff.2 hj) hi
```

**lean_error:** tail step 1/1 ('exact Finset.insert_subset.2 (Finset.singleton_subset_iff.2 hj) hi'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=263, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Finset.insert_subset, Finset.singleton_subset_iff, hi, hj]
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.1s, verify 0.1s, in=282, out=509)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [hi, hj, Finset.singleton_subset_iff, Finset.union_subset]
```

**lean_error:** tail step 1/1 ('simp only [hi, hj, Finset.singleton_subset_iff, Finset.union_subset]'): simp made no progress
