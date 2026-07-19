## Current goal
```
⊢ w ⬝ᵥ (crossProduct v) w = 0
```

## Full tactic state
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w ⬝ᵥ (crossProduct v) w = 0
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`dot_cross_self` in `Mathlib/LinearAlgebra/CrossProduct.lean`

## Premises used in the next tactic
- `cross_anticomm`
- `Matrix.dotProduct_neg`
- `dot_self_cross`
- `neg_zero`

## Premise signatures
### `cross_anticomm` (commanddeclaration)
```lean
@[simp]
theorem cross_anticomm (v w : Fin 3 → R) : -(v ×₃ w) = w ×₃ v
```

### `Matrix.dotProduct_neg` (commanddeclaration)
```lean
@[simp]
theorem dotProduct_neg : v ⬝ᵥ -w = -(v ⬝ᵥ w)
```

### `dot_self_cross` (commanddeclaration)
```lean
@[simp 1100] theorem dot_self_cross (v w : Fin 3 → R) : v ⬝ᵥ v ×₃ w = 0
```

### `neg_zero`
_(not found in premise corpus)_

## Premise full source (with proof)
### `cross_anticomm` (commanddeclaration) at `Mathlib/LinearAlgebra/CrossProduct.lean`
```lean
@[simp]
theorem cross_anticomm (v w : Fin 3 → R) : -(v ×₃ w) = w ×₃ v := by
  simp [cross_apply, mul_comm]
```

### `Matrix.dotProduct_neg` (commanddeclaration) at `Mathlib/Data/Matrix/Basic.lean`
```lean
@[simp]
theorem dotProduct_neg : v ⬝ᵥ -w = -(v ⬝ᵥ w) := by simp [dotProduct]
```

### `dot_self_cross` (commanddeclaration) at `Mathlib/LinearAlgebra/CrossProduct.lean`
```lean
/-- The cross product of two vectors is perpendicular to the first vector. -/
@[simp 1100] -- Porting note: increase priority so that the LHS doesn't simplify
theorem dot_self_cross (v w : Fin 3 → R) : v ⬝ᵥ v ×₃ w = 0 := by
  rw [cross_apply, vec3_dotProduct]
  set_option tactic.skipAssignedInstances false in norm_num
  ring
```

### `neg_zero`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 8/8 premises, ≈838 tokens)
### `Fin` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Fin n` is a natural number `i` with the constraint that `0 ≤ i < n`.
It is the "canonical type with `n` elements".
-/
structure Fin (n : Nat) where
  /-- If `i : Fin n`, then `i.val : ℕ` is the described number. It can also be
  written as `i.1` or just `i` when the target type is known. -/
  val  : Nat
  /-- If `i : Fin n`, then `i.2` is a proof that `i.1 < n`. -/
  isLt : LT.lt val n
```

### `cross_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/CrossProduct.lean`
```lean
theorem cross_apply (a b : Fin 3 → R) :
    a ×₃ b = ![a 1 * b 2 - a 2 * b 1, a 2 * b 0 - a 0 * b 2, a 0 * b 1 - a 1 * b 0] := rfl
```

### `mul_comm` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive]
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm
```

### `Matrix.dotProduct` (commanddeclaration) at `Mathlib/Data/Matrix/Basic.lean`
```lean
/-- `dotProduct v w` is the sum of the entrywise products `v i * w i` -/
def dotProduct [Mul α] [AddCommMonoid α] (v w : m → α) : α :=
  ∑ i, v i * w i
```

### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `Aesop.Goal.priority` (commanddeclaration) at `.lake/packages/aesop/Aesop/Tree/Data.lean`
```lean
def priority (g : Goal) : Percent :=
  g.successProbability * unificationGoalPenalty ^ g.mvars.size
```

### `LieAlgebra.Orthogonal.so` (commanddeclaration) at `Mathlib/Algebra/Lie/Classical.lean`
```lean
/-- The definite orthogonal Lie subalgebra: skew-adjoint matrices with respect to the symmetric
bilinear form defined by the identity matrix. -/
def so [Fintype n] : LieSubalgebra R (Matrix n n R) :=
  skewAdjointMatricesLieSubalgebra (1 : Matrix n n R)
```

### `Matrix.vec3_dotProduct` (commanddeclaration) at `Mathlib/Data/Matrix/Notation.lean`
```lean
@[simp]
theorem vec3_dotProduct (v w : Fin 3 → α) : v ⬝ᵥ w = v 0 * w 0 + v 1 * w 1 + v 2 * w 2 :=
  vec3_dotProduct'
```
