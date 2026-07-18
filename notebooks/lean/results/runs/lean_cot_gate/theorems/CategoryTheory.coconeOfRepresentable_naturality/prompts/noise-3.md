## Current goal
```
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```

## Full tactic state
```
case w.h.h
C : Type u₁
inst✝¹ : SmallCategory C
ℰ : Type u₂
inst✝ : Category.{u₁, u₂} ℰ
A : C ⥤ ℰ
P₁ P₂ : Cᵒᵖ ⥤ Type u₁
α : P₁ ⟶ P₂
j : (Functor.Elements P₁)ᵒᵖ
T : Cᵒᵖ
f : ((functorToRepresentables P₁).obj j).obj T
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```

## Proof so far (1 tactic)
```lean
ext T f
```

## Theorem
`CategoryTheory.coconeOfRepresentable_naturality` in `Mathlib/CategoryTheory/Limits/Presheaf.lean`

## Premises used in the next tactic
- `CategoryTheory.coconeOfRepresentable_ι_app`
- `CategoryTheory.FunctorToTypes.naturality`

## Premise signatures
### `CategoryTheory.coconeOfRepresentable_ι_app` (commanddeclaration)
```lean
theorem coconeOfRepresentable_ι_app (P : Cᵒᵖ ⥤ Type u₁) (j : P.Elementsᵒᵖ) :
    (coconeOfRepresentable P).ι.app j = (yonedaSectionsSmall _ _).inv j.unop.2
```

### `CategoryTheory.FunctorToTypes.naturality` (commanddeclaration)
```lean
theorem naturality (f : X ⟶ Y) (x : F.obj X) : σ.app Y ((F.map f) x) = (G.map f) (σ.app X x)
```

## Premise full source (with proof)
### `CategoryTheory.coconeOfRepresentable_ι_app` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Presheaf.lean`
```lean
/-- An explicit formula for the legs of the cocone `coconeOfRepresentable`. -/
theorem coconeOfRepresentable_ι_app (P : Cᵒᵖ ⥤ Type u₁) (j : P.Elementsᵒᵖ) :
    (coconeOfRepresentable P).ι.app j = (yonedaSectionsSmall _ _).inv j.unop.2 :=
  colimit.ι_desc _ _
```

### `CategoryTheory.FunctorToTypes.naturality` (commanddeclaration) at `Mathlib/CategoryTheory/Types.lean`
```lean
theorem naturality (f : X ⟶ Y) (x : F.obj X) : σ.app Y ((F.map f) x) = (G.map f) (σ.app X x) :=
  congr_fun (σ.naturality f) x
```

## Filler (hint:2 → hint:3 token-match, ≈642 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pari
