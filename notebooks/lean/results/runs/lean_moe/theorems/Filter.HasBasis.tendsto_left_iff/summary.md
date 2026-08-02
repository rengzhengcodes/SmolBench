# Filter.HasBasis.tendsto_left_iff   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.3s, in=428, out=1618)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h t ht
  rcases h t ht with ⟨i, hi, hsub⟩
  refine ⟨i, hi, ?_⟩
  intro x hx
  exact hsub hx
· intro h t ht
  rcases h t ht with ⟨i, hi, hmap⟩
  refine ⟨i, hi, ?_⟩
  intro x hx
  simpa [Set.preimage] using hmap hx
```

**lean_error:** tail step 2/11 ('· intro h t ht'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.8s, verify 0.3s, in=366, out=2032)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro t ht
  obtain ⟨i, ⟨hipa, hsub⟩⟩ := h t ht
  have hmap : MapsTo f (sa i) t := MapsTo_iff_subset_preimage.mpr hsub
  exact ⟨i, ⟨hipa, hmap⟩⟩
· intro t ht
  obtain ⟨i, ⟨hipa, hmap⟩⟩ := h t ht
  have hsub : sa i ⊆ f ⁻¹' t := MapsTo_iff_subset_preimage.mp hmap
  exact ⟨i, ⟨hipa, hsub⟩⟩
```

**lean_error:** tail step 2/9 ('· intro t ht'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.9s, verify 0.3s, in=357, out=738)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h t ht
  obtain ⟨i, hi_pa, hi_subset⟩ := h t ht
  refine' ⟨i, hi_pa, _⟩
  rw [Set.mapsTo_iff_subset_preimage]
  exact hi_subset
· intro h t ht
  obtain ⟨i, hi_pa, hi_mapsTo⟩ := h t ht
  refine' ⟨i, hi_pa, _⟩
  rw [Set.mapsTo_iff_subset_preimage] at hi_mapsTo
  exact hi_mapsTo
```

**lean_error:** tail step 2/11 ('· intro h t ht'): unsolved goals
