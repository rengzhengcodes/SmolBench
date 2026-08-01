## Current goal
```
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```

## Full tactic state
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```
