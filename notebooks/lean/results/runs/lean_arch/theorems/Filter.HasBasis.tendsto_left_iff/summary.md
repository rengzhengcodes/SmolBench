# Filter.HasBasis.tendsto_left_iff   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.3s, in=374, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h t ht
  obtain ⟨i, hi, h⟩ := h t ht
  exact ⟨i, hi, subset.mapsTo f h⟩
· intro h t ht
  obtain ⟨i, hi, h⟩ := h t ht
  exact ⟨i, hi, mapsTo.preimage h⟩
```

**lean_error:** tail step 2/7 ('· intro h t ht'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=340, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [← MapsTo.preimage_eq_iff, ← mem_preimage, hla.mem_iff]
simp only [mem_preimage, MapsTo]
rw [iff_self]
```

**lean_error:** tail step 1/3 ('simp_rw [← MapsTo.preimage_eq_iff, ← mem_preimage, hla.mem_iff]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 48.8s, verify 0.1s, in=363, out=3038)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply forall_congr
intro t
apply imp_congr_right
apply exists_congr
intro i
apply and_congr
refl
apply image_subset_iff
```

**lean_error:** tail step 1/8 ('apply forall_congr'): tactic 'apply' failed, failed to unify
