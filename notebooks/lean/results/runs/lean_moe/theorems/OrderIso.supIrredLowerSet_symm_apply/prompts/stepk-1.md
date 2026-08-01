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
