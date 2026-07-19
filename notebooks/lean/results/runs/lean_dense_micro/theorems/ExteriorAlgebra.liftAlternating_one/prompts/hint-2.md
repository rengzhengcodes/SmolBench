## Current goal
```
⊢ (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          f)
        1 0)
      0 =
    (f 0) 0
```

## Full tactic state
```
R : Type u_1
M : Type u_2
N : Type u_3
N' : Type u_4
inst✝⁶ : CommRing R
inst✝⁵ : AddCommGroup M
inst✝⁴ : AddCommGroup N
inst✝³ : AddCommGroup N'
inst✝² : Module R M
inst✝¹ : Module R N
inst✝ : Module R N'
f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N
⊢ (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          f)
        1 0)
      0 =
    (f 0) 0
```

## Proof so far (1 tactic)
```lean
dsimp [liftAlternating]
```

## Theorem
`ExteriorAlgebra.liftAlternating_one` in `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`

## Premises used in the next tactic
- `CliffordAlgebra.foldl_one`

## Premise signatures
### `CliffordAlgebra.foldl_one` (commanddeclaration)
```lean
@[simp]
theorem foldl_one (f : M →ₗ[R] N →ₗ[R] N) (hf) (n : N) : foldl Q f hf n 1 = n
```

## Premise full source (with proof)
### `CliffordAlgebra.foldl_one` (commanddeclaration) at `Mathlib/LinearAlgebra/CliffordAlgebra/Fold.lean`
```lean
@[simp]
theorem foldl_one (f : M →ₗ[R] N →ₗ[R] N) (hf) (n : N) : foldl Q f hf n 1 = n := by
  rw [← foldr_reverse, reverse.map_one, foldr_one]
```
