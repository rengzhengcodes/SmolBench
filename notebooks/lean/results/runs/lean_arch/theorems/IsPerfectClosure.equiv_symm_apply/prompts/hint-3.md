## Current goal
```
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
inst✝⁹ : CommRing M
inst✝⁸ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁷ : ExpChar K p
inst✝⁶ : ExpChar L p
inst✝⁵ : ExpChar M p
inst✝⁴ : ExpChar N p
inst✝³ : PerfectRing L p
inst✝² : IsPerfectClosure i p
inst✝¹ : PerfectRing M p
inst✝ : IsPerfectClosure j p
x : M
n : ℕ
y : K
h : j y = x ^ p ^ n
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`IsPerfectClosure.equiv_symm_apply` in `Mathlib/FieldTheory/IsPerfectClosure.lean`

## Premises used in the next tactic
- `IsPerfectClosure.equiv_symm`
- `IsPerfectClosure.equiv_apply`

## Premise signatures
### `IsPerfectClosure.equiv_symm` (commanddeclaration)
```lean
@[simp]
theorem equiv_symm : (equiv i j p).symm = equiv j i p
```

### `IsPerfectClosure.equiv_apply` (commanddeclaration)
```lean
theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y)
```

## Premise full source (with proof)
### `IsPerfectClosure.equiv_symm` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
@[simp]
theorem equiv_symm : (equiv i j p).symm = equiv j i p := rfl
```

### `IsPerfectClosure.equiv_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y) :=
  PerfectRing.liftAux_apply i j p _ _ _ h
```

## Transitive premise context (1-hop, 3/3 premises, ≈693 tokens)
### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `iterateFrobeniusEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
/-- The iterated Frobenius automorphism for a perfect ring. -/
@[simps! apply]
noncomputable def iterateFrobeniusEquiv : R ≃+* R :=
  RingEquiv.ofBijective (iterateFrobenius R p n) (bijective_iterateFrobenius R p n)
```

### `PerfectRing.liftAux_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
/-- If `i : K →+* L` and `j : K →+* M` are ring homomorphisms of characteristic `p` rings, such that
`i` is `p`-radical, and `M` is a perfect ring, then `PerfectRing.liftAux` is well-defined. -/
theorem liftAux_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    liftAux i j p x = (iterateFrobeniusEquiv M p n).symm (j y) := by
  rw [liftAux]
  have h' := Classical.choose_spec (lift_aux i p x)
  set n' := (Classical.choose (lift_aux i p x)).1
  replace h := congr($(h.symm) ^ p ^ n')
  rw [← pow_mul, mul_comm, pow_mul, ← h', ← map_pow, ← map_pow, ← sub_eq_zero, ← map_sub,
    ← RingHom.mem_ker] at h
  obtain ⟨m, h⟩ := mem_pNilradical.1 (IsPRadical.ker_le i p h)
  refine (iterateFrobeniusEquiv M p (m + n + n')).injective ?_
  conv_lhs => rw [iterateFrobeniusEquiv_add_apply, RingEquiv.apply_symm_apply]
  rw [add_assoc, add_comm n n', ← add_assoc,
    iterateFrobeniusEquiv_add_apply (m := m + n'), RingEquiv.apply_symm_apply,
    iterateFrobeniusEquiv_def, iterateFrobeniusEquiv_def,
    ← sub_eq_zero, ← map_pow, ← map_pow, ← map_sub,
    add_comm m, add_comm m, pow_add, pow_mul, pow_add, pow_mul, ← sub_pow_expChar_pow, h, map_zero]

/-- If `i : K →+* L` and `j : K →+* M` are ring homomorphisms of characteristic `p` rings, such that
`i` is `p`-radical, and `M` is a perfect ring, then `PerfectRing.liftAux`
is a ring homomorphism. This is similar to `IsAlgClosed.lift` and `IsSepClosed.lift`. -/
```
