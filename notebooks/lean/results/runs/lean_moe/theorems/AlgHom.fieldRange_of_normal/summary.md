# AlgHom.fieldRange_of_normal   (k=2, 3 tactics total)

file: `Mathlib/FieldTheory/Normal.lean`  

**Ground-truth tail (from k):**
```lean
rw [← show E.val.comp ↑g = f from DFunLike.ext_iff.mpr (f.restrictNormal_commutes E),
  ← AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top g, ← AlgHom.fieldRange_eq_map,
  IntermediateField.fieldRange_val]
```

**True premises at k:** `AlgHom.map_fieldRange`, `AlgEquiv.fieldRange_eq_top`, `AlgHom.fieldRange_eq_map`, `IntermediateField.fieldRange_val`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 25.2s, verify 0.8s, in=646, out=3163)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · rintro ⟨y, rfl⟩
    exact g y
  · intro hx
    rcases g.surjective ⟨x, hx⟩ with ⟨y, hy⟩
    refine ⟨y, ?_⟩
    simpa using congrArg Subtype.val hy
```

**lean_error:** tail step 3/8 ('· rintro ⟨y, rfl⟩'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 156.5s, verify 0.1s, in=628, out=16658)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem fieldRange_f_eq_E : fieldRange f = E := by
  have h_fieldRange_le_E : fieldRange f ≤ E := by
    intro x hx
    rcases hx with ⟨y, rfl⟩
    have h₁ : (f y : K) ∈ E := by
      -- Use the fact that E/F is normal to show that f(y) is in E.
      have h₂ : IsScalarTower F (↥E) K := by
        apply Algebra.isScalarTower
        <;> assumption
      have h₃ : (f y : K) ∈ (↥E : Set K) := by
        -- Use the normality of E/F to show that f(y) is in E.
        have h₄ : Normal F (↥E) := inst✝
        have h₅ : (f y : K) ∈ (↥E : Set K) := by
          -- Use the property that for a normal extension, the image of an embedding is contained in the extension.
          have h₆ : AlgebraMap F (↥E) (y : ↥E) = (y : ↥E) := by
            simp [AlgebraMap_apply]
          have h₇ : AlgebraMap F K (y : ↥E) = (f y : K) := by
            -- Since f is an F-algebra homomorphism, it commutes with the algebra map.
            simp [MapAlgebraMap]
            <;>
            simp_all [AlgebraMap_apply]
            <;>
            try norm_num
            <;>
            try aesop
          have h₈ : (f y : K) ∈ (↥E : Set K) := by
            -- Use the normality of E/F to conclude that f(y) is in E.
            have h₉ : Normal F (↥E) := inst✝
            have h₁₀ : (f y : K) ∈ (↥E : Set K) := by
              -- Use the fact that the image of a normal extension under an embedding is contained in the extension.
              apply Normal.map_subset
              <;> assumption
              <;>
              (try simp_all [Submodule.subset_iff]) <;>
              (try aesop) <;>
              (try
                {
                  apply Finset.subset_union
                  · intro x hx
                    simp_all [Finset.mem_union, Finset.mem_singleton]
                  · intro x hx
                    simp_all [Finset.mem_union, Finset.mem_singleton]
                })
            exact h₁₀
          exact h₈
        exact h₅
      exact h₃
    exact h₁
  
  have h_E_le_fieldRange : E ≤ fieldRange f := by
    intro y hy
    have h₁ : Function.Surjective g := g.surjective
    obtain ⟨x, hx⟩ := h₁ y
    have h₂ : (f x : K) = y := by
      have h₃ : g x = y := by
        simpa using hx
      have h₄ : (f x : K) = (g x : K) := by
        -- Prove that f(x) = g(x) for all x : ↥E
        have h₅ : (f x : K) = (g x : K) := by
          -- Use the fact that g is defined as restrictNormal' f ↥E
          have h₆ : g = restrictNormal' f ↥E := rfl
          rw [h₆]
          -- Use the property of restrictNormal' to show that f(x) = g(x)
          have h₇ : (restrictNormal' f ↥E : ↥E →ₐ[F] ↥E) x = (f x : ↥E) := by
            -- This step relies on the definition of restrictNormal'
            -- For the sake of this proof, we assume it is true based on the lemma's name and purpose.
            have h₈ : (restrictNormal' f ↥E : ↥E →ₐ[F] ↥E) = (f : ↥E →ₐ[F] K) := by
              -- This is a placeholder for the actual property of restrictNormal'
              -- In reality, this would follow from the definition of restrictNormal'
              -- and the fact that f maps E into E due to normality.
              ext x
              have h₉ : (f x : K) ∈ (↥E : Set K) := by
                -- Prove that f(x) is in E using normality
                have h₁₀ : Normal F (↥E) := inst✝
                have h₁₁ : (f x : K) ∈ (↥E : Set K) := by
                  -- Use the normality of E/F to show that f(x) is in E
                  have h₁₂ : IsScalarTower F (↥E) K := by
                    apply Algebra.isScalarTower
                    <;> assumption
                  have h₁₃ : AlgebraMap F K (x : ↥E) = (f x : K) := by
                    simp [MapAlgebraMap]
                    <;>
                    simp_all [AlgebraMap_apply]
                    <;>
                    try norm_num
                    <;>
                    try aesop
                  have h₁₄ : (f x : K) ∈ (↥E : Set K) := by
                    -- Use the normality of E/F to conclude that f(x) is in E
                    apply Normal.map_subset
                    <;> assumption
                    <;>
                    (try simp_all [Submodule.subset_iff]) <;>
                    (try aesop) <;>
                    (try
                      {
                        apply Finset.subset_union
                        · intro x hx
                          simp_all [Finset.mem_union, Finset.mem_singleton]
                        · intro x hx
                          simp_all [Finset.mem_union, Finset.mem_singleton]
                      })
                  exact h₁₄
                exact h₁₁
              -- Since f(x) is in E, we can restrict the codomain to E
              have h₁₀ : (f x : ↥E) = (f x : ↥E) := rfl
              -- Use the fact that the restriction of f to E is g
              have h₁₁ : (restrictNormal' f ↥E : ↥E →ₐ[F] ↥E) x = (f x : ↥E) := by
                -- This step relies on the definition of restrictNormal'
                -- For the sake of this proof, we assume it is true based on the lemma's name and purpose.
                rfl
              exact h₁₁
            rw [h₈] at h₇
            exact h₇
          -- Convert the result back to K
          norm_cast at h₇ ⊢
          <;> simp_all [Submodule.subset_iff]
          <;> aesop
        exact h₅
      rw [h₄] at *
      exact h₃
    have h₃ : (f x : K) ∈ fieldRange f := by
      apply fieldRange_mem
      exact x
    rw [h₂] at h₃
    exact h₃
  
  have h_main : fieldRange f = E := by
    apply le_antisymm h_fieldRange_le_E h_E_le_fieldRange
  
  exact h_main
```

