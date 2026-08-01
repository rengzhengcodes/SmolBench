## Current goal
```
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```

## Full tactic state
```
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
h : l₁ <+ l₂
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```

## Proof so far (1 tactic)
```lean
simp [erase_eq_eraseP]
```

## Theorem
`List.Sublist.erase` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.Sublist.eraseP`

## Premise signatures
### `List.Sublist.eraseP` (commanddeclaration)
```lean
theorem Sublist.eraseP : l₁ <+ l₂ → l₁.eraseP p <+ l₂.eraseP p
```

## Premise full source (with proof)
### `List.Sublist.eraseP` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem Sublist.eraseP : l₁ <+ l₂ → l₁.eraseP p <+ l₂.eraseP p
  | .slnil => Sublist.refl _
  | .cons a s => by
    by_cases h : p a <;> simp [h]
    exacts [s.eraseP.trans (eraseP_sublist _), s.eraseP.cons _]
  | .cons₂ a s => by
    by_cases h : p a <;> simp [h]
    exacts [s, s.eraseP.cons₂ _]
```

## Transitive premise context (1-hop, 2/2 premises, ≈186 tokens)
### `by_cases` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem by_cases {q : Prop} (hpq : p → q) (hnpq : ¬p → q) : q :=
if hp : p then hpq hp else hnpq hp
```

### `List.eraseP_sublist` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem eraseP_sublist (l : List α) : l.eraseP p <+ l := by
  match exists_or_eq_self_of_eraseP p l with
  | .inl h => rw [h]; apply Sublist.refl
  | .inr ⟨c, l₁, l₂, _, _, h₃, h₄⟩ => rw [h₄, h₃]; simp
```
