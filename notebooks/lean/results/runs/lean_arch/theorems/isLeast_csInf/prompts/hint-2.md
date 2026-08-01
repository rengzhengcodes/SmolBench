## Current goal
```
⊢ IsLeast s (argminOn id ⋯ s hs)
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
inst✝¹ : ConditionallyCompleteLinearOrder α
s t : Set α
a b : α
inst✝ : IsWellOrder α fun x x_1 => x < x_1
hs : Set.Nonempty s
⊢ IsLeast s (argminOn id ⋯ s hs)
```

## Proof so far (1 tactic)
```lean
rw [sInf_eq_argmin_on hs]
```

## Theorem
`isLeast_csInf` in `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`

## Premises used in the next tactic
- `Function.argminOn_mem`
- `Function.argminOn_le`
- `id`

## Premise signatures
### `Function.argminOn_mem` (commanddeclaration)
```lean
@[simp]
theorem argminOn_mem (s : Set α) (hs : s.Nonempty) : argminOn f h s hs ∈ s
```

### `Function.argminOn_le` (commanddeclaration)
```lean
theorem argminOn_le (s : Set α) {a : α} (ha : a ∈ s) (hs : s.Nonempty := Set.nonempty_of_mem ha) :
    f (argminOn f h s hs) ≤ f a
```

### `id` (commanddeclaration)
```lean
@[inline] def id {α : Sort u} (a : α) : α
```

## Premise full source (with proof)
### `Function.argminOn_mem` (commanddeclaration) at `Mathlib/Order/WellFounded.lean`
```lean
@[simp]
theorem argminOn_mem (s : Set α) (hs : s.Nonempty) : argminOn f h s hs ∈ s :=
  WellFounded.min_mem _ _ _
```

### `Function.argminOn_le` (commanddeclaration) at `Mathlib/Order/WellFounded.lean`
```lean
theorem argminOn_le (s : Set α) {a : α} (ha : a ∈ s) (hs : s.Nonempty := Set.nonempty_of_mem ha) :
    f (argminOn f h s hs) ≤ f a :=
  not_lt.mp <| not_lt_argminOn f h s ha hs
```

### `id` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The identity function. `id` takes an implicit argument `α : Sort u`
(a type in any universe), and an argument `a : α`, and returns `a`.

Although this may look like a useless function, one application of the identity
function is to explicitly put a type on an expression. If `e` has type `T`,
and `T'` is definitionally equal to `T`, then `@id T' e` typechecks, and Lean
knows that this expression has type `T'` rather than `T`. This can make a
difference for typeclass inference, since `T` and `T'` may have different
typeclass instances on them. `show T' from e` is sugar for an `@id T' e`
expression.
-/
@[inline] def id {α : Sort u} (a : α) : α := a

/--
Function composition is the act of pipelining the result of one function, to the input of another, creating an entirely new function.
Example:
```
```
