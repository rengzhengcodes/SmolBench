## Current goal
```
⊢ Finset.inf Finset.univ f = Finset.inf Fintype.elems f
```

## Full tactic state
```
α : Type u
J : Type w
inst✝⁴ : SmallCategory J
inst✝³ : FinCategory J
inst✝² : SemilatticeInf α
inst✝¹ : OrderTop α
ι : Type u
inst✝ : Fintype ι
f : ι → α
⊢ Finset.inf Finset.univ f = Finset.inf Fintype.elems f
```
