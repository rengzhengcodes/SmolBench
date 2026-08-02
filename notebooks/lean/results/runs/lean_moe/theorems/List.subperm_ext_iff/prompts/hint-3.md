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

## Transitive premise context (1-hop, 10/10 premises, ≈1007 tokens)
### `Lake.Manifest.version` (commanddeclaration) at `.lake/packages/lean4/src/lean/lake/Lake/Load/Manifest.lean`
```lean
/-- Current version of the manifest format. -/
def Manifest.version : Nat := 7

/-- An entry for a package stored in the manifest. -/
```

### `add_tsub_cancel_of_le` (commanddeclaration) at `Mathlib/Algebra/Order/Sub/Canonical.lean`
```lean
@[simp]
theorem add_tsub_cancel_of_le (h : a ≤ b) : a + (b - a) = b := by
  refine' le_antisymm _ le_add_tsub
  obtain ⟨c, rfl⟩ := exists_add_of_le h
  exact add_le_add_left add_tsub_le_left a
```

### `List` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`List α` is the type of ordered lists with elements of type `α`.
It is implemented as a linked list.

`List α` is isomorphic to `Array α`, but they are useful for different things:
* `List α` is easier for reasoning, and
  `Array α` is modeled as a wrapper around `List α`
* `List α` works well as a persistent data structure, when many copies of the
  tail are shared. When the value is not shared, `Array α` will have better
  performance because it can do destructive updates.
-/
inductive List (α : Type u) where
  /-- `[]` is the empty list. -/
  | nil : List α
  /-- If `a : α` and `l : List α`, then `cons a l`, or `a :: l`, is the
  list whose first element is `a` and with `l` as the rest of the list. -/
  | cons (head : α) (tail : List α) : List α
```

### `List.count_pos_iff_mem` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Count.lean`
```lean
theorem count_pos_iff_mem {a : α} {l : List α} : 0 < count a l ↔ a ∈ l := by
  simp only [count, countP_pos, beq_iff_eq, exists_eq_right]
```

### `Nat.lt_of_lt_of_le` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem lt_of_lt_of_le {n m k : Nat} : n < m → m ≤ k → n < k :=
  Nat.le_trans
```

### `List.perm_cons_erase` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Perm.lean`
```lean
theorem perm_cons_erase [DecidableEq α] {a : α} {l : List α} (h : a ∈ l) : l ~ a :: l.erase a :=
  let ⟨_l₁, _l₂, _, e₁, e₂⟩ := exists_erase_eq h
  e₂ ▸ e₁ ▸ perm_middle
```

### `List.diff_cons` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
@[simp] theorem diff_cons (l₁ l₂ : List α) (a : α) : l₁.diff (a :: l₂) = (l₁.erase a).diff l₂ := by
  simp_all [List.diff, erase_of_not_mem]
```

### `List.perm_cons` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Perm.lean`
```lean
@[simp] theorem perm_cons (a : α) {l₁ l₂ : List α} : a :: l₁ ~ a :: l₂ ↔ l₁ ~ l₂ :=
  ⟨.cons_inv, .cons a⟩
```

### `Nat.succ_le_succ_iff` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
theorem succ_le_succ_iff : succ a ≤ succ b ↔ a ≤ b := ⟨le_of_succ_le_succ, succ_le_succ⟩
```

### `Multiset.le_iff_count` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
theorem le_iff_count {s t : Multiset α} : s ≤ t ↔ ∀ a, count a s ≤ count a t :=
  ⟨fun h a => count_le_of_le a h, fun al => by
    rw [← (ext.2 fun a => by simp [max_eq_right (al a)] : s ∪ t = t)]; apply le_union_left⟩
```
