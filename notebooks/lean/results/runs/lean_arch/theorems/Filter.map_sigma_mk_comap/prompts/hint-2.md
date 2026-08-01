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
