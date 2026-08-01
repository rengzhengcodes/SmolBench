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

## Transitive premise context (1-hop, 6/6 premises, ≈849 tokens)
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

### `Or.resolve_left` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
theorem Or.resolve_left  (h: Or a b) (na : Not a) : b := h.elim (absurd · na) id
```

### `mt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem mt {a b : Prop} (h₁ : a → b) (h₂ : ¬b) : ¬a :=
  fun ha => h₂ (h₁ ha)
```

### `BEq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`BEq α` is a typeclass for supplying a boolean-valued equality relation on
`α`, notated as `a == b`. Unlike `DecidableEq α` (which uses `a = b`), this
is `Bool` valued instead of `Prop` valued, and it also does not have any
axioms like being reflexive or agreeing with `=`. It is mainly intended for
programming applications. See `LawfulBEq` for a version that requires that
`==` and `=` coincide.
-/
class BEq (α : Type u) where
  /-- Boolean equality, notated as `a == b`. -/
  beq : α → α → Bool
```

### `LawfulBEq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`LawfulBEq α` is a typeclass which asserts that the `BEq α` implementation
(which supplies the `a == b` notation) coincides with logical equality `a = b`.
In other words, `a == b` implies `a = b`, and `a == a` is true.
-/
class LawfulBEq (α : Type u) [BEq α] : Prop where
  /-- If `a == b` evaluates to `true`, then `a` and `b` are equal in the logic. -/
  eq_of_beq : {a b : α} → a == b → a = b
  /-- `==` is reflexive, that is, `(a == a) = true`. -/
  protected rfl : {a : α} → a == a

export LawfulBEq (eq_of_beq)
```
