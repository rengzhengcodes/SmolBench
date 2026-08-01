## Current goal
```
⊢ map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_2, u_1} C
X✝ Y✝ Z : C
inst✝¹ : HasPullbacks C
X Y S X' Y' S' : C
f : X ⟶ S
g : Y ⟶ S
f' : X' ⟶ S'
g' : Y' ⟶ S'
i₁ : X ⟶ X'
i₂ : Y ⟶ Y'
i₃ : S ⟶ S'
e₁ : f ≫ i₃ = i₁ ≫ f'
e₂ : g ≫ i₃ = i₂ ≫ g'
inst✝ : Mono i₃
⊢ map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv` in `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.pullbackFstFstIso_inv`
- `CategoryTheory.Limits.pullback.lift_snd_assoc`
- `CategoryTheory.Limits.pullback.lift_fst`

## Premise signatures
### `CategoryTheory.Limits.pullbackFstFstIso_inv`
_(not found in premise corpus)_

### `CategoryTheory.Limits.pullback.lift_snd_assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.pullback.lift_fst` (commanddeclaration)
```lean
@[reassoc]
theorem pullback.lift_fst {W X Y Z : C} {f : X ⟶ Z} {g : Y ⟶ Z} [HasPullback f g] (h : W ⟶ X)
    (k : W ⟶ Y) (w : h ≫ f = k ≫ g) : pullback.lift h k w ≫ pullback.fst = h
```

## Premise full source (with proof)
### `CategoryTheory.Limits.pullbackFstFstIso_inv`
_(not found in premise corpus)_

### `CategoryTheory.Limits.pullback.lift_snd_assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.pullback.lift_fst` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
@[reassoc]
theorem pullback.lift_fst {W X Y Z : C} {f : X ⟶ Z} {g : Y ⟶ Z} [HasPullback f g] (h : W ⟶ X)
    (k : W ⟶ Y) (w : h ≫ f = k ≫ g) : pullback.lift h k w ≫ pullback.fst = h :=
  limit.lift_π _ _
```

## Filler (hint:2 → hint:3 token-match, ≈134 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
