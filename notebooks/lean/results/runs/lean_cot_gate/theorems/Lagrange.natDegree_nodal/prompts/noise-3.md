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

## Filler (hint:2 → hint:3 token-match, ≈917 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
