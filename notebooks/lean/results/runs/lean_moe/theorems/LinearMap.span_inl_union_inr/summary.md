# LinearMap.span_inl_union_inr   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [span_union, prod_eq_sup_map, ← span_image, ← span_image]
```

**True premises at k:** `Submodule.span_union`, `LinearMap.prod_eq_sup_map`, `Submodule.span_image`, `Submodule.span_image`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 28.6s, verify 0.3s, in=508, out=6062)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
  ·
    refine span_le.2 ?hsubset
    intro x hx
    rcases hx with hx | hx
    · rcases hx with ⟨m, hm, rfl⟩
      exact
        (Submodule.mem_prod).2
          ⟨Submodule.subset_span hm,
           by
             simpa using (Submodule.zero_mem (span R t))⟩
    · rcases hx with ⟨m, hm, rfl⟩
      exact
        (Submodule.mem_prod).2
          ⟨by
             simpa using (Submodule.zero_mem (span R s)),
           Submodule.subset_span hm⟩
  ·
    intro x hx
    rcases Submodule.mem_prod.1 hx with ⟨hx1, hx2⟩
    cases x with
    | mk a b =>
      have ha' : (a, (0 : M₂)) ∈
          span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) := by
        refine Submodule.span_induction hx1 ?hs1 ?h0_1 ?hadd1 ?hsmul1
        · intro m hm
          have : (m, (0 : M₂)) ∈
              (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) := by
            left
            exact ⟨m, hm, rfl⟩
          exact Submodule.subset_span this
        · simpa using (Submodule.zero_mem _)
        · intro u v hu hv
          simpa using Submodule.add_mem _ hu hv
        · intro c u hu
          simpa using Submodule.smul_mem _ c hu
      have hb' : ((0 : M), b) ∈
          span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) := by
        refine Submodule.span_induction hx2 ?hs2 ?h0_2 ?hadd2 ?hsmul2
        · intro n hn
          have : ((0 : M), n) ∈
              (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) := by
            right
            exact ⟨n, hn, rfl⟩
          exact Submodule.subset_span this
        · simpa using (Submodule.zero_mem _)
        · intro u v hu hv
          simpa using Submodule.add_mem _ hu hv
        · intro c u hu
          simpa using Submodule.smul_mem _ c hu
      have : (a, (0 : M₂)) + ((0 : M), b) ∈
          span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) :=
        Submodule.add_mem _ ha' hb'
      simpa using this
```

**lean_error:** tail step 2/54 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 52.3s, verify 0.1s, in=471, out=5952)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem your_theorem_name : span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t) := by
  have h_main : span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t) := by
    calc
      span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = span R (⇑(inl R M M₂) '' s) + span R (⇑(inr R M M₂) '' t) := by
        rw [span_union]
      _ = (inl R M M₂).map (span R s) + (inr R M M₂).map (span R t) := by
        rw [span_image, span_image]
      _ = Submodule.prod (span R s) ⊥ + Submodule.prod ⊥ (span R t) := by
        rw [Submodule.map_prod_mk_inl, Submodule.map_prod_mk_inr]
      _ = Submodule.prod (span R s) (span R t) := by
        rw [Submodule.prod_add_prod]
  exact h_main
```

**lean_error:** tail step 1/12 ("theorem your_theorem_name : span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t) := by"): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.3s, verify 0.7s, in=459, out=941)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Submodule.ext
intro x
constructor
· intro hx
  rw [Submodule.mem_span_union] at hx
  rcases hx with ⟨y, hy, rfl⟩ | ⟨y, hy, rfl⟩
  · exact ⟨y, Submodule.mem_span.mpr hy, 0, by simp, by simp⟩
  · exact ⟨0, by simp, y, Submodule.mem_span.mpr hy, by simp⟩
· intro hx
  rcases hx with ⟨y, hy, z, hz, rfl⟩
  rw [Submodule.mem_span_union]
  left
  exact Submodule.mem_span.mpr ⟨y, hy, rfl⟩
```

