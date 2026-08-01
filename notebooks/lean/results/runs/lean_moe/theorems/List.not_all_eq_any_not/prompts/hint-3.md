## Current goal
```
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```

## Full tactic state
```
case cons
α : Type u_1
p : α → Bool
head✝ : α
tail✝ : List α
ih : (!all tail✝ p) = any tail✝ fun a => !p a
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```

## Proof so far (1 tactic)
```lean
induction l with simp | cons _ _ ih => rw [Bool.not_and, ih]
```

## Theorem
`List.not_all_eq_any_not` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `Bool.not_and`

## Premise signatures
### `Bool.not_and` (commanddeclaration)
```lean
theorem not_and : ∀ (x y : Bool), (!(x && y)) = (!x || !y)
```

## Premise full source (with proof)
### `Bool.not_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Bool.lean`
```lean
/-- De Morgan's law for boolean and -/
theorem not_and : ∀ (x y : Bool), (!(x && y)) = (!x || !y) := by decide
```

## Transitive premise context (1-hop, 2/2 premises, ≈356 tokens)
### `not_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem not_and : ¬(a ∧ b) ↔ (a → ¬b) := and_imp
```

### `Bool` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Bool` is the type of boolean values, `true` and `false`. Classically,
this is equivalent to `Prop` (the type of propositions), but the distinction
is important for programming, because values of type `Prop` are erased in the
code generator, while `Bool` corresponds to the type called `bool` or `boolean`
in most programming languages.
-/
inductive Bool : Type where
  /-- The boolean value `false`, not to be confused with the proposition `False`. -/
  | false : Bool
  /-- The boolean value `true`, not to be confused with the proposition `True`. -/
  | true : Bool

export Bool (false true)

/--
`Subtype p`, usually written as `{x : α // p x}`, is a type which
represents all the elements `x : α` for which `p x` is true. It is structurally
a pair-like type, so if you have `x : α` and `h : p x` then
`⟨x, h⟩ : {x // p x}`. An element `s : {x // p x}` will coerce to `α` but
you can also make it explicit using `s.1` or `s.val`.
-/
```
