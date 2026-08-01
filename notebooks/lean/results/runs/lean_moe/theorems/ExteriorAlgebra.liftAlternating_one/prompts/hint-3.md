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

## Transitive premise context (1-hop, 3/3 premises, ≈484 tokens)
### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `foldl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Fin/Fold.lean`
```lean
/-- Folds over `Fin n` from the left: `foldl 3 f x = f (f (f x 0) 1) 2`. -/
@[inline] def foldl (n) (f : α → Fin n → α) (init : α) : α := loop init 0 where
  /-- Inner loop for `Fin.foldl`. `Fin.foldl.loop n f x i = f (f (f x i) ...) (n-1)`  -/
  loop (x : α) (i : Nat) : α :=
    if h : i < n then loop (f x ⟨i, h⟩) (i+1) else x
  termination_by n - i

/-- Folds over `Fin n` from the right: `foldr 3 f x = f 0 (f 1 (f 2 x))`. -/
```

### `CliffordAlgebra.foldr_one` (commanddeclaration) at `Mathlib/LinearAlgebra/CliffordAlgebra/Fold.lean`
```lean
@[simp]
theorem foldr_one (f : M →ₗ[R] N →ₗ[R] N) (hf) (n : N) : foldr Q f hf n 1 = n :=
  LinearMap.congr_fun (AlgHom.map_one _) n
```
