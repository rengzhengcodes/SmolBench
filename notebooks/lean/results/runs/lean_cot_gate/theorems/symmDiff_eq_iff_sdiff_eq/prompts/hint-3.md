## Current goal
```
⊢ a ∆ b = c ↔ a ∆ c = b
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
ha : a ≤ c
⊢ a ∆ b = c ↔ a ∆ c = b
```

## Proof so far (1 tactic)
```lean
rw [← symmDiff_of_le ha]
```

## Theorem
`symmDiff_eq_iff_sdiff_eq` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `symmDiff_right_involutive`
- `Function.Involutive.toPerm`
- `eq_comm`

## Premise signatures
### `symmDiff_right_involutive` (commanddeclaration)
```lean
theorem symmDiff_right_involutive (a : α) : Involutive (a ∆ ·)
```

### `Function.Involutive.toPerm` (commanddeclaration)
```lean
def toPerm (f : α → α) (h : Involutive f) : Equiv.Perm α
```

### `eq_comm` (commanddeclaration)
```lean
theorem eq_comm {a b : α} : a = b ↔ b = a
```

## Premise full source (with proof)
### `symmDiff_right_involutive` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_right_involutive (a : α) : Involutive (a ∆ ·) :=
  symmDiff_symmDiff_cancel_left _
```

### `Function.Involutive.toPerm` (commanddeclaration) at `Mathlib/Logic/Equiv/Basic.lean`
```lean
/-- Convert an involutive function `f` to a permutation with `toFun = invFun = f`. -/
def toPerm (f : α → α) (h : Involutive f) : Equiv.Perm α :=
  ⟨f, f, h.leftInverse, h.rightInverse⟩
```

### `eq_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_comm {a b : α} : a = b ↔ b = a := Eq.comm
```

## Transitive premise context (1-hop, 5/5 premises, ≈341 tokens)
### `Function.Involutive` (commanddeclaration) at `Mathlib/Logic/Function/Basic.lean`
```lean
/-- A function is involutive, if `f ∘ f = id`. -/
def Involutive {α} (f : α → α) : Prop :=
  ∀ x, f (f x) = x
```

### `symmDiff_symmDiff_cancel_left` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
@[simp]
theorem symmDiff_symmDiff_cancel_left : a ∆ (a ∆ b) = b := by simp [← symmDiff_assoc]
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `Equiv.Perm` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
/-- `Perm α` is the type of bijections from `α` to itself. -/
@[reducible]
def Equiv.Perm (α : Sort*) :=
  Equiv α α
```

### `Eq.comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem Eq.comm {a b : α} : a = b ↔ b = a := Iff.intro Eq.symm Eq.symm
```
