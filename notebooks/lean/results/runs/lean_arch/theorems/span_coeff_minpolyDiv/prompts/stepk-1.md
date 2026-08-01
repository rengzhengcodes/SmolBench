## Current goal
```
⊢ i ≤ natDegree (minpolyDiv R x)
```

## Full tactic state
```
case a.refine_2
R : Type u_2
K : Type ?u.90304
L : Type ?u.90307
S : Type u_1
inst✝⁵ : CommRing R
inst✝⁴ : Field K
inst✝³ : Field L
inst✝² : CommRing S
inst✝¹ : Algebra R S
inst✝ : Algebra K L
x : S
hx : IsIntegral R x
a✝ : Nontrivial S
i✝ i : ℕ
hi :
  ∀ m < i,
    m ∈ Set.Iio (natDegree (minpoly R x)) →
      m ∈ (fun x_1 => x ^ x_1) ⁻¹' ↑(Submodule.span R (Set.range (coeff (minpolyDiv R x))))
hi' : i ∈ Set.Iio (natDegree (minpoly R x))
this : coeff (minpolyDiv R x) (natDegree (minpolyDiv R x) - i) ∈ Submodule.span R (Set.range (coeff (minpolyDiv R x)))
⊢ i ≤ natDegree (minpolyDiv R x)
```
