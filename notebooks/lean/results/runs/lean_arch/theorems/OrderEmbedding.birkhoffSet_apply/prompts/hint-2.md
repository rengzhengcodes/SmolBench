## Current goal
```
⊢ OrderIso.lowerSetSupIrred a = OrderIso.lowerSetSupIrred a
```

## Full tactic state
```
α : Type u_1
inst✝⁴ : DistribLattice α
inst✝³ : OrderBot α
inst✝² : Fintype α
inst✝¹ : DecidablePred SupIrred
inst✝ : DecidableEq α
a : α
⊢ OrderIso.lowerSetSupIrred a = OrderIso.lowerSetSupIrred a
```

## Proof so far (1 tactic)
```lean
simp [birkhoffSet]
```

## Theorem
`OrderEmbedding.birkhoffSet_apply` in `Mathlib/Order/Birkhoff.lean`

## Premises used in the next tactic
- `rfl`

## Premise signatures
### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

## Premise full source (with proof)
### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```
