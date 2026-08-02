# Filter.IsBasis.mem_filter_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsBasis.filter, FilterBasis.mem_filter_iff, mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**True premises at k:** `Filter.IsBasis.filter`, `FilterBasis.mem_filter_iff`, `Filter.IsBasis.mem_filterBasis_iff`, `exists_exists_and_eq_and`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=341, out=928)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using h.mem_iff
```

**lean_error:** tail step 1/1 ('simpa using h.mem_iff'): invalid field 'mem_iff', the environment does not contain 'Filter.IsBasis.mem_iff'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 189.5s, verify 0.1s, in=282, out=23957)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply mem_filterOfIsBasis
```

**lean_error:** tail step 1/1 ('apply mem_filterOfIsBasis'): unknown identifier 'mem_filterOfIsBasis'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=279, out=454)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsBasis.filter, Filter.generate_le_iff]
```

**lean_error:** tail step 1/1 ('simp [IsBasis.filter, Filter.generate_le_iff]'): unknown constant 'Filter.generate_le_iff'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=1091, out=1049)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**lean_error:** tail step 1/2 ('simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,'): <stdin>:1:79: unexpected end of input; expected '*' or '-'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 76.0s, verify 0.1s, in=1035, out=10157)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : U ∈ IsBasis.filter h ↔ ∃ s ∈ h.filterBasis, s ⊆ U := by
  have h₁₁ : IsBasis.filter h = h.filterBasis.filter := rfl
  rw [h₁₁]
  apply FilterBasis.mem_filter_iff
  
have h₂ : (∃ s ∈ h.filterBasis, s ⊆ U) ↔ (∃ i, p i ∧ s i ⊆ U) := by
  have h₂₁ : (∃ s ∈ h.filterBasis, s ⊆ U) ↔ (∃ s, s ∈ h.filterBasis ∧ s ⊆ U) := by rfl
  have h₂₂ : (∃ s, s ∈ h.filterBasis ∧ s ⊆ U) ↔ (∃ s, (∃ i, p i ∧ s i = s) ∧ s ⊆ U) := by
    apply Iff.congr
    · -- Forward direction
      intro h
      obtain ⟨s, hs, hsub⟩ := h
      have h₃ : ∃ i, p i ∧ s i = s := by
        have h₃₁ : s ∈ h.filterBasis ↔ ∃ i, p i ∧ s i = s := Filter.IsBasis.mem_filterBasis_iff
        have h₃₂ : ∃ i, p i ∧ s i = s := by
          rw [h₃₁] at hs
          exact hs
        exact h₃₂
      obtain ⟨i, hi, hs'⟩ := h₃
      refine' ⟨s, ⟨i, hi, hs'⟩, hsub⟩
    · -- Backward direction
      intro h
      obtain ⟨s, ⟨i, hi, hs'⟩, hsub⟩ := h
      have h₃ : s ∈ h.filterBasis := by
        have h₃₁ : s ∈ h.filterBasis ↔ ∃ i, p i ∧ s i = s := Filter.IsBasis.mem_filterBasis_iff
        have h₃₂ : ∃ i, p i ∧ s i = s := ⟨i, hi, hs'⟩
        rw [h₃₁]
        exact h₃₂
      exact ⟨s, h₃, hsub⟩
  have h₂₃ : (∃ s, (∃ i, p i ∧ s i = s) ∧ s ⊆ U) ↔ (∃ i, p i ∧ s i ⊆ U) := by
    apply exists_exists_and_eq_and
  rw [h₂₁]
  rw [h₂₂]
  rw [h₂₃]
  
have h₃ : U ∈ IsBasis.filter h ↔ (∃ i, p i ∧ s i ⊆ U) := by
  rw [h₁]
  rw [h₂]
  
exact h₃
```

**lean_error:** tail step 1/37 ('have h₁ : U ∈ IsBasis.filter h ↔ ∃ s ∈ h.filterBasis, s ⊆ U := by'): <stdin>:1:65: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 11.1s, verify 0.1s, in=999, out=1196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.IsBasis.filter, FilterBasis.mem_filter_iff, Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.2s, in=1942, out=1542)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 49.4s, verify 0.1s, in=1883, out=6371)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : U ∈ IsBasis.filter h ↔ U ∈ h.filterBasis.filter := by
  rw [Filter.IsBasis.filter]
  <;> rfl
