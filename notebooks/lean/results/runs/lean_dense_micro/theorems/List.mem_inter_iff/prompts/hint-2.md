## Current goal
```
⊢ x ∈ l₁ ∩ l₂ ↔ x ∈ l₁ ∧ x ∈ l₂
```

## Full tactic state
```
α : Type u_1
x✝ : DecidableEq α
x : α
l₁ l₂ : List α
⊢ x ∈ l₁ ∩ l₂ ↔ x ∈ l₁ ∧ x ∈ l₂
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`List.mem_inter_iff` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.inter_def`
- `List.mem_filter`

## Premise signatures
### `List.inter_def` (commanddeclaration)
```lean
theorem inter_def [DecidableEq α] (l₁ l₂ : List α)  : l₁ ∩ l₂ = filter (· ∈ l₂) l₁
```

### `List.mem_filter` (commanddeclaration)
```lean
theorem mem_filter : x ∈ filter p as ↔ x ∈ as ∧ p x
```

## Premise full source (with proof)
### `List.inter_def` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem inter_def [DecidableEq α] (l₁ l₂ : List α)  : l₁ ∩ l₂ = filter (· ∈ l₂) l₁ := rfl
```

### `List.mem_filter` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Lemmas.lean`
```lean
theorem mem_filter : x ∈ filter p as ↔ x ∈ as ∧ p x := by
  induction as with
  | nil => simp [filter]
  | cons a as ih =>
    by_cases h : p a <;> simp [*, or_and_right]
    · exact or_congr_left (and_iff_left_of_imp fun | rfl => h).symm
    · exact (or_iff_right fun ⟨rfl, h'⟩ => h h').symm
```
