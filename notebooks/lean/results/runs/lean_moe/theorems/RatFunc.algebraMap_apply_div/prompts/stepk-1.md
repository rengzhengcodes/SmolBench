## Current goal
```
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q
```

## Full tactic state
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (algebraMap F[X] (LaurentSeries F)) p / (algebraMap F[X] (LaurentSeries F)) q
```
