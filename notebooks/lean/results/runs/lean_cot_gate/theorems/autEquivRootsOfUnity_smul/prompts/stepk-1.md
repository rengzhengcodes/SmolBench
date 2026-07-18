## Current goal
```
⊢ (autEquivRootsOfUnity ⋯ hn H L) σ • ζ ^ i • rootOfSplitsXPowSubC hn a L =
    ζ ^ i • (autEquivRootsOfUnity hζ hn H L) σ • rootOfSplitsXPowSubC hn a L
```

## Full tactic state
```
case intro.intro
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
σ : L ≃ₐ[K] L
ζ : K
hζ'✝ : ζ ∈ primitiveRoots n K
hζ' : IsPrimitiveRoot ζ n
i : ℕ
left✝ : i < n
⊢ (autEquivRootsOfUnity ⋯ hn H L) σ • ζ ^ i • rootOfSplitsXPowSubC hn a L =
    ζ ^ i • (autEquivRootsOfUnity hζ hn H L) σ • rootOfSplitsXPowSubC hn a L
```
