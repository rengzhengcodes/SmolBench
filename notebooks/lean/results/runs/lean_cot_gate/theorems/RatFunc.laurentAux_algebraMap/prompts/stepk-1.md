## Current goal
```
⊢ (laurentAux r) ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) ((taylor r) p)
```

## Full tactic state
```
R : Type u
inst✝ : CommRing R
hdomain : IsDomain R
r s : R
p q : R[X]
f : RatFunc R
⊢ (laurentAux r) ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) ((taylor r) p)
```
