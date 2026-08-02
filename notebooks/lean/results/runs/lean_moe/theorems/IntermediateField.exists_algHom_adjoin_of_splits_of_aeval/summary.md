# IntermediateField.exists_algHom_adjoin_of_splits_of_aeval   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/Extension.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨φ, (DFunLike.congr_fun hφ <| AdjoinSimple.gen F x).trans <|
  algHomAdjoinIntegralEquiv_symm_apply_gen F ix _⟩
```

**True premises at k:** `DFunLike.congr_fun`, `IntermediateField.AdjoinSimple.gen`, `Eq.trans`, `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.6s, in=543, out=2336)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h := congrArg (fun g : (adjoin F S) →ₐ[F] K => g { val := x, property := hx }) hφ
simpa using h
```

**lean_error:** tail step 2/3 ('have h := congrArg (fun g : (adjoin F S) →ₐ[F] K => g { val := x, property := hx }) hφ'): application type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 263.9s, verify 0.3s, in=502, out=31662)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨φ, _⟩
have h₁ : φ ⟨x, hx⟩ = y := by
  have h₂ : (φ.comp inclusion) ⟨x, hx⟩ = ((algHomAdjoinIntegralEquiv F ix).symm { val := y, property := _ }) ⟨x, hx⟩ := by
    apply hφ
  -- Simplify the LHS: (φ.comp inclusion) ⟨x, hx⟩ = φ (inclusion ⟨x, hx⟩)
  -- Since inclusion : ↥(adjoin F S) → E, inclusion ⟨x, hx⟩ = x : E
  -- But we need to convert φ to a map on E using hS
  -- Use the fact that adjoin F S = ⊤ to get an equivalence between ↥(adjoin F S) and E
  -- Then, transfer φ to E and simplify
  have h₃ : φ ⟨x, hx⟩ = y := by
    sorry
  exact h₃

Exact h₁
```

**lean_error:** tail step 2/13 ('have h₁ : φ ⟨x, hx⟩ = y := by'): <stdin>:1:29: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.7s, verify 0.3s, in=487, out=680)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨φ, _⟩
have : (inclusion (adjoin F S)) { val := x, property := hx } = x := by simp
have h : φ { val := x, property := hx } = y := by
  have h₁ := congr_fun hφ { val := x, property := hx }
  simp only [AlgHom.comp_apply, inclusion_apply] at h₁
  simp_all [algHomAdjoinIntegralEquiv_apply]
