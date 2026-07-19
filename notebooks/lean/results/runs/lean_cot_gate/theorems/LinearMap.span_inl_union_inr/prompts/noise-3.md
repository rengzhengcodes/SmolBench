## Current goal
```
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
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
inst✝⁸ : Semiring R
inst✝⁷ : AddCommMonoid M
inst✝⁶ : AddCommMonoid M₂
inst✝⁵ : AddCommMonoid M₃
inst✝⁴ : AddCommMonoid M₄
inst✝³ : Module R M
inst✝² : Module R M₂
inst✝¹ : Module R M₃
inst✝ : Module R M₄
s : Set M
t : Set M₂
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`LinearMap.span_inl_union_inr` in `Mathlib/LinearAlgebra/Prod.lean`

## Premises used in the next tactic
- `Submodule.span_union`
- `LinearMap.prod_eq_sup_map`
- `Submodule.span_image`
- `Submodule.span_image`

## Premise signatures
### `Submodule.span_union` (commanddeclaration)
```lean
theorem span_union (s t : Set M) : span R (s ∪ t) = span R s ⊔ span R t
```

### `LinearMap.prod_eq_sup_map` (commanddeclaration)
```lean
theorem prod_eq_sup_map (p : Submodule R M) (q : Submodule R M₂) :
    p.prod q = p.map (LinearMap.inl R M M₂) ⊔ q.map (LinearMap.inr R M M₂)
```

### `Submodule.span_image` (commanddeclaration)
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s)
```

### `Submodule.span_image` (commanddeclaration)
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s)
```

## Premise full source (with proof)
### `Submodule.span_union` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_union (s t : Set M) : span R (s ∪ t) = span R s ⊔ span R t :=
  (Submodule.gi R M).gc.l_sup
```

### `LinearMap.prod_eq_sup_map` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
theorem prod_eq_sup_map (p : Submodule R M) (q : Submodule R M₂) :
    p.prod q = p.map (LinearMap.inl R M M₂) ⊔ q.map (LinearMap.inr R M M₂) := by
  rw [← map_coprod_prod, coprod_inl_inr, map_id]
```

### `Submodule.span_image` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s) :=
  (map_span f s).symm
```

### `Submodule.span_image` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem span_image [RingHomSurjective σ₁₂] (f : F) :
    span R₂ (f '' s) = map f (span R s) :=
  (map_span f s).symm
```

## Filler (hint:2 → hint:3 token-match, ≈780 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