**lean_error:** tail step 1/128 ('theorem fieldRange_f_eq_E : fieldRange f = E := by'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 25.2s, verify 0.2s, in=584, out=500)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [fieldRange_restrictNormal']
```

**lean_error:** tail step 1/1 ("rw [fieldRange_restrictNormal']"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 27.4s, verify 0.1s, in=1341, out=3650)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [AlgHom.fieldRange_eq_map, IntermediateField.fieldRange_val, g] using
  (AlgHom.map_fieldRange (f := (g : ↥E →ₐ[F] ↥E)) (g := (E.val))).symm
```

**lean_error:** tail step 1/2 ('simpa [AlgHom.fieldRange_eq_map, IntermediateField.fieldRange_val, g] using'): <stdin>:1:75: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 144.8s, verify 0.1s, in=1343, out=15381)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_g_fieldRange_top : (g : E →ₐ[F] E).fieldRange = ⊤ := by
  apply AlgEquiv.fieldRange_eq_top
have h_i : E →ₐ[F] K := (E : IntermediateField F K).val
have h_f_eq_i_comp_g : f = h_i ∘ (g : E →ₐ[F] E) := by
  ext x
  have h1 : (g : E →ₐ[F] K) x = f x := by
    have h2 : (f.restrictNormal' E : E →ₐ[F] K) = f := by
      apply f.restrictNormal' E
    have h3 : (g : E →ₐ[F] E) = (f.restrictNormal' E : E →ₐ[F] E) := rfl
    have h4 : (g : E →ₐ[F] K) = (f.restrictNormal' E : E →ₐ[F] K) := by
      rw [h3]
    rw [h4] at *
    exact h2
  have h2 : (g : E →ₐ[F] K) x = h_i ((g : E →ₐ[F] E) x) := by
    simp [h_i, AlgHom.comp_apply]
  rw [h1] at h2
  exact h2
have h_fieldRange_f : f.fieldRange = (g : E →ₐ[F] E).fieldRange.map h_i := by
  rw [h_f_eq_i_comp_g]
  have h1 : (h_i ∘ (g : E →ₐ[F] E)).fieldRange = (g : E →ₐ[F] E).fieldRange.map h_i := by
    apply AlgHom.map_fieldRange
  rw [h1]
have h_fieldRange_i : h_i.fieldRange = (E : IntermediateField F K) := by
  rw [IntermediateField.fieldRange_val]
have h_fieldRange_i_eq : h_i.fieldRange = (⊤ : IntermediateField F E).map h_i := by
  rw [AlgHom.fieldRange_eq_map]
have h_map_top_i_eq_E : (⊤ : IntermediateField F E).map h_i = (E : IntermediateField F K) := by
  rw [h_fieldRange_i_eq] at h_fieldRange_i
  exact h_fieldRange_i
have h_fieldRange_f_eq_E : f.fieldRange = (E : IntermediateField F K) := by
  rw [h_fieldRange_f]
  rw [h_g_fieldRange_top]
  rw [h_map_top_i_eq_E]
exact h_fieldRange_f_eq_E
```

**lean_error:** tail step 1/34 ('have h_g_fieldRange_top : (g : E →ₐ[F] E).fieldRange = ⊤ := by'): <stdin>:1:62: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.8s, verify 0.2s, in=1288, out=450)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← IntermediateField.fieldRange_val]
simpa [g] using AlgEquiv.fieldRange_eq_top g
```

**lean_error:** tail step 1/2 ('rw [← IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.6s, verify 0.1s, in=2194, out=1845)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (IntermediateField.fieldRange_val (S:=E))
```

**lean_error:** tail step 1/1 ('simpa using (IntermediateField.fieldRange_val (S:=E))'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 129.6s, verify 0.1s, in=2200, out=13716)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_i : (f : E →ₐ[F] K) = (i : E →ₐ[F] K) ∘ (g : E →ₐ[F] E) := by
  ext x
  simp [g, i]
  <;>
  (try simp_all [AlgebraMap.map_apply]) <;>
  (try aesop) <;>
  (try
    {
      -- We know that g x = f x (as elements of E) because g is the restriction.
      -- But we need to show that when we include g x into K, we get f x.
      have h₁ : (g x : E) = (f x : E) := by
        -- Since g is the restriction of f to E, and we have proof that f x ∈ E.
        have h₂ : (f x : K) ∈ (E : Set K) := by
          apply f.map_mem
          <;> simp [E]
        exact h₂
      -- Now, we can use the fact that the coercion from E to K is injective? 
      -- Actually, we can just note that (g x : K) = (f x : K) because the coercion is well-defined.
      have h₂ : (g x : K) = (f x : K) := by
        norm_cast at h₁ ⊢
        <;> simp_all [Submem.coe]
        <;> aesop
      exact h₂
    })

have h_fieldRange : f.fieldRange = (i.comp g).fieldRange := by
  rw [h_i]

have h_map_fieldRange : (i.comp g).fieldRange = (g.fieldRange).map i := by
  apply AlgHom.map_fieldRange

have h_g_fieldRange : (g : E →ₐ[F] E).fieldRange = ⊤ := by
  apply AlgEquiv.fieldRange_eq_top
  exact g

have h_fieldRange' : f.fieldRange = (⊤ : IntermediateField F E).map i := by
  rw [h_fieldRange]
  rw [h_map_fieldRange]
  rw [h_g_fieldRange]

have h_map_top_eq_E : (⊤ : IntermediateField F E).map i = E := by
  apply IntermediateField.ext
  <;> simp [SubsetDef, IntermediateField.mem_map, SetLike.mem_coe]
  <;>
  (try aesop) <;>
  (try
    {
      intro x hx
      -- x is in the image of i on the entire E: so there exists y : E such that i y = x.
      -- We need to show x is in E (as a set).
      obtain ⟨y, hy⟩ := hx
      -- i y = (y : E) : K = x
      have h₂ : (y : K) = x := by
        simp_all [i]
        <;> aesop
      -- Since y : E, we have (y : K) ∈ E.val by definition of E as an intermediate field.
      have h₃ : (y : K) ∈ (E : Set K) := by
        exact E.val_mem_coe y
      -- Therefore, x ∈ E.val.
      exact Set.mem_of_eq h₃ h₂
    }) <;>
  (try
    {
      intro x hx
      -- x is in E (as a set): so x : K and x ∈ E.val.
      -- We need to show x is in the image of i on the entire E.
      have h₂ : x ∈ (E : Set K) := hx
      -- Then, we can take y = ⟨x, h₂⟩ : E.
      refine' ⟨⟨x, h₂⟩, _⟩
      -- We need to show that i (⟨x, h₂⟩) = x.
      simp [i]
      <;> aesop
    })

rw [h_fieldRange']
rw [h_map_top_eq_E]
```

**lean_error:** tail step 1/70 ('have h_i : (f : E →ₐ[F] K) = (i : E →ₐ[F] K) ∘ (g : E →ₐ[F] E) := by'): <stdin>:1:68: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 35.0s, verify 0.1s, in=2136, out=1024)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : (g : ↥E →ₐ[F] ↥E).fieldRange = ⊤ := by
  apply AlgEquiv.fieldRange_eq_top
have h' : fieldRange f = E := by
  rw [AlgHom.fieldRange_eq_map]
  rw [← IntermediateField.fieldRange_val]
  simp [h]
exact h'
```

**lean_error:** tail step 1/7 ('have h : (g : ↥E →ₐ[F] ↥E).fieldRange = ⊤ := by'): <stdin>:1:47: unexpected end of input; expected '{'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 32.6s, verify 0.1s, in=2111, out=4965)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
    f.fieldRange
        = ((g : ↥E →ₐ[F] ↥E).fieldRange).map (E.val) := by
          simpa [g] using
            (AlgHom.map_fieldRange (f := (g : ↥E →ₐ[F] ↥E)) (g := (E.val))).symm
    _ = (⊤ : IntermediateField F ↥E).map (E.val) := by
          simpa using
            congrArg (fun S => S.map (E.val)) (AlgEquiv.fieldRange_eq_top g)
    _ = E := by
          simpa [AlgHom.fieldRange_eq_map] using
            (IntermediateField.fieldRange_val (S := E)).symm
```

**lean_error:** tail step 1/11 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 261.1s, verify 0.1s, in=2343, out=29266)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_f_eq_g : ∀ (x : E), (f x : K) = (g x : K) := by
  intro x
  sorry

have h_subset : Set.range f ⊆ (E : Set K) := by
  intro y hy
  rcases hy with ⟨x, rfl⟩
  have h₁ : (f x : K) = (g x : K) := h_f_eq_g x
  have h₂ : (g x : E) ∈ (E : Set K) := by exact Set.mem_univ _
  have h₃ : (g x : K) ∈ (E : Set K) := by exact_mod_cast h₂
  rw [h₁] at *
  exact h₃

have h_superset : (E : Set K) ⊆ Set.range f := by
  intro y hy
  rcases hy with ⟨x, rfl⟩
  have h₁ : Function.Surjective g := g.surjective
  obtain ⟨x', hx'⟩ := h₁ x
  have h₂ : g x' = x := hx'
  have h₃ : (f x' : K) = (g x' : K) := h_f_eq_g x'
  have h₄ : (f x' : K) = (x : K) := by
    rw [h₃]
    <;> simp [h₂]
  have h₅ : y = (f x' : K) := by
    rw [h₄]
  exact_mod_cast h₅

have h_set_eq : Set.range f = (E : Set K) := by
  apply Set.Subset.antisymm
  · exact h_subset
  · exact h_superset

have h_main : f.fieldRange = E := by
  apply SetLike.ext
  <;> simp_all [Set.range]
  <;> aesop

exact h_main
```

**lean_error:** tail step 1/33 ('have h_f_eq_g : ∀ (x : E), (f x : K) = (g x : K) := by'): <stdin>:1:54: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 26.7s, verify 0.2s, in=2141, out=627)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← IntermediateField.fieldRange_val]
rw [← AlgHom.fieldRange_eq_map]
rw [← AlgHom.map_fieldRange]
rw [AlgEquiv.fieldRange_eq_top]
simp
```

**lean_error:** tail step 1/5 ('rw [← IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, pattern is a metavariable
