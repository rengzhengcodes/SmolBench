## Current goal
```
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```

## Full tactic state
```
F : Type u
inst✝² : Field F
K : Type v
inst✝¹ : Field K
inst✝ : Algebra F K
f : F[X]
hf : f ≠ 0
h : Splits (RingHom.id K) (map (algebraMap F K) f)
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```
