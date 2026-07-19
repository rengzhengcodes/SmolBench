## Current goal
```
⊢ Sigma.mk a '' (g a ⁻¹' id x✝) = Sigma.map f g ⁻¹' (Sigma.mk (f a) '' id x✝)
```

## Full tactic state
```
case h.e'_5.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
π : α → Type u_6
π' : β → Type u_7
f : α → β
hf : Function.Injective f
g : (a : α) → π a → π' (f a)
a : α
l : Filter (π' (f a))
x✝ : Set (π' (f a))
⊢ Sigma.mk a '' (g a ⁻¹' id x✝) = Sigma.map f g ⁻¹' (Sigma.mk (f a) '' id x✝)
```

## Proof so far (2 tactics)
```lean
refine' (((basis_sets _).comap _).map _).eq_of_same_basis _
convert ((basis_sets l).map (Sigma.mk (f a))).comap (Sigma.map f g)
```

## Theorem
`Filter.map_sigma_mk_comap` in `Mathlib/Order/Filter/Bases.lean`

## Premises used in the next tactic
- `Set.image_sigmaMk_preimage_sigmaMap`

## Premise signatures
### `Set.image_sigmaMk_preimage_sigmaMap` (commanddeclaration)
```lean
theorem image_sigmaMk_preimage_sigmaMap {β : ι' → Type*} {f : ι → ι'} (hf : Function.Injective f)
    (g : ∀ i, α i → β (f i)) (i : ι) (s : Set (β (f i))) :
    Sigma.mk i '' (g i ⁻¹' s) = Sigma.map f g ⁻¹' (Sigma.mk (f i) '' s)
```

## Premise full source (with proof)
### `Set.image_sigmaMk_preimage_sigmaMap` (commanddeclaration) at `Mathlib/Data/Set/Sigma.lean`
```lean
theorem image_sigmaMk_preimage_sigmaMap {β : ι' → Type*} {f : ι → ι'} (hf : Function.Injective f)
    (g : ∀ i, α i → β (f i)) (i : ι) (s : Set (β (f i))) :
    Sigma.mk i '' (g i ⁻¹' s) = Sigma.map f g ⁻¹' (Sigma.mk (f i) '' s) := by
  refine' (image_sigmaMk_preimage_sigmaMap_subset f g i s).antisymm _
  rintro ⟨j, x⟩ ⟨y, hys, hxy⟩
  simp only [hf.eq_iff, Sigma.map, Sigma.ext_iff] at hxy
  rcases hxy with ⟨rfl, hxy⟩; rw [heq_iff_eq] at hxy; subst y
  exact ⟨x, hys, rfl⟩
```

## Transitive premise context (1-hop, 7/7 premises, ≈712 tokens)
### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `Function.Injective` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
/-- A function `f : α → β` is called injective if `f x = f y` implies `x = y`. -/
def Injective (f : α → β) : Prop :=
  ∀ ⦃a₁ a₂⦄, f a₁ = f a₂ → a₁ = a₂
```

### `Sigma.map` (commanddeclaration) at `Mathlib/Data/Sigma/Basic.lean`
```lean
/-- Map the left and right components of a sigma -/
def map (f₁ : α₁ → α₂) (f₂ : ∀ a, β₁ a → β₂ (f₁ a)) (x : Sigma β₁) : Sigma β₂ :=
  ⟨f₁ x.1, f₂ x.1 x.2⟩
```

### `Set.image_sigmaMk_preimage_sigmaMap_subset` (commanddeclaration) at `Mathlib/Data/Set/Sigma.lean`
```lean
theorem image_sigmaMk_preimage_sigmaMap_subset {β : ι' → Type*} (f : ι → ι')
    (g : ∀ i, α i → β (f i)) (i : ι) (s : Set (β (f i))) :
    Sigma.mk i '' (g i ⁻¹' s) ⊆ Sigma.map f g ⁻¹' (Sigma.mk (f i) '' s) :=
  image_subset_iff.2 fun x hx ↦ ⟨g i x, hx, rfl⟩
```

### `antisymm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem antisymm [IsAntisymm α r] {a b : α} : a ≺ b → b ≺ a → a = b :=
  IsAntisymm.antisymm _ _
```

### `Sigma.ext_iff` (commanddeclaration) at `Mathlib/Data/Sigma/Basic.lean`
```lean
theorem ext_iff {x₀ x₁ : Sigma β} : x₀ = x₁ ↔ x₀.1 = x₁.1 ∧ HEq x₀.2 x₁.2 := by
  cases x₀; cases x₁; exact Sigma.mk.inj_iff
```

### `heq_iff_eq` (commanddeclaration) at `.lake/packages/std/Std/Logic.lean`
```lean
theorem heq_iff_eq : HEq a b ↔ a = b := ⟨eq_of_heq, heq_of_eq⟩
```
