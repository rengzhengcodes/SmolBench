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

## Transitive premise context (1-hop, 8/8 premises, ≈831 tokens)
### `DecidableEq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Asserts that `α` has decidable equality, that is, `a = b` is decidable
for all `a b : α`. See `Decidable`.
-/
abbrev DecidableEq (α : Sort u) :=
  (a b : α) → Decidable (Eq a b)

/-- Proves that `a = b` is decidable given `DecidableEq α`. -/
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

### `by_cases` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem by_cases {q : Prop} (hpq : p → q) (hnpq : ¬p → q) : q :=
if hp : p then hpq hp else hnpq hp
```

### `or_and_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
/-- `∧` distributes over `∨` (on the right). -/
theorem or_and_right : (a ∨ b) ∧ c ↔ (a ∧ c) ∨ (b ∧ c) := by rw [@and_comm (a ∨ b), and_or_left, @and_comm c, @and_comm c]

/-- `∨` distributes over `∧` (on the left). -/
```

### `or_congr_left` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem or_congr_left (h : a ↔ b) : a ∨ c ↔ b ∨ c := or_congr h .rfl
```

### `and_iff_left_of_imp` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
theorem and_iff_left_of_imp  (h : a → b) : (a ∧ b) ↔ a := Iff.intro And.left (fun ha => And.intro ha (h ha))
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `or_iff_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem or_iff_right (ha : ¬a) : a ∨ b ↔ b := or_iff_right_iff_imp.mpr ha.elim

/-! ## distributivity -/
```