exact h
```

**lean_error:** tail step 2/7 ('have : (inclusion (adjoin F S)) { val := x, property := hx } = x := by simp'): application type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 14.5s, verify 3.1s, in=1689, out=2307)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h' := DFunLike.congr_fun hφ (AdjoinSimple.gen F x)
simp [AlgHom.comp_apply, IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen] at h'
exact h'
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 179.7s, verify 0.1s, in=1687, out=21922)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_main : φ ⟨x, hx⟩ = y := by
  have h₁ : (AlgHom.comp φ (inclusion _ (adjoin_simple_le_iff.mpr hx))) = (algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ := by
    exact hφ
  have h₂ : (AlgHom.comp φ (inclusion _ (adjoin_simple_le_iff.mpr hx))) (AdjoinSimple.gen F x) = φ ⟨x, hx⟩ := by
    have h₃ : (inclusion _ (adjoin_simple_le_iff.mpr hx)) (AdjoinSimple.gen F x) = ⟨x, hx⟩ := by
      -- Prove that the inclusion map sends the generator of F⟮x⟧ to ⟨x, hx⟩ in adjoin F S
      have h₄ : (inclusion _ (adjoin_simple_le_iff.mpr hx)) (AdjoinSimple.gen F x) = ⟨(AdjoinSimple.gen F x : {x // x ∈ adjoin F F⟮x⟧}).val, _⟩ := by
        simp [inclusion]
        <;>
        (try simp_all [mem_adjoin]) <;>
        (try aesop) <;>
        (try norm_num) <;>
        (try ring_nf) <;>
        (try simp_all [AdjoinSimple.gen]) <;>
        (try aesop)
      rw [h₄]
      -- Simplify the expression to show it equals ⟨x, hx⟩
      have h₅ : (AdjoinSimple.gen F x : {x // x ∈ adjoin F F⟮x⟧}).val = x := by
        simp [AdjoinSimple.gen]
      rw [h₅]
      -- The proof that x is in adjoin F S is hx
      <;> simp_all [Subtype.ext_iff]
      <;> aesop
    calc
      (AlgHom.comp φ (inclusion _ (adjoin_simple_le_iff.mpr hx))) (AdjoinSimple.gen F x) = φ ((inclusion _ (adjoin_simple_le_iff.mpr hx)) (AdjoinSimple.gen F x)) := by
        simp [AlgHom.comp_apply]
      _ = φ ⟨x, hx⟩ := by rw [h₃]
  have h₃ : ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) = ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ := by
    have h₄ : IsIntegral F x := ix
    have h₅ : ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ : {y : K // y ∈ (minpoly F x).aroots K} := ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩
    rw [IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen h₄ h₅]
  have h₄ : φ ⟨x, hx⟩ = y := by
    have h₅ : (AlgHom.comp φ (inclusion _ (adjoin_simple_le_iff.mpr hx))) (AdjoinSimple.gen F x) = ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) := by
      rw [h₁]
    have h₆ : (AlgHom.comp φ (inclusion _ (adjoin_simple_le_iff.mpr hx))) (AdjoinSimple.gen F x) = φ ⟨x, hx⟩ := h₂
    have h₇ : ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) = ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ := h₃
    have h₈ : φ ⟨x, hx⟩ = ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ := by
      linarith
    -- Now we need to show that ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ : {y : K // y ∈ (minpoly F x).aroots K} is equal to y : K
    -- This is done by noting that the coercion of the subtype element to K is y
    have h₉ : (⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ : {y : K // y ∈ (minpoly F x).aroots K}) = y := by
      simp [Subtype.ext_iff]
      <;> aesop
    -- However, h₈ is an equality in the subtype, so we need to convert it to an equality in K
    -- We do this by noting that φ ⟨x, hx⟩ is in K and the subtype element coerces to y
    have h₁₀ : φ ⟨x, hx⟩ = y := by
      -- Use the fact that the coercion is injective to transfer the equality
      have h₁₁ : φ ⟨x, hx⟩ = y := by
        -- Since φ ⟨x, hx⟩ : K and y : K, we can directly compare them
        -- We know that φ ⟨x, hx⟩ equals the subtype element, which coerces to y
        have h₁₂ : (φ ⟨x, hx⟩ : K) = (⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ : {y : K // y ∈ (minpoly F x).aroots K}) := by
          exact_mod_cast h₈
        -- Now we use the fact that the coercion from the subtype to K is injective
        have h₁₃ : (⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩ : {y : K // y ∈ (minpoly F x).aroots K}) = y := by
          simp [Subtype.ext_iff]
          <;> aesop
        -- Therefore, φ ⟨x, hx⟩ = y
        rw [h₁₂] at *
        exact h₁₃
      exact h₁₁
    exact h₁₀
  exact h₄

refine' ⟨φ, _⟩
exact h_main
```

**lean_error:** tail step 1/64 ('have h_main : φ ⟨x, hx⟩ = y := by'): <stdin>:1:33: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 27.8s, verify 0.1s, in=1614, out=2690)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ := congr_fun hφ (AdjoinSimple.gen F x)
have h₂ : (AlgHom.comp φ (inclusion ⋯)) (AdjoinSimple.gen F x) = φ { val := x, property := hx } := by
  simp [AlgHom.comp_apply]
have h₃ : (algHomAdjoinIntegralEquiv F ix).symm { val := y, property := ⋯ } (AdjoinSimple.gen F x) = y :=
  algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩
exact ⟨φ, Eq.trans (h₁.symm.trans h₂) h₃.symm⟩
```

**lean_error:** tail step 1/6 ('have h₁ := congr_fun hφ (AdjoinSimple.gen F x)'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.0s, verify 0.5s, in=4494, out=2269)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have hval := DFunLike.congr_fun hφ (AdjoinSimple.gen F x)
simp [AlgHom.comp_apply,
      IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen] at hval
simpa using hval
```

