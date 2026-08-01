## Current goal
```
⊢ PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd ⋯ ≫ g = pullback.snd
```

## Full tactic state
```
case h.a.g.refine'_2
C : Type u₁
inst✝⁴ : Category.{v₁, u₁} C
X✝ Y✝ Z✝ : C
D : Type u₂
inst✝³ : Category.{v₂, u₂} D
inst✝² : HasPullbacks C
X Y Z W : C
f : X ⟶ Y
g : X ⟶ Z
h : Y ⟶ W
k : Z ⟶ W
inst✝¹ : Mono h
inst✝ : Mono g
comm : f ≫ h = g ≫ k
t : IsLimit (PullbackCone.mk f g comm)
a : MonoOver Y
⊢ PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd ⋯ ≫ g = pullback.snd
```

## Proof so far (13 tactics)
```lean
revert p
apply Quotient.ind'
intro a
apply Quotient.sound
apply ThinSkeleton.equiv_of_both_ways
refine' MonoOver.homMk (pullback.lift pullback.fst _ _) (pullback.lift_snd _ _ _)
change _ ≫ a.arrow ≫ h = (pullback.snd ≫ g) ≫ _
rw [assoc, ← comm, pullback.condition_assoc]
refine' MonoOver.homMk (pullback.lift pullback.fst
  (PullbackCone.IsLimit.lift t (pullback.fst ≫ a.arrow) pullback.snd _)
  (PullbackCone.IsLimit.lift_fst _ _ _ _).symm) _
rw [← pullback.condition, assoc]
rfl
dsimp
rw [pullback.lift_snd_assoc]
```

## Theorem
`CategoryTheory.Subobject.map_pullback` in `Mathlib/CategoryTheory/Subobject/Basic.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd`

## Premise signatures
### `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd` (lemma)
```lean
@[reassoc (attr := simp)]
lemma IsLimit.lift_snd {t : PullbackCone f g} (ht : IsLimit t) {W : C} (h : W ⟶ X) (k : W ⟶ Y)
    (w : h ≫ f = k ≫ g) : IsLimit.lift ht h k w ≫ snd t = k
```

## Premise full source (with proof)
### `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd` (lemma) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
@[reassoc (attr := simp)]
lemma IsLimit.lift_snd {t : PullbackCone f g} (ht : IsLimit t) {W : C} (h : W ⟶ X) (k : W ⟶ Y)
    (w : h ≫ f = k ≫ g) : IsLimit.lift ht h k w ≫ snd t = k := ht.fac _ _

/-- If `t` is a limit pullback cone over `f` and `g` and `h : W ⟶ X` and `k : W ⟶ Y` are such that
    `h ≫ f = k ≫ g`, then we have `l : W ⟶ t.pt` satisfying `l ≫ fst t = h` and `l ≫ snd t = k`.
    -/
```
