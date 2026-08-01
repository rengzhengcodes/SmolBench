## Current goal
```
⊢ (symm supIrredLowerSet) { val := LowerSet.Iic a, property := hs } =
    sup (Set.toFinset ↑↑{ val := LowerSet.Iic a, property := hs }) id
```

## Full tactic state
```
case mk.intro.intro
α : Type u_1
inst✝³ : SemilatticeSup α
inst✝² : OrderBot α
inst✝¹ : Finite α
a : α
hs : SupIrred (LowerSet.Iic a)
inst✝ : Fintype ↥↑{ val := LowerSet.Iic a, property := hs }
val✝ : Fintype α
this : LocallyFiniteOrder α
⊢ (symm supIrredLowerSet) { val := LowerSet.Iic a, property := hs } =
    sup (Set.toFinset ↑↑{ val := LowerSet.Iic a, property := hs }) id
```

## Proof so far (5 tactics)
```lean
classical
obtain ⟨s, hs⟩ := s
obtain ⟨a, rfl⟩ := supIrred_iff_of_finite.1 hs
cases nonempty_fintype α
have : LocallyFiniteOrder α := Fintype.toLocallyFiniteOrder
simp [symm_apply_eq]
obtain ⟨s, hs⟩ := s
obtain ⟨a, rfl⟩ := supIrred_iff_of_finite.1 hs
cases nonempty_fintype α
have : LocallyFiniteOrder α := Fintype.toLocallyFiniteOrder
```

## Theorem
`OrderIso.supIrredLowerSet_symm_apply` in `Mathlib/Order/Birkhoff.lean`

## Premises used in the next tactic
- `OrderIso.symm_apply_eq`

## Premise signatures
### `OrderIso.symm_apply_eq` (commanddeclaration)
```lean
theorem symm_apply_eq (e : α ≃o β) {x : α} {y : β} : e.symm y = x ↔ y = e x
```

## Premise full source (with proof)
### `OrderIso.symm_apply_eq` (commanddeclaration) at `Mathlib/Order/Hom/Basic.lean`
```lean
theorem symm_apply_eq (e : α ≃o β) {x : α} {y : β} : e.symm y = x ↔ y = e x :=
  e.toEquiv.symm_apply_eq
```
