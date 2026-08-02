## Current goal
```
⊢ Surjective ⇑((piEquiv ι R M) v) ↔ span R (range v) = ⊤
```

## Full tactic state
```
ι : Type u_1
R : Type u_2
M : Type u_3
N : Type u_4
inst✝⁵ : Finite ι
inst✝⁴ : CommSemiring R
inst✝³ : AddCommMonoid M
inst✝² : AddCommMonoid N
inst✝¹ : Module R M
inst✝ : Module R N
v : ι → M
⊢ Surjective ⇑((piEquiv ι R M) v) ↔ span R (range v) = ⊤
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Module.surjective_piEquiv_apply_iff` in `Mathlib/LinearAlgebra/StdBasis.lean`

## Premises used in the next tactic
- `LinearMap.range_eq_top`
- `Module.range_piEquiv`

## Premise signatures
### `LinearMap.range_eq_top` (commanddeclaration)
```lean
theorem range_eq_top [RingHomSurjective τ₁₂] {f : F} : range f = ⊤ ↔ Surjective f
```

### `Module.range_piEquiv` (lemma)
```lean
@[simp] lemma range_piEquiv (v : ι → M) :
    LinearMap.range (piEquiv ι R M v) = span R (range v)
```

## Premise full source (with proof)
### `LinearMap.range_eq_top` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
theorem range_eq_top [RingHomSurjective τ₁₂] {f : F} : range f = ⊤ ↔ Surjective f := by
  rw [SetLike.ext'_iff, range_coe, top_coe, Set.range_iff_surjective]
```

### `Module.range_piEquiv` (lemma) at `Mathlib/LinearAlgebra/StdBasis.lean`
```lean
@[simp] lemma range_piEquiv (v : ι → M) :
    LinearMap.range (piEquiv ι R M v) = span R (range v) :=
  Basis.constr_range _ _
```

## Transitive premise context (1-hop, 6/6 premises, ≈537 tokens)
### `RingHomSurjective` (commanddeclaration) at `Mathlib/Algebra/Ring/CompTypeclasses.lean`
```lean
/-- Class expressing the fact that a `RingHom` is surjective. This is needed in the context
of semilinear maps, where some lemmas require this. -/
class RingHomSurjective (σ : R₁ →+* R₂) : Prop where
  /-- The ring homomorphism is surjective -/
  is_surjective : Function.Surjective σ
```

### `Function.Surjective` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
/-- A function `f : α → β` is called surjective if every `b : β` is equal to `f a`
for some `a : α`. -/
def Surjective (f : α → β) : Prop :=
  ∀ b, ∃ a, f a = b
```

### `SetLike.ext'_iff` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
theorem ext'_iff : p = q ↔ (p : Set B) = q :=
  coe_set_eq.symm
```

### `Set.range_iff_surjective` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
theorem range_iff_surjective : range f = univ ↔ Surjective f :=
  eq_univ_iff_forall
```

### `LinearMap.range` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
/-- The range of a linear map `f : M → M₂` is a submodule of `M₂`.
See Note [range copy pattern]. -/
def range [RingHomSurjective τ₁₂] (f : F) : Submodule R₂ M₂ :=
  (map f ⊤).copy (Set.range f) Set.image_univ.symm
```

### `Basis.constr_range` (commanddeclaration) at `Mathlib/LinearAlgebra/Basis.lean`
```lean
theorem constr_range {f : ι → M'} :
    LinearMap.range (constr (M' := M') b S f) = span R (range f) := by
  rw [b.constr_def S f, LinearMap.range_comp, LinearMap.range_comp, LinearEquiv.range, ←
    Finsupp.supported_univ, Finsupp.lmapDomain_supported, ← Set.image_univ, ←
    Finsupp.span_image_eq_map_total, Set.image_id]
```
