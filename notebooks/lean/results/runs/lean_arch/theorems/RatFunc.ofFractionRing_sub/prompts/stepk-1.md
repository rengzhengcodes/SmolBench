## Current goal
```
⊢ { toFractionRing := p - q } = { toFractionRing := p } - { toFractionRing := q }
```

## Full tactic state
```
K : Type u
inst✝ : CommRing K
p q : FractionRing K[X]
⊢ { toFractionRing := p - q } = { toFractionRing := p } - { toFractionRing := q }
```
