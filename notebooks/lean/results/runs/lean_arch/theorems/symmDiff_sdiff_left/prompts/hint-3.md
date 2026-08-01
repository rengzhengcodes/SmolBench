## Current goal
```
⊢ a ∆ b \ a = b \ a
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
⊢ a ∆ b \ a = b \ a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`symmDiff_sdiff_left` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `symmDiff_def`
- `sup_sdiff`
- `sdiff_idem`
- `sdiff_sdiff_self`
- `bot_sup_eq`

## Premise signatures
### `symmDiff_def` (commanddeclaration)
```lean
theorem symmDiff_def [Sup α] [SDiff α] (a b : α) : a ∆ b = a \ b ⊔ b \ a
```

### `sup_sdiff` (commanddeclaration)
```lean
theorem sup_sdiff : (a ⊔ b) \ c = a \ c ⊔ b \ c
```

### `sdiff_idem` (commanddeclaration)
```lean
@[simp]
theorem sdiff_idem : (a \ b) \ b = a \ b
```

### `sdiff_sdiff_self` (commanddeclaration)
```lean
@[simp]
theorem sdiff_sdiff_self : (a \ b) \ a = ⊥
```

### `bot_sup_eq` (commanddeclaration)
```lean
theorem bot_sup_eq (a : α) : ⊥ ⊔ a = a
```

## Premise full source (with proof)
### `symmDiff_def` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_def [Sup α] [SDiff α] (a b : α) : a ∆ b = a \ b ⊔ b \ a :=
  rfl
```

### `sup_sdiff` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sup_sdiff : (a ⊔ b) \ c = a \ c ⊔ b \ c :=
  sup_sdiff_distrib _ _ _
```

### `sdiff_idem` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sdiff_idem : (a \ b) \ b = a \ b := by rw [sdiff_sdiff_left, sup_idem]
```

### `sdiff_sdiff_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sdiff_sdiff_self : (a \ b) \ a = ⊥ := by rw [sdiff_sdiff_comm, sdiff_self, bot_sdiff]
```

### `bot_sup_eq` (commanddeclaration) at `Mathlib/Order/BoundedOrder.lean`
```lean
theorem bot_sup_eq (a : α) : ⊥ ⊔ a = a :=
  sup_of_le_right bot_le
```

## Transitive premise context (1-hop, 10/10 premises, ≈890 tokens)
### `Sup` (commanddeclaration) at `Mathlib/Order/Notation.lean`
```lean
/-- Typeclass for the `⊔` (`\lub`) notation -/
@[notation_class, ext]
class Sup (α : Type*) where
  /-- Least upper bound (`\lub` notation) -/
  sup : α → α → α
```

### `SDiff` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/-- Notation type class for the set difference `\`. -/
class SDiff (α : Type u) where
  /--
  `a \ b` is the set difference of `a` and `b`,
  consisting of all elements in `a` that are not in `b`.
  -/
  sdiff : α → α → α

/-- Subset relation: `a ⊆ b`  -/
infix:50 " ⊆ " => Subset

/-- Strict subset relation: `a ⊂ b`  -/
infix:50 " ⊂ " => SSubset

/-- Superset relation: `a ⊇ b`  -/
infix:50 " ⊇ " => Superset

/-- Strict superset relation: `a ⊃ b`  -/
infix:50 " ⊃ " => SSuperset

/-- `a ∪ b` is the union of`a` and `b`. -/
infixl:65 " ∪ " => Union.union

/-- `a ∩ b` is the intersection of`a` and `b`. -/
infixl:70 " ∩ " => Inter.inter

/--
`a \ b` is the set difference of `a` and `b`,
consisting of all elements in `a` that are not in `b`.
-/
infix:70 " \\ " => SDiff.sdiff

/-! # collections  -/

/-- `EmptyCollection α` is the typeclass which supports the notation `∅`, also written as `{}`. -/
```

### `sup_sdiff_distrib` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sup_sdiff_distrib (a b c : α) : (a ⊔ b) \ c = a \ c ⊔ b \ c :=
  eq_of_forall_ge_iff fun d => by simp_rw [sdiff_le_iff, sup_le_iff, sdiff_le_iff]
```

### `sdiff_sdiff_left` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sdiff_sdiff_left : (a \ b) \ c = a \ (b ⊔ c) :=
  sdiff_sdiff _ _ _
```

### `sup_idem` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem sup_idem (a : α) : a ⊔ a = a := by simp
```

### `sdiff_sdiff_comm` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sdiff_sdiff_comm : (a \ b) \ c = (a \ c) \ b :=
  sdiff_right_comm _ _ _
```

### `sdiff_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sdiff_self : a \ a = ⊥ :=
  le_bot_iff.1 <| sdiff_le_iff.2 le_sup_left
```

### `bot_sdiff` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem bot_sdiff : ⊥ \ a = ⊥ :=
  sdiff_eq_bot_iff.2 bot_le
```

### `sup_of_le_right` (stdtacticaliasaliaslr) at `Mathlib/Order/Lattice.lean`
```lean
alias ⟨le_of_sup_eq, sup_of_le_right⟩ := sup_eq_right
```

### `bot_le` (commanddeclaration) at `Mathlib/Order/BoundedOrder.lean`
```lean
@[simp]
theorem bot_le : ⊥ ≤ a :=
  OrderBot.bot_le a
```
