## Current goal
```
⊢ pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u₂
inst✝³ : Category.{v₂, u₂} D
W X Y Z : C
f : X ⟶ Y
g : X ⟶ Z
g' : Z ⟶ W
inst✝² : HasPushout f g
inst✝¹ : HasPushout pushout.inr g'
inst✝ : HasPushout f (g ≫ g')
⊢ pushout.inl ≫ pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').hom = pushout.inl
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom` in `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Iso.eq_comp_inv`
- `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration)
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f
```

### `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem inl_pushoutLeftPushoutInrIso_inv :
    pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv = pushout.inl ≫ pushout.inl
```

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f :=
  (comp_inv_eq α.symm).symm
```

### `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
@[reassoc (attr := simp)]
theorem inl_pushoutLeftPushoutInrIso_inv :
    pushout.inl ≫ (pushoutLeftPushoutInrIso f g g').inv = pushout.inl ≫ pushout.inl :=
  ((bigSquareIsPushout g g' _ _ f _ _ pushout.condition pushout.condition (pushoutIsPushout _ _)
          (pushoutIsPushout _ _)).comp_coconePointUniqueUpToIso_inv
      (pushoutIsPushout _ _) WalkingSpan.left :
    _)
```

## Transitive premise context (1-hop, 5/5 premises, ≈1010 tokens)
### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.pushoutLeftPushoutInrIso` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- The canonical isomorphism `(Y ⨿[X] Z) ⨿[Z] W ≅ Y ×[X] W` -/
noncomputable def pushoutLeftPushoutInrIso :
    pushout (pushout.inr : _ ⟶ pushout f g) g' ≅ pushout f (g ≫ g') :=
  ((bigSquareIsPushout g g' _ _ f _ _ pushout.condition pushout.condition (pushoutIsPushout _ _)
          (pushoutIsPushout _ _)).coconePointUniqueUpToIso
      (pushoutIsPushout _ _) :
    _)
```

### `CategoryTheory.Limits.bigSquareIsPushout` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- Given

X₁ - f₁ -> X₂ - f₂ -> X₃
|          |          |
i₁         i₂         i₃
∨          ∨          ∨
Y₁ - g₁ -> Y₂ - g₂ -> Y₃

Then the big square is a pushout if both the small squares are.
-/
def bigSquareIsPushout (H : IsColimit (PushoutCocone.mk _ _ h₂))
    (H' : IsColimit (PushoutCocone.mk _ _ h₁)) :
    IsColimit
      (PushoutCocone.mk _ _
        (show i₁ ≫ g₁ ≫ g₂ = (f₁ ≫ f₂) ≫ i₃ by
          rw [← Category.assoc, h₁, Category.assoc, h₂, Category.assoc])) := by
  fapply PushoutCocone.isColimitAux'
  intro s
  have : i₁ ≫ s.inl = f₁ ≫ f₂ ≫ s.inr := by rw [s.condition, Category.assoc]
  rcases PushoutCocone.IsColimit.desc' H' s.inl (f₂ ≫ s.inr) this with ⟨l₁, hl₁, hl₁'⟩
  rcases PushoutCocone.IsColimit.desc' H l₁ s.inr hl₁' with ⟨l₂, hl₂, hl₂'⟩
  use l₂
  use
    show (g₁ ≫ g₂) ≫ l₂ = s.inl by
      rw [← hl₁, ← hl₂, Category.assoc]
      rfl
  use hl₂'
  intro m hm₁ hm₂
  apply PushoutCocone.IsColimit.hom_ext H
  · apply PushoutCocone.IsColimit.hom_ext H'
    · erw [← Category.assoc, hm₁, hl₂, hl₁]
    · erw [← Category.assoc, h₂, Category.assoc, hm₂, ← hl₂', ← Category.assoc, ← Category.assoc, ←
        h₂]
      rfl
  · erw [hm₂, hl₂']
```

### `CategoryTheory.Limits.pushoutIsPushout` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- The pushout cocone built from the pushout coprojections is a pushout. -/
def pushoutIsPushout {X Y Z : C} (f : X ⟶ Y) (g : X ⟶ Z) [HasPushout f g] :
    IsColimit (PushoutCocone.mk (pushout.inl : _ ⟶ pushout f g) pushout.inr pushout.condition) :=
  PushoutCocone.IsColimit.mk _ (fun s => pushout.desc s.inl s.inr s.condition) (by simp) (by simp)
    (by aesop_cat)
```
