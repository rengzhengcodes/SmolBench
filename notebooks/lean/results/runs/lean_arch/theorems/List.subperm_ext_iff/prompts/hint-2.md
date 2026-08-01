## Current goal
```
⊢ List.diff l₂ l₁ ++ l₁ ~ l₂
```

## Full tactic state
```
α : Type u_1
inst✝ : DecidableEq α
l₁ l₂ : List α
h : ∀ (x : α), x ∈ l₁ → count x l₁ ≤ count x l₂
this : l₁ <+~ List.diff l₂ l₁ ++ l₁
⊢ List.diff l₂ l₁ ++ l₁ ~ l₂
```

## Proof so far (3 tactics)
```lean
refine ⟨fun h x _ => h.count_le x, fun h => ?_⟩
have : l₁ <+~ l₂.diff l₁ ++ l₁ := (subperm_append_right l₁).mpr nil_subperm
refine this.trans (Perm.subperm ?_)
```

## Theorem
`List.subperm_ext_iff` in `.lake/packages/std/Std/Data/List/Perm.lean`

## Premises used in the next tactic
- `List.subperm_append_diff_self_of_count_le`

## Premise signatures
### `List.subperm_append_diff_self_of_count_le` (commanddeclaration)
```lean
theorem subperm_append_diff_self_of_count_le {l₁ l₂ : List α}
    (h : ∀ x ∈ l₁, count x l₁ ≤ count x l₂) : l₁ ++ l₂.diff l₁ ~ l₂
```

## Premise full source (with proof)
### `List.subperm_append_diff_self_of_count_le` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Perm.lean`
```lean
/-- The list version of `add_tsub_cancel_of_le` for multisets. -/
theorem subperm_append_diff_self_of_count_le {l₁ l₂ : List α}
    (h : ∀ x ∈ l₁, count x l₁ ≤ count x l₂) : l₁ ++ l₂.diff l₁ ~ l₂ := by
  induction l₁ generalizing l₂ with
  | nil => simp
  | cons hd tl IH =>
    have : hd ∈ l₂ := by
      rw [← count_pos_iff_mem]
      exact Nat.lt_of_lt_of_le (count_pos_iff_mem.mpr (.head _)) (h hd (.head _))
    have := perm_cons_erase this
    refine Perm.trans ?_ this.symm
    rw [cons_append, diff_cons, perm_cons]
    refine IH fun x hx => ?_
    specialize h x (.tail _ hx)
    rw [perm_iff_count.mp this] at h
    if hx : x = hd then subst hd; simpa [Nat.succ_le_succ_iff] using h
    else simpa [hx] using h

/-- The list version of `Multiset.le_iff_count`. -/
```
