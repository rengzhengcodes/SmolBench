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

## Filler (hint:2 → hint:3 token-match, ≈532 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in repreh
