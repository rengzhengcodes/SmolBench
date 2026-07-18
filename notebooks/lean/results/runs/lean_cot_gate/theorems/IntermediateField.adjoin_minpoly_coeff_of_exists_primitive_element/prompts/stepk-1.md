## Current goal
```
⊢ finrank (↥K) E = natDegree (minpoly (↥K) α)
```

## Full tactic state
```
F : Type u_1
inst✝⁷ : Field F
E : Type u_2
inst✝⁶ : Field E
inst✝⁵ : Algebra F E
α : E
K✝¹ : Type u
inst✝⁴ : Field K✝¹
inst✝³ : Algebra F K✝¹
L : Type u_3
inst✝² : Field L
inst✝¹ : Algebra K✝¹ L
inst✝ : FiniteDimensional F E
hprim : F⟮α⟯ = ⊤
K✝ : IntermediateField F E
g : E[X] := Polynomial.map (algebraMap (↥K✝) E) (minpoly (↥K✝) α)
K' : IntermediateField F E := adjoin F ↑(frange g)
hsub : K' ≤ K✝
dvd_g : minpoly (↥K') α ∣ toSubring g (Subalgebra.toSubring K'.toSubalgebra) ⋯
K : IntermediateField F E
this : finrank (↥K) E = natDegree (minpoly (↥K) α)
⊢ finrank (↥K) E = natDegree (minpoly (↥K) α)
```
