## Current goal
```
⊢ natSepDegree f = natDegree f ↔ (Multiset.toFinset (aroots f (SplittingField f))).card = natDegree f
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Algebra F E
K : Type w
inst✝¹ : Field K
inst✝ : Algebra F K
f : F[X]
hf : f ≠ 0
⊢ natSepDegree f = natDegree f ↔ (Multiset.toFinset (aroots f (SplittingField f))).card = natDegree f
```
