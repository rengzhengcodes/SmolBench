## Current goal
```
⊢ (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y)
```

## Full tactic state
```
case refine'_2
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝⁶ : (i : ι) → AddCommMonoid (s i)
inst✝⁵ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁴ : AddCommMonoid M
inst✝³ : Module R M
E : Type u_9
inst✝² : AddCommMonoid E
inst✝¹ : Module R E
F : Type u_10
inst✝ : AddCommMonoid F
φ : MultilinearMap R s E
r : R
x z y : ⨂[R] (i : ι), s i
ihz : (liftAux φ) (r • z) = r • (liftAux φ) z
ihy : (liftAux φ) (r • y) = r • (liftAux φ) y
⊢ (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y)
```

## Proof so far (4 tactics)
```lean
refine' PiTensorProduct.induction_on' x _ _
intro z f
rw [smul_tprodCoeff' r z f, liftAux_tprodCoeff, liftAux_tprodCoeff, smul_assoc]
intro z y ihz ihy
```

## Theorem
`PiTensorProduct.liftAux.smul` in `Mathlib/LinearAlgebra/PiTensorProduct.lean`

## Premises used in the next tactic
- `smul_add`
- `PiTensorProduct.liftAux`
- `AddMonoidHom.map_add`
- `PiTensorProduct.liftAux`
- `AddMonoidHom.map_add`
- `smul_add`

## Premise signatures
### `smul_add` (commanddeclaration)
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂
```

### `PiTensorProduct.liftAux` (commanddeclaration)
```lean
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `PiTensorProduct.liftAux` (commanddeclaration)
```lean
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `smul_add` (commanddeclaration)
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂
```

## Premise full source (with proof)
### `smul_add` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂ :=
  DistribSMul.smul_add _ _ _
```

### `PiTensorProduct.liftAux` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- Auxiliary function to constructing a linear map `(⨂[R] i, s i) → E` given a
`MultilinearMap R s E` with the property that its composition with the canonical
`MultilinearMap R s (⨂[R] i, s i)` is the given multilinear map. -/
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E :=
  liftAddHom (fun p : R × Π i, s i ↦ p.1 • φ p.2)
    (fun z f i hf ↦ by simp_rw [map_coord_zero φ i hf, smul_zero])
    (fun f ↦ by simp_rw [zero_smul])
    (fun z f i m₁ m₂ ↦ by simp_rw [← smul_add, φ.map_add])
    (fun z₁ z₂ f ↦ by rw [← add_smul])
    fun z f i r ↦ by simp [φ.map_smul, smul_smul, mul_comm]
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `PiTensorProduct.liftAux` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- Auxiliary function to constructing a linear map `(⨂[R] i, s i) → E` given a
`MultilinearMap R s E` with the property that its composition with the canonical
`MultilinearMap R s (⨂[R] i, s i)` is the given multilinear map. -/
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E :=
  liftAddHom (fun p : R × Π i, s i ↦ p.1 • φ p.2)
    (fun z f i hf ↦ by simp_rw [map_coord_zero φ i hf, smul_zero])
    (fun f ↦ by simp_rw [zero_smul])
    (fun z f i m₁ m₂ ↦ by simp_rw [← smul_add, φ.map_add])
    (fun z₁ z₂ f ↦ by rw [← add_smul])
    fun z f i r ↦ by simp [φ.map_smul, smul_smul, mul_comm]
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `smul_add` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂ :=
  DistribSMul.smul_add _ _ _
```

## Filler (hint:2 → hint:3 token-match, ≈1033 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaec
