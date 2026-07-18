## Current goal
```
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
inst✝ : LocallyFiniteOrderTop α
a : Subtype p
hp : ∀ ⦃a x : α⦄, a ≤ x → p a → p x
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```

## Proof so far (1 tactic)
```lean
rw [subtype_Ioi_eq]
```

## Theorem
`Finset.map_subtype_embedding_Ioi` in `Mathlib/Order/LocallyFinite.lean`

## Premises used in the next tactic
- `Finset.subtype_map_of_mem`
- `Finset.mem_Ioi`
- `LT.lt.le`

## Premise signatures
### `Finset.subtype_map_of_mem` (commanddeclaration)
```lean
theorem subtype_map_of_mem {p : α → Prop} [DecidablePred p] {s : Finset α} (h : ∀ x ∈ s, p x) :
    (s.subtype p).map (Embedding.subtype _) = s
```

### `Finset.mem_Ioi` (commanddeclaration)
```lean
@[simp]
theorem mem_Ioi : x ∈ Ioi a ↔ a < x
```

### `LT.lt.le` (stdtacticaliasalias)
```lean
alias LT.lt.le
```

## Premise full source (with proof)
### `Finset.subtype_map_of_mem` (commanddeclaration) at `Mathlib/Data/Finset/Image.lean`
```lean
/-- If all elements of a `Finset` satisfy the predicate `p`,
`s.subtype p` converts back to `s` with `Embedding.subtype`. -/
theorem subtype_map_of_mem {p : α → Prop} [DecidablePred p] {s : Finset α} (h : ∀ x ∈ s, p x) :
    (s.subtype p).map (Embedding.subtype _) = s := ext <| by simpa [subtype_map] using h
```

### `Finset.mem_Ioi` (commanddeclaration) at `Mathlib/Order/LocallyFinite.lean`
```lean
@[simp]
theorem mem_Ioi : x ∈ Ioi a ↔ a < x :=
  LocallyFiniteOrderTop.finset_mem_Ioi _ _
```

### `LT.lt.le` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.le := le_of_lt

alias LT.lt.trans := lt_trans

alias LT.lt.trans' := lt_trans'

alias LT.lt.trans_le := lt_of_lt_of_le

alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```

## Transitive premise context (1-hop, 14/14 premises, ≈1060 tokens)
### `Finset` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
/-- `Finset α` is the type of finite sets of elements of `α`. It is implemented
  as a multiset (a list up to permutation) which has no duplicate elements. -/
structure Finset (α : Type*) where
  /-- The underlying multiset -/
  val : Multiset α
  /-- `val` contains no duplicates -/
  nodup : Nodup val
```

### `Lean.Parsec.satisfy` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Parsec.lean`
```lean
@[inline]
def satisfy (p : Char → Bool) : Parsec Char := attempt do
  let c ← anyChar
  if p c then return c else fail "condition not satisfied"
```

### `DecidablePred` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/-- A decidable predicate. See `Decidable`. -/
abbrev DecidablePred {α : Sort u} (r : α → Prop) :=
  (a : α) → Decidable (r a)

/-- A decidable relation. See `Decidable`. -/
```

### `le_of_lt` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem le_of_lt : ∀ {a b : α}, a < b → a ≤ b
  | _a, _b, hab => (le_not_le_of_lt hab).left
```

### `LT.lt.trans` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.trans := lt_trans

alias LT.lt.trans' := lt_trans'

alias LT.lt.trans_le := lt_of_lt_of_le

alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```

### `lt_trans` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
@[trans]
theorem lt_trans : ∀ {a b c : α}, a < b → b < c → a < c
  | _a, _b, _c, hab, hbc =>
    match le_not_le_of_lt hab, le_not_le_of_lt hbc with
    | ⟨hab, _hba⟩, ⟨hbc, hcb⟩ =>
      lt_of_le_not_le (le_trans hab hbc) fun hca => hcb (le_trans hca hab)
```

### `LT.lt.trans'` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.trans' := lt_trans'

alias LT.lt.trans_le := lt_of_lt_of_le

alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```

### `lt_trans'` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem lt_trans' : b < c → a < b → a < c :=
  flip lt_trans
```

### `LT.lt.trans_le` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.trans_le := lt_of_lt_of_le

alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```

### `lt_of_lt_of_le` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
@[trans]
theorem lt_of_lt_of_le : ∀ {a b c : α}, a < b → b ≤ c → a < c
  | _a, _b, _c, hab, hbc =>
    let ⟨hab, hba⟩ := le_not_le_of_lt hab
    lt_of_le_not_le (le_trans hab hbc) fun hca => hba (le_trans hbc hca)
```

### `LT.lt.trans_le'` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.trans_le' := lt_of_lt_of_le'

alias LT.lt.ne := ne_of_lt
```

### `lt_of_lt_of_le'` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem lt_of_lt_of_le' : b < c → a ≤ b → a < c :=
  flip lt_of_le_of_lt
```

### `LT.lt.ne` (stdtacticaliasalias) at `Mathlib/Order/Basic.lean`
```lean
alias LT.lt.ne := ne_of_lt
```

### `ne_of_lt` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem ne_of_lt {a b : α} (h : a < b) : a ≠ b := fun he => absurd h (he ▸ lt_irrefl a)
```
