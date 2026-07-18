## Current goal
```
⊢ natDegree (nodal s v) = s.card
```

## Full tactic state
```
R : Type u_1
inst✝¹ : CommRing R
ι : Type u_2
s : Finset ι
v : ι → R
inst✝ : Nontrivial R
⊢ natDegree (nodal s v) = s.card
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Lagrange.natDegree_nodal` in `Mathlib/LinearAlgebra/Lagrange.lean`

## Premises used in the next tactic
- `Lagrange.nodal`
- `Polynomial.natDegree_prod_of_monic`
- `Polynomial.monic_X_sub_C`
- `Polynomial.natDegree_X_sub_C`
- `Finset.sum_const`
- `smul_eq_mul`
- `mul_one`

## Premise signatures
### `Lagrange.nodal` (commanddeclaration)
```lean
def nodal (s : Finset ι) (v : ι → R) : R[X]
```

### `Polynomial.natDegree_prod_of_monic` (commanddeclaration)
```lean
theorem natDegree_prod_of_monic (h : ∀ i ∈ s, (f i).Monic) :
    (∏ i in s, f i).natDegree = ∑ i in s, (f i).natDegree
```

### `Polynomial.monic_X_sub_C` (commanddeclaration)
```lean
theorem monic_X_sub_C (x : R) : Monic (X - C x)
```

### `Polynomial.natDegree_X_sub_C` (commanddeclaration)
```lean
theorem natDegree_X_sub_C (x : R) : (X - C x).natDegree = 1
```

### `Finset.sum_const`
_(not found in premise corpus)_

### `smul_eq_mul` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem smul_eq_mul (α : Type*) [Mul α] {a a' : α} : a • a' = a * a'
```

### `mul_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem mul_one : ∀ a : M, a * 1 = a
```

## Premise full source (with proof)
### `Lagrange.nodal` (commanddeclaration) at `Mathlib/LinearAlgebra/Lagrange.lean`
```lean
/-- `nodal s v` is the unique monic polynomial whose roots are the nodes defined by `v` and `s`.

That is, the roots of `nodal s v` are exactly the image of `v` on `s`,
with appropriate multiplicity.

We can use `nodal` to define the barycentric forms of the evaluated interpolant.
-/

def nodal (s : Finset ι) (v : ι → R) : R[X] :=
  ∏ i in s, (X - C (v i))
```

### `Polynomial.natDegree_prod_of_monic` (commanddeclaration) at `Mathlib/Algebra/Polynomial/BigOperators.lean`
```lean
theorem natDegree_prod_of_monic (h : ∀ i ∈ s, (f i).Monic) :
    (∏ i in s, f i).natDegree = ∑ i in s, (f i).natDegree := by
  simpa using natDegree_multiset_prod_of_monic (s.1.map f) (by simpa using h)
```

### `Polynomial.monic_X_sub_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Monic.lean`
```lean
theorem monic_X_sub_C (x : R) : Monic (X - C x) := by
  simpa only [sub_eq_add_neg, C_neg] using monic_X_add_C (-x)
```

### `Polynomial.natDegree_X_sub_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
theorem natDegree_X_sub_C (x : R) : (X - C x).natDegree = 1 := by
  rw [natDegree_sub_C, natDegree_X]
```

### `Finset.sum_const`
_(not found in premise corpus)_

### `smul_eq_mul` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem smul_eq_mul (α : Type*) [Mul α] {a a' : α} : a • a' = a * a' :=
  rfl
```

### `mul_one` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem mul_one : ∀ a : M, a * 1 = a :=
  MulOneClass.mul_one
```

## Transitive premise context (1-hop, 9/9 premises, ≈888 tokens)
### `Finset` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
/-- `Finset α` is the type of finite sets of elements of `α`. It is implemented
  as a multiset (a list up to permutation) which has no duplicate elements. -/
structure Finset (α : Type*) where
  /-- The underlying multiset -/
  val : Multiset α
  /-- `val` contains no duplicates -/
  nodup : Nodup val
```

### `Polynomial.Monic` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
/-- a polynomial is `Monic` if its leading coefficient is 1 -/
def Monic (p : R[X]) :=
  leadingCoeff p = (1 : R)
```

### `Polynomial.natDegree` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
/-- `natDegree p` forces `degree p` to ℕ, by defining `natDegree 0 = 0`. -/
def natDegree (p : R[X]) : ℕ :=
  (degree p).unbot' 0
```

### `Polynomial.natDegree_multiset_prod_of_monic` (commanddeclaration) at `Mathlib/Algebra/Polynomial/BigOperators.lean`
```lean
theorem natDegree_multiset_prod_of_monic (h : ∀ f ∈ t, Monic f) :
    t.prod.natDegree = (t.map natDegree).sum := by
  nontriviality R
  apply natDegree_multiset_prod'
  suffices (t.map fun f => leadingCoeff f).prod = 1 by
    rw [this]
    simp
  convert prod_replicate (Multiset.card t) (1 : R)
  · simp only [eq_replicate, Multiset.card_map, eq_self_iff_true, true_and_iff]
    rintro i hi
    obtain ⟨i, hi, rfl⟩ := Multiset.mem_map.mp hi
    apply h
    assumption
  · simp
```

### `Polynomial.monic_X_add_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Monic.lean`
```lean
theorem monic_X_add_C (x : R) : Monic (X + C x) :=
  pow_one (X : R[X]) ▸ monic_X_pow_add_C x one_ne_zero
```

### `Polynomial.natDegree_sub_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
@[simp]
theorem natDegree_sub_C {a : R} : natDegree (p - C a) = natDegree p := by
  rw [sub_eq_add_neg, ← C_neg, natDegree_add_C]
```

### `Polynomial.natDegree_X` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
@[simp]
theorem natDegree_X : (X : R[X]).natDegree = 1 :=
  natDegree_eq_of_degree_eq_some degree_X
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `Mul` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/-- The homogeneous version of `HMul`: `a * b : α` where `a b : α`. -/
class Mul (α : Type u) where
  /-- `a * b` computes the product of `a` and `b`. See `HMul`. -/
  mul : α → α → α

/--
The notation typeclass for negation.
This enables the notation `-a : α` where `a : α`.
-/
```
