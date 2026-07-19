## Current goal
```
⊢ Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥)
```

## Full tactic state
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
M₃ : Type y
V₃ : Type y'
M₄ : Type z
ι : Type x
M₅ : Type u_1
M₆ : Type u_2
S : Type u_3
inst✝¹³ : Semiring R
inst✝¹² : Semiring S
inst✝¹¹ : AddCommMonoid M
inst✝¹⁰ : AddCommMonoid M₂
inst✝⁹ : AddCommMonoid M₃
inst✝⁸ : AddCommMonoid M₄
inst✝⁷ : AddCommMonoid M₅
inst✝⁶ : AddCommMonoid M₆
inst✝⁵ : Module R M
inst✝⁴ : Module R M₂
inst✝³ : Module R M₃
inst✝² : Module R M₄
inst✝¹ : Module R M₅
inst✝ : Module R M₆
f✝ f : M →ₗ[R] M₂
g : M₃ →ₗ[R] M₄
⊢ Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥)
```

## Proof so far (1 tactic)
```lean
dsimp only [ker]
```

## Theorem
`LinearMap.ker_prodMap` in `Mathlib/LinearAlgebra/Prod.lean`

## Premises used in the next tactic
- `LinearMap.prodMap_comap_prod`
- `Submodule.prod_bot`

## Premise signatures
### `LinearMap.prodMap_comap_prod` (commanddeclaration)
```lean
theorem prodMap_comap_prod (f : M →ₗ[R] M₂) (g : M₃ →ₗ[R] M₄) (S : Submodule R M₂)
    (S' : Submodule R M₄) :
    (Submodule.prod S S').comap (LinearMap.prodMap f g) = (S.comap f).prod (S'.comap g)
```

### `Submodule.prod_bot` (commanddeclaration)
```lean
@[simp]
theorem prod_bot : (prod ⊥ ⊥ : Submodule R (M × M')) = ⊥
```

## Premise full source (with proof)
### `LinearMap.prodMap_comap_prod` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
theorem prodMap_comap_prod (f : M →ₗ[R] M₂) (g : M₃ →ₗ[R] M₄) (S : Submodule R M₂)
    (S' : Submodule R M₄) :
    (Submodule.prod S S').comap (LinearMap.prodMap f g) = (S.comap f).prod (S'.comap g) :=
  SetLike.coe_injective <| Set.preimage_prod_map_prod f g _ _
```

### `Submodule.prod_bot` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
@[simp]
theorem prod_bot : (prod ⊥ ⊥ : Submodule R (M × M')) = ⊥ := by ext ⟨x, y⟩; simp [Prod.zero_eq_mk]
```

## Transitive premise context (1-hop, 5/5 premises, ≈507 tokens)
### `Submodule` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Basic.lean`
```lean
/-- A submodule of a module is one which is closed under vector operations.
  This is a sufficient condition for the subset of vectors in the submodule
  to themselves form a module. -/
structure Submodule (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M] [Module R M] extends
  AddSubmonoid M, SubMulAction R M : Type v
```

### `Submodule.prod` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
/-- The product of two submodules is a submodule. -/
def prod : Submodule R (M × M') :=
  { p.toAddSubmonoid.prod q₁.toAddSubmonoid with
    carrier := p ×ˢ q₁
    smul_mem' := by rintro a ⟨x, y⟩ ⟨hx, hy⟩; exact ⟨smul_mem _ a hx, smul_mem _ a hy⟩ }
```

### `LinearMap.prodMap` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
/-- `prod.map` of two linear maps. -/
def prodMap (f : M →ₗ[R] M₃) (g : M₂ →ₗ[R] M₄) : M × M₂ →ₗ[R] M₃ × M₄ :=
  (f.comp (fst R M M₂)).prod (g.comp (snd R M M₂))
```

### `SetLike.coe_injective` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
theorem coe_injective : Function.Injective (SetLike.coe : A → Set B) := fun _ _ h =>
  SetLike.coe_injective' h
```

### `Set.preimage_prod_map_prod` (commanddeclaration) at `Mathlib/Data/Set/Prod.lean`
```lean
theorem preimage_prod_map_prod (f : α → β) (g : γ → δ) (s : Set β) (t : Set δ) :
    Prod.map f g ⁻¹' s ×ˢ t = (f ⁻¹' s) ×ˢ (g ⁻¹' t) :=
  rfl
```
