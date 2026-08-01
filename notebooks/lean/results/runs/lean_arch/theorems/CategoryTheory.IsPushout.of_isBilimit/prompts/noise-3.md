## Current goal
```
⊢ IsPushout 0 0 b.inl b.inr
```

## Full tactic state
```
C : Type u₁
inst✝² : Category.{v₁, u₁} C
Z X Y P : C
f : Z ⟶ X
g : Z ⟶ Y
inl : X ⟶ P
inr : Y ⟶ P
inst✝¹ : HasZeroObject C
inst✝ : HasZeroMorphisms C
b : BinaryBicone X Y
h : BinaryBicone.IsBilimit b
⊢ IsPushout 0 0 b.inl b.inr
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.IsPushout.of_isBilimit` in `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`

## Premises used in the next tactic
- `CategoryTheory.IsPushout.of_is_coproduct'`
- `CategoryTheory.Limits.HasZeroObject.zeroIsInitial`

## Premise signatures
### `CategoryTheory.IsPushout.of_is_coproduct'` (commanddeclaration)
```lean
theorem of_is_coproduct' (h : Limits.IsColimit (BinaryCofan.mk inl inr)) (t : IsInitial Z) :
    IsPushout (t.to _) (t.to _) inl inr
```

### `CategoryTheory.Limits.HasZeroObject.zeroIsInitial` (commanddeclaration)
```lean
def zeroIsInitial : IsInitial (0 : C)
```

## Premise full source (with proof)
### `CategoryTheory.IsPushout.of_is_coproduct'` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`
```lean
/-- A variant of `of_is_coproduct` that is more useful with `apply`. -/
theorem of_is_coproduct' (h : Limits.IsColimit (BinaryCofan.mk inl inr)) (t : IsInitial Z) :
    IsPushout (t.to _) (t.to _) inl inr :=
  of_is_coproduct h t
```

### `CategoryTheory.Limits.HasZeroObject.zeroIsInitial` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroObjects.lean`
```lean
/-- A zero object is in particular initial. -/
def zeroIsInitial : IsInitial (0 : C) :=
  (isZero_zero C).isInitial
```

## Filler (hint:2 → hint:3 token-match, ≈318 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostr
