# Lagrange.interpolate_eq_add_interpolate_erase   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact insert_subset_iff.mpr ⟨hi, singleton_subset_iff.mpr hj⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.2s, in=339, out=921)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro a ha
  simp [Finset.mem_pair] at ha
  rcases ha with h | h
  · simpa [h] using hi
  · simpa [h] using hj
```

**lean_error:** tail step 2/5 ('simp [Finset.mem_pair] at ha'): unknown constant 'Finset.mem_pair'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.1s, in=281, out=1477)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.subset_iff.mpr
intro x hx
simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hx
<;> tauto
```

**lean_error:** tail step 1/4 ('apply Set.subset_iff.mpr'): unknown constant 'Set.subset_iff.mpr'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=275, out=363)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hi, hj]
```

**lean_error:** tail step 1/1 ('simp [hi, hj]'): simp made no progress
