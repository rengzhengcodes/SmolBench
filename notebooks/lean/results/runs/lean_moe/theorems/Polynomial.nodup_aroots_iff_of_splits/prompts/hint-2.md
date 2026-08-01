## Current goal
```
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```

## Full tactic state
```
F : Type u
inst✝² : Field F
K : Type v
inst✝¹ : Field K
inst✝ : Algebra F K
f : F[X]
hf : f ≠ 0
h : Splits (RingHom.id K) (map (algebraMap F K) f)
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```

## Proof so far (1 tactic)
```lean
rw [← (algebraMap F K).id_comp, ← splits_map_iff] at h
```

## Theorem
`Polynomial.nodup_aroots_iff_of_splits` in `Mathlib/FieldTheory/Separable.lean`

## Premises used in the next tactic
- `Polynomial.nodup_roots_iff_of_splits`
- `Polynomial.map_ne_zero`
- `Polynomial.separable_map`

## Premise signatures
### `Polynomial.nodup_roots_iff_of_splits` (commanddeclaration)
```lean
theorem nodup_roots_iff_of_splits {f : F[X]} (hf : f ≠ 0) (h : f.Splits (RingHom.id F)) :
    f.roots.Nodup ↔ f.Separable
```

### `Polynomial.map_ne_zero` (commanddeclaration)
```lean
theorem map_ne_zero [Semiring S] [Nontrivial S] {f : R →+* S} (hp : p ≠ 0) : p.map f ≠ 0
```

### `Polynomial.separable_map` (commanddeclaration)
```lean
theorem separable_map {S} [CommRing S] [Nontrivial S] (f : F →+* S) {p : F[X]} :
    (p.map f).Separable ↔ p.Separable
```

## Premise full source (with proof)
### `Polynomial.nodup_roots_iff_of_splits` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
/-- If a non-zero polynomial splits, then it has no repeated roots on that field
if and only if it is separable. -/
theorem nodup_roots_iff_of_splits {f : F[X]} (hf : f ≠ 0) (h : f.Splits (RingHom.id F)) :
    f.roots.Nodup ↔ f.Separable := by
  refine ⟨(fun hnsep ↦ ?_).mtr, nodup_roots⟩
  rw [Separable, ← gcd_isUnit_iff, isUnit_iff_degree_eq_zero] at hnsep
  obtain ⟨x, hx⟩ := exists_root_of_splits _
    (splits_of_splits_of_dvd _ hf h (gcd_dvd_left f _)) hnsep
  simp_rw [Multiset.nodup_iff_count_le_one, not_forall, not_le]
  exact ⟨x, ((one_lt_rootMultiplicity_iff_isRoot_gcd hf).2 hx).trans_eq f.count_roots.symm⟩

/-- If a non-zero polynomial over `F` splits in `K`, then it has no repeated roots on `K`
if and only if it is separable. -/
```

### `Polynomial.map_ne_zero` (commanddeclaration) at `Mathlib/Data/Polynomial/FieldDivision.lean`
```lean
theorem map_ne_zero [Semiring S] [Nontrivial S] {f : R →+* S} (hp : p ≠ 0) : p.map f ≠ 0 :=
  mt (map_eq_zero f).1 hp
```

### `Polynomial.separable_map` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
theorem separable_map {S} [CommRing S] [Nontrivial S] (f : F →+* S) {p : F[X]} :
    (p.map f).Separable ↔ p.Separable := by
  refine ⟨fun H ↦ ?_, fun H ↦ H.map⟩
  obtain ⟨m, hm⟩ := Ideal.exists_maximal S
  have := Separable.map H (f := Ideal.Quotient.mk m)
  rwa [map_map, separable_def, derivative_map, isCoprime_map] at this
```
