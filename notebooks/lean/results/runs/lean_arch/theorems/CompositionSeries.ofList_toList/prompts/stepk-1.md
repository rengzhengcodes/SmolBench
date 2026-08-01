## Current goal
```
⊢ (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = s.series (Fin.cast ⋯ { val := i, isLt := hi })
```

## Full tactic state
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
hi : i < (ofList (toList s) ⋯ ⋯).length + 1
⊢ (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = s.series (Fin.cast ⋯ { val := i, isLt := hi })
```