**lean_error:** tail step 4/13 ('· intro hx'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=1180, out=1401)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union,
      Submodule.span_image (f := LinearMap.inl R M M₂) (s := s),
      Submodule.span_image (f := LinearMap.inr R M M₂) (s := t),
      LinearMap.prod_eq_sup_map]
  rfl
```

**lean_error:** tail step 1/5 ('rw [span_union,'): <stdin>:1:15: unexpected end of input; expected ']'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.7s, verify 0.1s, in=1169, out=9756)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : span R ( (⇑(inl R M M₂) '' s) ∪ (⇑(inr R M M₂) '' t) ) = span R (⇑(inl R M M₂) '' s) ⊔ span R (⇑(inr R M M₂) '' t) := by
  rw [span_union]
have h2 : span R (⇑(inl R M M₂) '' s) = (span R s).map (⇑(inl R M M₂)) := by
  rw [← map_span]
have h3 : span R (⇑(inr R M M₂) '' t) = (span R t).map (⇑(inr R M M₂)) := by
  rw [← map_span]
have h4 : (span R s).prod (span R t) = (span R s).map (⇑(inl R M M₂)) ⊔ (span R t).map (⇑(inr R M M₂)) := by
  rw [LinearMap.prod_eq_sup_map]
calc
  span R ( (⇑(inl R M M₂) '' s) ∪ (⇑(inr R M M₂) '' t) ) = span R (⇑(inl R M M₂) '' s) ⊔ span R (⇑(inr R M M₂) '' t) := h1
  _ = (span R s).map (⇑(inl R M M₂)) ⊔ (span R t).map (⇑(inr R M M₂)) := by rw [h2, h3]
  _ = (span R s).prod (span R t) := by rw [h4]
```

