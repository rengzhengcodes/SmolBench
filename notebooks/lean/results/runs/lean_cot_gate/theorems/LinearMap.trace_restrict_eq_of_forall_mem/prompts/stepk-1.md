## Current goal
```
⊢ ∀ x ∈ Finset.univ, B x x ≠ 0 → (fun j => j ∈ Set.range ⇑snf.f) x
```

## Full tactic state
```
R : Type u_1
M : Type u_2
inst✝⁶ : CommRing R
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
inst✝³ : Module.Finite R M
inst✝² : Module.Free R M
inst✝¹ : IsDomain R
inst✝ : IsPrincipalIdealRing R
p : Submodule R M
f : M →ₗ[R] M
hf : ∀ (x : M), f x ∈ p
hf' : optParam (∀ x ∈ p, f x ∈ p) ⋯
ι : Type u_2 := Module.Free.ChooseBasisIndex R M
n : ℕ
snf : Basis.SmithNormalForm p ι n
A : Matrix (Fin n) (Fin n) R := (toMatrix snf.bN snf.bN) (restrict f hf')
B : Matrix ι ι R := (toMatrix snf.bM snf.bM) f
aux : ∀ (i : ι), B i i ≠ 0 → i ∈ Set.range ⇑snf.f
⊢ ∀ x ∈ Finset.univ, B x x ≠ 0 → (fun j => j ∈ Set.range ⇑snf.f) x
```
