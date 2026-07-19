## Current goal
```
⊢ x ∈ RingHom.range (algebraMap (↥S) B) ↔ x ∈ S
```

## Full tactic state
```
A : Type u_1
B✝ : Type u_2
B' : Type u_3
inst✝⁶ : CommRing A
inst✝⁵ : Ring B✝
inst✝⁴ : Algebra A B✝
x✝ : B✝
inst✝³ : Nontrivial B✝
B : Type u_4
inst✝² : CommRing B
inst✝¹ : Algebra A B
inst✝ : Nontrivial B
S : Subalgebra A B
x : B
int : IsIntegral (↥S) x
⊢ x ∈ RingHom.range (algebraMap (↥S) B) ↔ x ∈ S
```