**lean_error:** tail step 1/12 ("have h1 : span R ( (⇑(inl R M M₂) '' s) ∪ (⇑(inr R M M₂) '' t) ) = span R (⇑(inl R M M₂) '' s) ⊔ span R (⇑(inr R M M₂) '' t) := by"): <stdin>:1:130: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.4s, in=1134, out=520)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [span_union]
rw [span_image, span_image]
rw [← LinearMap.prod_eq_sup_map]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.3s, in=2025, out=1547)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Submodule.span_union, Submodule.span_image, LinearMap.prod_eq_sup_map]
```

**lean_error:** tail step 1/1 ('simpa [Submodule.span_union, Submodule.span_image, LinearMap.prod_eq_sup_map]'): tactic 'assumption' failed

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 141.8s, verify 0.1s, in=2021, out=16685)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : span R (⇑(inl R M M₂) '' s) = ⇑(inl R M M₂) (span R s) := by
  haveI : RingHomSurjective (RingHom.id : R →+* R) := ⟨fun y => ⟨y, by simp⟩⟩
  let f : M →ₗ[(1 : R →+* R)] (M × M₂) := LinearMap.mapId (inl R M M₂)
  have h₁₀ : span R (f '' s) = map f (span R s) := by
    apply Submodule.span_image
  have h₁₁ : (f '' s : Set (M × M₂)) = ((inl R M M₂) '' s : Set (M × M₂)) := by
    ext x
    simp [LinearMap.mapId_apply]
    <;>
    aesop
  have h₁₂ : span R (f '' s) = span R ((inl R M M₂) '' s) := by
    rw [h₁₁]
  have h₁₃ : (map f (span R s) : Set (M × M₂)) = ((inl R M M₂) '' (span R s) : Set (M × M₂)) := by
    ext x
    simp [LinearMap.mapId_apply, Map.image]
    <;>
    aesop
  have h₁₄ : map f (span R s) = (inl R M M₂) (span R s) := by
    apply Submodule.ext
    rw [h₁₃]
  have h₁₅ : span R ((inl R M M₂) '' s) = span R (f '' s) := by
    rw [h₁₁]
  have h₁₆ : span R (f '' s) = map f (span R s) := h₁₀
  have h₁₇ : map f (span R s) = (inl R M M₂) (span R s) := h₁₄
  linarith

have h₂ : span R (⇑(inr R M M₂) '' t) = ⇑(inr R M M₂) (span R t) := by
  haveI : RingHomSurjective (RingHom.id : R →+* R) := ⟨fun y => ⟨y, by simp⟩⟩
  let f : M₂ →ₗ[(1 : R →+* R)] (M × M₂) := LinearMap.mapId (inr R M M₂)
  have h₂₀ : span R (f '' t) = map f (span R t) := by
    apply Submodule.span_image
  have h₂₁ : (f '' t : Set (M × M₂)) = ((inr R M M₂) '' t : Set (M × M₂)) := by
    ext x
    simp [LinearMap.mapId_apply]
    <;>
    aesop
  have h₂₂ : span R (f '' t) = span R ((inr R M M₂) '' t) := by
    rw [h₂₁]
  have h₂₃ : (map f (span R t) : Set (M × M₂)) = ((inr R M M₂) '' (span R t) : Set (M × M₂)) := by
    ext x
    simp [LinearMap.mapId_apply, Map.image]
    <;>
    aesop
  have h₂₄ : map f (span R t) = (inr R M M₂) (span R t) := by
    apply Submodule.ext
    rw [h₂₃]
  have h₂₅ : span R ((inr R M M₂) '' t) = span R (f '' t) := by
    rw [h₂₁]
  have h₂₆ : span R (f '' t) = map f (span R t) := h₂₀
  have h₂₇ : map f (span R t) = (inr R M M₂) (span R t) := h₂₄
  linarith

calc
  span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = span R (⇑(inl R M M₂) '' s) ⊔ span R (⇑(inr R M M₂) '' t) := by
    rw [Submodule.span_union]
  _ = (⇑(inl R M M₂) (span R s)) ⊔ (⇑(inr R M M₂) (span R t)) := by rw [h₁, h₂]
  _ = (span R s).map (LinearMap.inl R M M₂) ⊔ (span R t).map (LinearMap.inr R M M₂) := by rfl
  _ = (span R s).prod (span R t) := by
    rw [← LinearMap.prod_eq_sup_map]
```

**lean_error:** tail step 1/57 ("have h₁ : span R (⇑(inl R M M₂) '' s) = ⇑(inl R M M₂) (span R s) := by"): <stdin>:1:70: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 9.9s, verify 0.4s, in=1944, out=886)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Submodule.span_union]
rw [Submodule.span_image, Submodule.span_image]
rw [← LinearMap.prod_eq_sup_map]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.1s, in=1912, out=3255)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.span_union (R:=R)
        (s:= (LinearMap.inl R M M₂) '' s)
        (t:= (LinearMap.inr R M M₂) '' t)]
  rw [Submodule.span_image (R:=R) (R₂:=R) (f:=LinearMap.inl R M M₂) (s:=s),
      Submodule.span_image (R:=R) (R₂:=R) (f:=LinearMap.inr R M M₂) (s:=t)]
  rw [← LinearMap.prod_eq_sup_map (p:=span R s) (q:=span R t)]
  rfl
```

**lean_error:** tail step 1/7 ('rw [Submodule.span_union (R:=R)'): <stdin>:1:31: unexpected end of input; expected ']'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 100.4s, verify 0.3s, in=2120, out=11846)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.span_union]
rw [Submodule.span_image (inl R M M₂) s]
rw [Submodule.span_image (inr R M M₂) t]
rw [LinearMap.prod_eq_sup_map]
```

**lean_error:** tail step 2/4 ('rw [Submodule.span_image (inl R M M₂) s]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=1948, out=486)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [span_union, span_image, span_image, ← prod_eq_sup_map]
```
