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
