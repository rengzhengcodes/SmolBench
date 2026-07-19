## Current goal
```
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```

## Full tactic state
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
p✝ : X✝ ⟶ X✝
idem✝ : p✝ ≫ p✝ = p✝
h_p : p✝¹ ≫ eqToHom ⋯ = eqToHom ⋯ ≫ p✝
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```

## Proof so far (4 tactics)
```lean
cases P
cases Q
dsimp at h_X h_p
subst h_X
```

## Theorem
`CategoryTheory.Idempotents.Karoubi.ext` in `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`

## Premises used in the next tactic
- `heq_eq_eq`
- `true_and`
- `CategoryTheory.eqToHom_refl`
- `CategoryTheory.Category.comp_id`
- `CategoryTheory.Category.id_comp`

## Premise signatures
### `heq_eq_eq` (commanddeclaration)
```lean
@[simp] theorem heq_eq_eq {α : Sort u} (a b : α) : HEq a b = (a = b)
```

### `true_and` (commanddeclaration)
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration)
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_

## Premise full source (with proof)
### `heq_eq_eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem heq_eq_eq {α : Sort u} (a b : α) : HEq a b = (a = b) := propext <| Iff.intro eq_of_heq heq_of_eq
```

### `true_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p := propext ⟨(·.2), (⟨trivial, ·⟩)⟩
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration) at `Mathlib/CategoryTheory/EqToHom.lean`
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X :=
  rfl
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_
