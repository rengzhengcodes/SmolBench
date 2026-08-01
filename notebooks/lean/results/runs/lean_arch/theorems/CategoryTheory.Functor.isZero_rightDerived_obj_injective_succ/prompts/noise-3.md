## Current goal
```
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```

## Full tactic state
```
C : Type u
inst✝⁶ : Category.{v, u} C
D : Type u_1
inst✝⁵ : Category.{u_2, u_1} D
inst✝⁴ : Abelian C
inst✝³ : HasInjectiveResolutions C
inst✝² : Abelian D
F : C ⥤ D
inst✝¹ : Additive F
n : ℕ
X : C
inst✝ : Injective X
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```

## Proof so far (3 tactics)
```lean
refine IsZero.of_iso ?_ ((InjectiveResolution.self X).isoRightDerivedObj F (n + 1))
erw [← HomologicalComplex.exactAt_iff_isZero_homology]
exact ShortComplex.exact_of_isZero_X₂ _ (F.map_isZero (by apply isZero_zero))
```

## Theorem
`CategoryTheory.Functor.isZero_rightDerived_obj_injective_succ` in `Mathlib/CategoryTheory/Abelian/RightDerived.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.isZero_zero`

## Premise signatures
### `CategoryTheory.Limits.isZero_zero` (commanddeclaration)
```lean
theorem isZero_zero : IsZero (0 : C)
```

## Premise full source (with proof)
### `CategoryTheory.Limits.isZero_zero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroObjects.lean`
```lean
theorem isZero_zero : IsZero (0 : C) :=
  HasZeroObject.zero.choose_spec
```

## Filler (hint:2 → hint:3 token-match, ≈184 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
