## Current goal
```
⊢ ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r
```

## Full tactic state
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s t : Finset ι
i j : ι
v r r' : ι → F
f : F[X]
hvs : Set.InjOn v ↑s
degree_f_lt : degree f < ↑s.card
eval_f : ∀ i ∈ s, eval (v i) f = r i
⊢ ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r
```

## Proof so far (1 tactic)
```lean
rw [eq_interpolate hvs degree_f_lt]
```

## Theorem
`Lagrange.eq_interpolate_of_eval_eq` in `Mathlib/LinearAlgebra/Lagrange.lean`

## Premises used in the next tactic
- `Lagrange.interpolate_eq_of_values_eq_on`

## Premise signatures
### `Lagrange.interpolate_eq_of_values_eq_on` (commanddeclaration)
```lean
theorem interpolate_eq_of_values_eq_on (hrr' : ∀ i ∈ s, r i = r' i) :
    interpolate s v r = interpolate s v r'
```

## Premise full source (with proof)
### `Lagrange.interpolate_eq_of_values_eq_on` (commanddeclaration) at `Mathlib/LinearAlgebra/Lagrange.lean`
```lean
theorem interpolate_eq_of_values_eq_on (hrr' : ∀ i ∈ s, r i = r' i) :
    interpolate s v r = interpolate s v r' :=
  sum_congr rfl fun i hi => by rw [hrr' _ hi]
```

## Transitive premise context (1-hop, 3/3 premises, ≈973 tokens)
### `Localization.r'` (commanddeclaration) at `Mathlib/GroupTheory/MonoidLocalization.lean`
```lean
/-- An alternate form of the congruence relation on `M × S`, `M` a `CommMonoid` and `S` a
submonoid of `M`, whose quotient is the localization of `M` at `S`. -/
@[to_additive AddLocalization.r'
    "An alternate form of the congruence relation on `M × S`, `M` a `CommMonoid` and `S` a
submonoid of `M`, whose quotient is the localization of `M` at `S`."]
def r' : Con (M × S) := by
  -- note we multiply by `c` on the left so that we can later generalize to `•`
  refine
    { r := fun a b : M × S ↦ ∃ c : S, ↑c * (↑b.2 * a.1) = c * (a.2 * b.1)
      iseqv := ⟨fun a ↦ ⟨1, rfl⟩, fun ⟨c, hc⟩ ↦ ⟨c, hc.symm⟩, ?_⟩
      mul' := ?_ }
  · rintro a b c ⟨t₁, ht₁⟩ ⟨t₂, ht₂⟩
    use t₂ * t₁ * b.2
    simp only [Submonoid.coe_mul]
    calc
      (t₂ * t₁ * b.2 : M) * (c.2 * a.1) = t₂ * c.2 * (t₁ * (b.2 * a.1)) := by ac_rfl
      _ = t₁ * a.2 * (t₂ * (c.2 * b.1)) := by rw [ht₁]; ac_rfl
      _ = t₂ * t₁ * b.2 * (a.2 * c.1) := by rw [ht₂]; ac_rfl
  · rintro a b c d ⟨t₁, ht₁⟩ ⟨t₂, ht₂⟩
    use t₂ * t₁
    calc
      (t₂ * t₁ : M) * (b.2 * d.2 * (a.1 * c.1)) = t₂ * (d.2 * c.1) * (t₁ * (b.2 * a.1)) := by ac_rfl
      _ = (t₂ * t₁ : M) * (a.2 * c.2 * (b.1 * d.1)) := by rw [ht₁, ht₂]; ac_rfl
```

### `Lagrange.interpolate` (commanddeclaration) at `Mathlib/LinearAlgebra/Lagrange.lean`
```lean
/-- Lagrange interpolation: given a finset `s : Finset ι`, a nodal map `v : ι → F` injective on
`s` and a value function `r : ι → F`, `interpolate s v r` is the unique
polynomial of degree `< s.card` that takes value `r i` on `v i` for all `i` in `s`. -/
@[simps]
def interpolate (s : Finset ι) (v : ι → F) : (ι → F) →ₗ[F] F[X] where
  toFun r := ∑ i in s, C (r i) * Lagrange.basis s v i
  map_add' f g := by
    simp_rw [← Finset.sum_add_distrib]
    have h : (fun x => C (f x) * Lagrange.basis s v x + C (g x) * Lagrange.basis s v x) =
    (fun x => C ((f + g) x) * Lagrange.basis s v x) := by
      simp_rw [← add_mul, ← C_add, Pi.add_apply]
    rw [h]
  map_smul' c f := by
    simp_rw [Finset.smul_sum, C_mul', smul_smul, Pi.smul_apply, RingHom.id_apply, smul_eq_mul]
```

### `MeasureTheory.Measure.sum_congr` (commanddeclaration) at `Mathlib/MeasureTheory/Measure/MeasureSpace.lean`
```lean
theorem sum_congr {μ ν : ℕ → Measure α} (h : ∀ n, μ n = ν n) : sum μ = sum ν :=
  congr_arg sum (funext h)
```
