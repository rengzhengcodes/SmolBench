## Current goal
```
⊢ Separable (minpoly F (v y))
```

## Full tactic state
```
case intro
F : Type u
E : Type v
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Algebra F E
K : Type w
inst✝¹ : Field K
inst✝ : Algebra F K
q n : ℕ
hF : ExpChar F q
ι : Type u_1
v : ι → E
hsep : ∀ (i : ι), Separable (minpoly F (v i))
h : LinearIndependent F v
E' : IntermediateField F E := adjoin F (Set.range v)
y : ι
⊢ Separable (minpoly F (v y))
```
