## Current goal
```
⊢ p ∣ Fintype.card { x // (eval x) f₁ = 0 ∧ (eval x) f₂ = 0 }
```

## Full tactic state
```
K : Type u_1
σ : Type u_2
ι : Type u_3
inst✝⁵ : Fintype K
inst✝⁴ : Field K
inst✝³ : Fintype σ
inst✝² : DecidableEq σ
inst✝¹ : DecidableEq K
p : ℕ
inst✝ : CharP K p
f₁ f₂ : MvPolynomial σ K
h : totalDegree f₁ + totalDegree f₂ < Fintype.card σ
F : Bool → MvPolynomial σ K := fun b => bif b then f₂ else f₁
this : ∑ b : Bool, totalDegree (F b) < Fintype.card σ
⊢ p ∣ Fintype.card { x // (eval x) f₁ = 0 ∧ (eval x) f₂ = 0 }
```

## Proof so far (2 tactics)
```lean
let F : Bool → MvPolynomial σ K := fun b => cond b f₂ f₁
have : (∑ b : Bool, (F b).totalDegree) < Fintype.card σ := (add_comm _ _).trans_lt h
```

## Theorem
`char_dvd_card_solutions_of_add_lt` in `Mathlib/FieldTheory/ChevalleyWarning.lean`

## Premises used in the next tactic
- `Bool.forall_bool`
- `char_dvd_card_solutions_of_fintype_sum_lt`

## Premise signatures
### `Bool.forall_bool` (commanddeclaration)
```lean
@[simp]
theorem forall_bool {p : Bool → Prop} : (∀ b, p b) ↔ p false ∧ p true
```

### `char_dvd_card_solutions_of_fintype_sum_lt` (commanddeclaration)
```lean
theorem char_dvd_card_solutions_of_fintype_sum_lt [Fintype ι] {f : ι → MvPolynomial σ K}
    (h : (∑ i, (f i).totalDegree) < Fintype.card σ) :
    p ∣ Fintype.card { x : σ → K // ∀ i, eval x (f i) = 0 }
```

## Premise full source (with proof)
### `Bool.forall_bool` (commanddeclaration) at `Mathlib/Data/Bool/Basic.lean`
```lean
@[simp]
theorem forall_bool {p : Bool → Prop} : (∀ b, p b) ↔ p false ∧ p true :=
  forall_bool' false
```

### `char_dvd_card_solutions_of_fintype_sum_lt` (commanddeclaration) at `Mathlib/FieldTheory/ChevalleyWarning.lean`
```lean
/-- The **Chevalley–Warning theorem**, `Fintype` version.
Let `(f i)` be a finite family of multivariate polynomials
in finitely many variables (`X s`, `s : σ`) over a finite field of characteristic `p`.
Assume that the sum of the total degrees of the `f i` is less than the cardinality of `σ`.
Then the number of common solutions of the `f i` is divisible by `p`. -/
theorem char_dvd_card_solutions_of_fintype_sum_lt [Fintype ι] {f : ι → MvPolynomial σ K}
    (h : (∑ i, (f i).totalDegree) < Fintype.card σ) :
    p ∣ Fintype.card { x : σ → K // ∀ i, eval x (f i) = 0 } := by
  simpa using char_dvd_card_solutions_of_sum_lt p h
```
