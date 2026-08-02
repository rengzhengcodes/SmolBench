## Current goal
```
⊢ η.app (op (op X).unop) (val p) = yonedaEquiv s
```

## Full tactic state
```
C : Type u
inst✝ : Category.{v, u} C
A : Cᵒᵖ ⥤ Type v
Y : C
η : yoneda.obj Y ⟶ A
X : C
s : yoneda.obj X ⟶ A
p : OverArrows η s
⊢ η.app (op (op X).unop) (val p) = yonedaEquiv s
```

## Proof so far (1 tactic)
```lean
rw [← yonedaEquiv.injective.eq_iff, yonedaEquiv_comp, yonedaEquiv_yoneda_map]
```

## Theorem
`CategoryTheory.OverPresheafAux.OverArrows.map_val` in `Mathlib/CategoryTheory/Comma/Presheaf.lean`

## Premises used in the next tactic
- `Opposite.unop_op`

## Premise signatures
### `Opposite.unop_op` (commanddeclaration)
```lean
@[simp]
theorem unop_op (x : α) : unop (op x) = x
```

## Premise full source (with proof)
### `Opposite.unop_op` (commanddeclaration) at `Mathlib/Data/Opposite.lean`
```lean
@[simp]
theorem unop_op (x : α) : unop (op x) = x :=
  rfl
```
