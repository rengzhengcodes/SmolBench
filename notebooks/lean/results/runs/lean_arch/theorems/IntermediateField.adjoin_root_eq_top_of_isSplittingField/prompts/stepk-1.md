## Current goal
```
⊢ ⊤.toSubalgebra = Algebra.adjoin K {α}
```

## Full tactic state
```
K : Type u
inst✝³ : Field K
n : ℕ
hζ : (primitiveRoots n K).Nonempty
hn : 0 < n
a : K
H : Irreducible (X ^ n - C a)
L : Type u_1
inst✝² : Field L
inst✝¹ : Algebra K L
inst✝ : IsSplittingField K L (X ^ n - C a)
α : L
hα : α ^ n = (algebraMap K L) a
⊢ ⊤.toSubalgebra = Algebra.adjoin K {α}
```
