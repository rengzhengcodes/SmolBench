## Current goal
```
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
```

## Full tactic state
```
R : Type u_1
inst✝⁴ : CommRing R
inst✝³ : IsDomain R
p n : ℕ
inst✝² : ExpChar R p
f : R[X]
inst✝¹ : PerfectRing R p
inst✝ : DecidableEq R
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Polynomial.roots_expand_image_frobenius` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `Finset.image_toFinset`
- `Polynomial.roots_expand_map_frobenius`
- `Polynomial.roots`
- `Multiset.toFinset_nsmul`
- `expChar_pos`
- `LT.lt.ne'`

## Premise signatures
### `Finset.image_toFinset` (commanddeclaration)
```lean
theorem image_toFinset [DecidableEq α] {s : Multiset α} :
    s.toFinset.image f = (s.map f).toFinset
```

### `Polynomial.roots_expand_map_frobenius` (commanddeclaration)
```lean
theorem roots_expand_map_frobenius : (expand R p f).roots.map (frobenius R p) = p • f.roots
```

### `Polynomial.roots` (commanddeclaration)
```lean
noncomputable def roots (p : R[X]) : Multiset R
```

### `Multiset.toFinset_nsmul` (commanddeclaration)
```lean
@[simp]
theorem toFinset_nsmul (s : Multiset α) : ∀ n ≠ 0, (n • s).toFinset = s.toFinset
```

### `expChar_pos` (commanddeclaration)
```lean
theorem expChar_pos (q : ℕ) [ExpChar R q] : 0 < q
```

### `LT.lt.ne'` (commanddeclaration)
```lean
theorem ne' [Preorder α] {x y : α} (h : x < y) : y ≠ x
```

## Premise full source (with proof)
### `Finset.image_toFinset` (commanddeclaration) at `Mathlib/Data/Finset/Image.lean`
```lean
theorem image_toFinset [DecidableEq α] {s : Multiset α} :
    s.toFinset.image f = (s.map f).toFinset :=
  ext fun _ => by simp only [mem_image, Multiset.mem_toFinset, exists_prop, Multiset.mem_map]
```

### `Polynomial.roots_expand_map_frobenius` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem roots_expand_map_frobenius : (expand R p f).roots.map (frobenius R p) = p • f.roots := by
  simp [roots_expand, Multiset.map_nsmul]
```

### `Polynomial.roots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
/-- `roots p` noncomputably gives a multiset containing all the roots of `p`,
including their multiplicities. -/
noncomputable def roots (p : R[X]) : Multiset R :=
  haveI := Classical.decEq R
  haveI := Classical.dec (p = 0)
  if h : p = 0 then ∅ else Classical.choose (exists_multiset_roots h)
```

### `Multiset.toFinset_nsmul` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp]
theorem toFinset_nsmul (s : Multiset α) : ∀ n ≠ 0, (n • s).toFinset = s.toFinset
  | 0, h => by contradiction
  | n + 1, _ => by
    by_cases h : n = 0
    · rw [h, zero_add, one_nsmul]
    · rw [add_nsmul, toFinset_add, one_nsmul, toFinset_nsmul s n h, Finset.union_idempotent]
```

### `expChar_pos` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The exponential characteristic is positive. -/
theorem expChar_pos (q : ℕ) [ExpChar R q] : 0 < q := by
  rcases expChar_is_prime_or_one R q with h | rfl
  exacts [Nat.Prime.pos h, Nat.one_pos]

/-- Any power of the exponential characteristic is positive. -/
```

### `LT.lt.ne'` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem ne' [Preorder α] {x y : α} (h : x < y) : y ≠ x :=
  h.ne.symm
```