**lean_error:** tail step 3/5 ('simp [AlgHom.comp_apply,'): <stdin>:1:24: unexpected end of input; expected ']'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 273.5s, verify 0.1s, in=4571, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁₁ : (AdjoinSimple.gen F x : E) = x := by
  rfl
```

**lean_error:** tail step 1/2 ('have h₁₁ : (AdjoinSimple.gen F x : E) = x := by'): <stdin>:1:47: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 29.8s, verify 0.4s, in=4445, out=2922)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h := DFunLike.congr_fun hφ (IntermediateField.AdjoinSimple.gen F x)
refine' ⟨φ, Eq.trans _ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩)⟩
simpa using h
```

**lean_error:** tail step 2/3 ("refine' ⟨φ, Eq.trans _ (IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩)⟩"): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 18.3s, verify 0.3s, in=4188, out=3384)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨φ, ?_⟩
have h_eq :=
  congrArg (fun f : (F⟮x⟯) →ₐ[F] K => f (AdjoinSimple.gen F x)) hφ
simp [AlgHom.comp_apply,
      IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen ix] at h_eq
exact h_eq
```

**lean_error:** tail step 2/6 ('have h_eq :='): <stdin>:1:12: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 222.9s, verify 0.1s, in=4953, out=26815)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_incl_val : ((i (AdjoinSimple.gen F x) : E)) = x := by
  simp [Subtype.coe_inclusion, AdjoinSimple.gen]
  <;>
  simp_all [Subtype.coe_mk]
  <;>
  aesop
have h_eq : { val := x, property := hx } = i (AdjoinSimple.gen F x) := by
  apply Subtype.ext
  <;> simp_all [Subtype.coe_inclusion]
  <;>
  (try
    {
      simp_all [h_incl_val]
      <;> aesop
    })
have h1 : φ { val := x, property := hx } = φ (i (AdjoinSimple.gen F x)) := by
  rw [h_eq]
have h2 : φ (i (AdjoinSimple.gen F x)) = (φ.comp i) (AdjoinSimple.gen F x) := by
  simp [AlgHom.comp_apply]
have h3 : (φ.comp i) (AdjoinSimple.gen F x) = ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) := by
  rw [hφ]
have h4 : ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) = y := by
  apply IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen
  <;> assumption
have h5 : φ { val := x, property := hx } = y := by
  calc
    φ { val := x, property := hx } = φ (i (AdjoinSimple.gen F x)) := h1
    _ = (φ.comp i) (AdjoinSimple.gen F x) := h2
    _ = ((algHomAdjoinIntegralEquiv F ix).symm ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (AdjoinSimple.gen F x) := h3
    _ = y := h4
exact ⟨φ, h5⟩
```

**lean_error:** tail step 1/31 ('have h_incl_val : ((i (AdjoinSimple.gen F x) : E)) = x := by'): <stdin>:1:60: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.3s, verify 0.1s, in=4396, out=1319)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (AlgHom.comp φ (inclusion (adjoin F S) E)) (AdjoinSimple.gen F x) = 
    (algHomAdjoinIntegralEquiv F ix).symm { val := y, property := hy } (AdjoinSimple.gen F x) :=
  congr_fun hφ (AdjoinSimple.gen F x)
have h₂ : (algHomAdjoinIntegralEquiv F ix).symm { val := y, property := hy } (AdjoinSimple.gen F x) = y :=
  algHomAdjoinIntegralEquiv_symm_apply_gen ix ⟨y, hy⟩
have h₃ : φ { val := x, property := hx } = y := by
  rw [← h₂, ← h₁]
  simp [AlgHom.comp_apply]
exact ⟨φ, h₃⟩
```

**lean_error:** tail step 1/9 ('have h₁ : (AlgHom.comp φ (inclusion (adjoin F S) E)) (AdjoinSimple.gen F x) ='): <stdin>:1:77: unexpected end of input
