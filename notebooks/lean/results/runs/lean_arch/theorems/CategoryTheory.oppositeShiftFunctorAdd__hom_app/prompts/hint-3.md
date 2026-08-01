## Current goal
```
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_3, u_1} C
A : Type u_2
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
X : OppositeShift C A
a b : A
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```

## Proof so far (1 tactic)
```lean
subst h
```

## Theorem
`CategoryTheory.oppositeShiftFunctorAdd'_hom_app` in `Mathlib/CategoryTheory/Shift/Opposite.lean`

## Premises used in the next tactic
- `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`
- `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Premise signatures
### `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd` (lemma)
```lean
lemma shiftFunctorAdd'_eq_shiftFunctorAdd (i j : A) :
    shiftFunctorAdd' C i j (i+j) rfl = shiftFunctorAdd C i j
```

### `CategoryTheory.oppositeShiftFunctorAdd_hom_app` (lemma)
```lean
lemma oppositeShiftFunctorAdd_hom_app :
    (shiftFunctorAdd (OppositeShift C A) a b).hom.app X =
      ((shiftFunctorAdd C a b).inv.app X.unop).op
```

## Premise full source (with proof)
### `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd` (lemma) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
lemma shiftFunctorAdd'_eq_shiftFunctorAdd (i j : A) :
    shiftFunctorAdd' C i j (i+j) rfl = shiftFunctorAdd C i j := by
  ext1
  apply Category.id_comp
```

### `CategoryTheory.oppositeShiftFunctorAdd_hom_app` (lemma) at `Mathlib/CategoryTheory/Shift/Opposite.lean`
```lean
lemma oppositeShiftFunctorAdd_hom_app :
    (shiftFunctorAdd (OppositeShift C A) a b).hom.app X =
      ((shiftFunctorAdd C a b).inv.app X.unop).op := by
  rw [← cancel_mono ((shiftFunctorAdd (OppositeShift C A) a b).inv.app X),
    Iso.hom_inv_id_app, oppositeShiftFunctorAdd_inv_app, ← op_comp,
    Iso.hom_inv_id_app, op_id]
  rfl
```

## Transitive premise context (1-hop, 4/4 premises, ≈403 tokens)
### `CategoryTheory.OppositeShift` (commanddeclaration) at `Mathlib/CategoryTheory/Shift/Opposite.lean`
```lean
/-- The category `OppositeShift C A` is the opposite category `Cᵒᵖ` equipped
with the naive shift: `shiftFunctor (OppositeShift C A) n` is `(shiftFunctor C n).op`. -/
@[nolint unusedArguments]
def OppositeShift (A : Type*) [AddMonoid A] [HasShift C A] := Cᵒᵖ
```

### `CategoryTheory.cancel_mono` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem cancel_mono (f : X ⟶ Y) [Mono f] {g h : Z ⟶ X} : g ≫ f = h ≫ f ↔ g = h :=
  -- Porting note: in Lean 3 we could just write `congr_arg _` here.
  ⟨fun p => Mono.right_cancellation g h p, congr_arg (fun k => k ≫ f)⟩
```

### `CategoryTheory.oppositeShiftFunctorAdd_inv_app` (lemma) at `Mathlib/CategoryTheory/Shift/Opposite.lean`
```lean
lemma oppositeShiftFunctorAdd_inv_app :
    (shiftFunctorAdd (OppositeShift C A) a b).inv.app X =
      ((shiftFunctorAdd C a b).hom.app X.unop).op := rfl
```

### `CategoryTheory.op_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Opposites.lean`
```lean
@[simp, reassoc]
theorem op_comp {X Y Z : C} {f : X ⟶ Y} {g : Y ⟶ Z} : (f ≫ g).op = g.op ≫ f.op :=
  rfl
```
