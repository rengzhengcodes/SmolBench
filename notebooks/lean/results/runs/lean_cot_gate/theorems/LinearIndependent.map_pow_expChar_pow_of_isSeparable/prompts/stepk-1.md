## Current goal
```
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁵ : Field F
inst✝⁴ : Field E
inst✝³ : Algebra F E
K : Type w
inst✝² : Field K
inst✝¹ : Algebra F K
q n : ℕ
hF : ExpChar F q
ι : Type u_1
v : ι → E
inst✝ : IsSeparable F E
h : ∀ (s : Finset ι), LinearIndependent F (v ∘ Subtype.val)
halg : Algebra.IsAlgebraic F E
s : Finset ι
E' : IntermediateField F E := adjoin F ↑(Finset.image v s)
this✝ : FiniteDimensional F ↥E'
this : IsSeparable F ↥E'
v' : { x // x ∈ s } → ↥E' := fun i => { val := v ↑i, property := ⋯ }
h' : LinearIndependent F v'
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```
