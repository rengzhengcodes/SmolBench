## Current goal
```
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```

## Full tactic state
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
X Y Z : C
f : X ⟶ Z
g : Y ⟶ Z
inst✝¹ : HasPullback f g
inst✝ : HasPushout f.op g.op
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```

## Proof so far (2 tactics)
```lean
apply Quiver.Hom.unop_inj
dsimp
```

## Theorem
`CategoryTheory.Limits.pullbackIsoUnopPushout_hom_inl` in `Mathlib/CategoryTheory/Limits/Opposites.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst`
- `CategoryTheory.Iso.hom_inv_id_assoc`

## Premise signatures
### `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem pullbackIsoUnopPushout_inv_fst {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g]
    [HasPushout f.op g.op] :
    (pullbackIsoUnopPushout f g).inv ≫ pullback.fst = (pushout.inl : _ ⟶ pushout f.op g.op).unop
```

### `CategoryTheory.Iso.hom_inv_id_assoc`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Opposites.lean`
```lean
@[reassoc (attr := simp)]
theorem pullbackIsoUnopPushout_inv_fst {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g]
    [HasPushout f.op g.op] :
    (pullbackIsoUnopPushout f g).inv ≫ pullback.fst = (pushout.inl : _ ⟶ pushout f.op g.op).unop :=
  (IsLimit.conePointUniqueUpToIso_inv_comp _ _ _).trans (by simp [unop_id (X := { unop := X })])
```

### `CategoryTheory.Iso.hom_inv_id_assoc`
_(not found in premise corpus)_

## Filler (hint:2 → hint:3 token-match, ≈621 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
