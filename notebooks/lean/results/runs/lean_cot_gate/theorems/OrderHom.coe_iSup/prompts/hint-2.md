## Current goal
```
⊢ (⨆ i, f i) x = iSup (fun i => ⇑(f i)) x
```

## Full tactic state
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
f : ι → α →o β
x : α
⊢ (⨆ i, f i) x = iSup (fun i => ⇑(f i)) x
```

## Proof so far (1 tactic)
```lean
funext x
```

## Theorem
`OrderHom.coe_iSup` in `Mathlib/Order/Hom/Order.lean`

## Premises used in the next tactic
- `OrderHom.iSup_apply`

## Premise signatures
### `OrderHom.iSup_apply` (commanddeclaration)
```lean
theorem iSup_apply {ι : Sort*} [CompleteLattice β] (f : ι → α →o β) (x : α) :
    (⨆ i, f i) x = ⨆ i, f i x
```

## Premise full source (with proof)
### `OrderHom.iSup_apply` (commanddeclaration) at `Mathlib/Order/Hom/Order.lean`
```lean
theorem iSup_apply {ι : Sort*} [CompleteLattice β] (f : ι → α →o β) (x : α) :
    (⨆ i, f i) x = ⨆ i, f i x :=
  (sSup_apply _ _).trans iSup_range
```
