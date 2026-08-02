## Current goal
```
⊢ extract.loop as size start bs = bs ++ extract.loop as size start #[]
```

## Full tactic state
```
case e_xs
α : Type u_1
i : Nat
as bs : Array α
size start : Nat
hlt : i < Array.size bs
h : optParam (i < Array.size (extract.loop as size start bs)) ⋯
⊢ extract.loop as size start bs = bs ++ extract.loop as size start #[]
```