have h₂ : U ∈ h.filterBasis.filter ↔ ∃ s ∈ h.filterBasis, s ⊆ U := by
  apply FilterBasis.mem_filter_iff
have h₃ : (∃ s ∈ h.filterBasis, s ⊆ U) ↔ ∃ i, p i ∧ s i ⊆ U := by
  constructor
  · -- Forward direction
    intro h
    obtain ⟨s, hs, hsub⟩ := h
    have h₄ : s ∈ h.filterBasis := hs
    have h₅ : s ⊆ U := hsub
    have h₆ : ∃ i, p i ∧ s i = s := by
      rw [Filter.IsBasis.mem_filterBasis_iff] at h₄
      exact h₄
    obtain ⟨i, pi, eqsi⟩ := h₆
    have h₇ : s i ⊆ U := by
      rw [eqsi] at h₅
      exact h₅
    exact ⟨i, pi, h₇⟩
  · -- Backward direction
    intro h
    obtain ⟨i, pi, hsub⟩ := h
    have h₄ : s i ∈ h.filterBasis := by
      rw [Filter.IsBasis.mem_filterBasis_iff]
      exact ⟨i, pi, rfl⟩
    exact ⟨s i, h₄, hsub⟩
have h₄ : U ∈ IsBasis.filter h ↔ ∃ i, p i ∧ s i ⊆ U := by
  rw [h₁]
  rw [h₂]
  rw [h₃]
exact h₄
```

**lean_error:** tail step 1/32 ('have h₁ : U ∈ IsBasis.filter h ↔ U ∈ h.filterBasis.filter := by'): <stdin>:1:63: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.3s, in=1866, out=617)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.IsBasis.filter]
rw [FilterBasis.mem_filter_iff]
rw [Filter.IsBasis.mem_filterBasis_iff]
simp [exists_exists_and_eq_and]
```

**lean_error:** tail step 3/4 ('rw [Filter.IsBasis.mem_filterBasis_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=1864, out=1304)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,
  exists_exists_and_eq_and]
```

**lean_error:** tail step 1/2 ('simpa [IsBasis.filter, FilterBasis.mem_filter_iff, IsBasis.mem_filterBasis_iff,'): <stdin>:1:79: unexpected end of input; expected '*' or '-'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 17.7s, verify 0.1s, in=2041, out=2339)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : U ∈ IsBasis.filter h ↔ U ∈ (h.filterBasis).filter := rfl
rw [h₁]
have h₂ : U ∈ (h.filterBasis).filter ↔ ∃ s ∈ h.filterBasis, s ⊆ U := FilterBasis.mem_filter_iff
rw [h₂]
have h₃ : (∃ s ∈ h.filterBasis, s ⊆ U) ↔ (∃ s, (∃ i, p i ∧ s i = s) ∧ s ⊆ U) := by
  constructor
  · intro h
    obtain ⟨s, hs, hsub⟩ := h
    have h₄ : s ∈ h.filterBasis := hs
    have h₅ : ∃ i, p i ∧ s i = s := by
      rw [Filter.IsBasis.mem_filterBasis_iff] at h₄
      exact h₄
    obtain ⟨i, hi, heq⟩ := h₅
    refine' ⟨s, ⟨i, hi, heq⟩, hsub⟩
  · intro h
    obtain ⟨s, ⟨i, hi, heq⟩, hsub⟩ := h
    have h₄ : s ∈ h.filterBasis := by
      rw [Filter.IsBasis.mem_filterBasis_iff]
      exact ⟨i, hi, heq⟩
    exact ⟨s, h₄, hsub⟩
rw [h₃]
have h₄ : (∃ s, (∃ i, p i ∧ s i = s) ∧ s ⊆ U) ↔ (∃ i, p i ∧ s i ⊆ U) := by
  apply exists_exists_and_eq_and
rw [h₄]
```

**lean_error:** tail step 1/24 ('have h₁ : U ∈ IsBasis.filter h ↔ U ∈ (h.filterBasis).filter := rfl'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.9s, verify 0.3s, in=1856, out=579)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.IsBasis.filter]
rw [FilterBasis.mem_filter_iff]
simp only [Filter.IsBasis.mem_filterBasis_iff, exists_exists_and_eq_and]
```
