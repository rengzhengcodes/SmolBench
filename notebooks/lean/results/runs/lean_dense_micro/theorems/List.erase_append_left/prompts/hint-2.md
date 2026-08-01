## Current goal
```
⊢ eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂
```

## Full tactic state
```
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
h : a ∈ l₁
⊢ eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂
```

## Proof so far (1 tactic)
```lean
simp [erase_eq_eraseP]
```

## Theorem
`List.erase_append_left` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.eraseP_append_left`
- `beq_self_eq_true`

## Premise signatures
### `List.eraseP_append_left` (commanddeclaration)
```lean
theorem eraseP_append_left {a : α} (pa : p a) :
    ∀ {l₁ : List α} l₂, a ∈ l₁ → (l₁++l₂).eraseP p = l₁.eraseP p ++ l₂
```

### `beq_self_eq_true` (commanddeclaration)
```lean
@[simp] theorem beq_self_eq_true [BEq α] [LawfulBEq α] (a : α) : (a == a) = true
```

## Premise full source (with proof)
### `List.eraseP_append_left` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem eraseP_append_left {a : α} (pa : p a) :
    ∀ {l₁ : List α} l₂, a ∈ l₁ → (l₁++l₂).eraseP p = l₁.eraseP p ++ l₂
  | x :: xs, l₂, h => by
    by_cases h' : p x <;> simp [h']
    rw [eraseP_append_left pa l₂ ((mem_cons.1 h).resolve_left (mt _ h'))]
    intro | rfl => exact pa
```

### `beq_self_eq_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem beq_self_eq_true [BEq α] [LawfulBEq α] (a : α) : (a == a) = true := LawfulBEq.rfl
```
