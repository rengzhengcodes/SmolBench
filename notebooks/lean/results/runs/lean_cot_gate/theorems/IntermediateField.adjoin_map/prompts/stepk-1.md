## Current goal
```
⊢ x ∈ Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑↑f '' S) ↔
    x ∈ Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑f '' S)
```

## Full tactic state
```
case h
F : Type u_1
inst✝⁴ : Field F
E : Type u_2
inst✝³ : Field E
inst✝² : Algebra F E
S : Set E
E' : Type u_3
inst✝¹ : Field E'
inst✝ : Algebra F E'
f : E →ₐ[F] E'
x : E'
⊢ x ∈ Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑↑f '' S) ↔
    x ∈ Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑f '' S)
```
