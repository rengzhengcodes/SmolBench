## Current goal
```
⊢ IsDetector G.unop ↔ IsCodetector G
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
G : Cᵒᵖ
⊢ IsDetector G.unop ↔ IsCodetector G
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.isDetector_unop_iff` in `Mathlib/CategoryTheory/Generator.lean`

## Premises used in the next tactic
- `CategoryTheory.IsDetector`
- `CategoryTheory.IsCodetector`
- `CategoryTheory.isDetecting_unop_iff`
- `Set.singleton_unop`

## Premise signatures
### `CategoryTheory.IsDetector` (commanddeclaration)
```lean
def IsDetector (G : C) : Prop
```

### `CategoryTheory.IsCodetector` (commanddeclaration)
```lean
def IsCodetector (G : C) : Prop
```

### `CategoryTheory.isDetecting_unop_iff` (commanddeclaration)
```lean
theorem isDetecting_unop_iff (𝒢 : Set Cᵒᵖ) : IsDetecting 𝒢.unop ↔ IsCodetecting 𝒢
```

### `Set.singleton_unop` (commanddeclaration)
```lean
@[simp]
theorem singleton_unop (x : αᵒᵖ) : ({x} : Set αᵒᵖ).unop = {unop x}
```

## Premise full source (with proof)
### `CategoryTheory.IsDetector` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `G` is a detector if the functor `C(G, -)` reflects isomorphisms. -/
def IsDetector (G : C) : Prop :=
  IsDetecting ({G} : Set C)
```

### `CategoryTheory.IsCodetector` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
/-- We say that `G` is a codetector if the functor `C(-, G)` reflects isomorphisms. -/
def IsCodetector (G : C) : Prop :=
  IsCodetecting ({G} : Set C)
```

### `CategoryTheory.isDetecting_unop_iff` (commanddeclaration) at `Mathlib/CategoryTheory/Generator.lean`
```lean
theorem isDetecting_unop_iff (𝒢 : Set Cᵒᵖ) : IsDetecting 𝒢.unop ↔ IsCodetecting 𝒢 := by
  rw [← isCodetecting_op_iff, Set.unop_op]
```

### `Set.singleton_unop` (commanddeclaration) at `Mathlib/Data/Set/Opposite.lean`
```lean
@[simp]
theorem singleton_unop (x : αᵒᵖ) : ({x} : Set αᵒᵖ).unop = {unop x} := by
  ext
  constructor
  · apply op_injective
  · apply unop_injective
```

## Filler (hint:2 → hint:3 token-match, ≈726 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
