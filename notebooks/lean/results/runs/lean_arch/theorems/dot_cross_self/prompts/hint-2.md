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
