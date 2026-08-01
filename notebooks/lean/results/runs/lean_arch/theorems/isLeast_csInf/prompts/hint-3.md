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

## Transitive premise context (1-hop, 11/11 premises, ≈1012 tokens)
### `Function.argminOn` (commanddeclaration) at `Mathlib/Order/WellFounded.lean`
```lean
/-- Given a function `f : α → β` where `β` carries a well-founded `<`, and a non-empty subset `s`
of `α`, this is an element of `s` whose image under `f` is minimal in the sense of
`Function.not_lt_argminOn`. -/
noncomputable def argminOn (s : Set α) (hs : s.Nonempty) : α :=
  WellFounded.min (InvImage.wf f h) s hs
```

### `WellFounded.min_mem` (commanddeclaration) at `Mathlib/Order/WellFounded.lean`
```lean
theorem min_mem {r : α → α → Prop} (H : WellFounded r) (s : Set α) (h : s.Nonempty) :
    H.min s h ∈ s :=
  let ⟨h, _⟩ := Classical.choose_spec (H.has_min s h)
  h
```

### `Set.nonempty_of_mem` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
theorem nonempty_of_mem {x} (h : x ∈ s) : s.Nonempty :=
  ⟨x, h⟩
```

### `Function.not_lt_argminOn` (commanddeclaration) at `Mathlib/Order/WellFounded.lean`
```lean
theorem not_lt_argminOn (s : Set α) {a : α} (ha : a ∈ s)
    (hs : s.Nonempty := Set.nonempty_of_mem ha) : ¬f a < f (argminOn f h s hs) :=
  WellFounded.not_lt_min (InvImage.wf f h) s hs ha
```

### `Lean.Parser.Term.argument` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
def argument       :=
  checkWsBefore "expected space" >>
  checkColGt "expected to be indented" >>
  (namedArgument <|> ellipsis <|> termParser argPrec)
-- `app` precedence is `lead` (cannot be used as argument)
-- `lhs` precedence is `max` (i.e. does not accept `arg` precedence)
-- argument precedence is `arg` (i.e. does not accept `lead` precedence)
```

### `Lean.Parser.Command.universe` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
@[builtin_command_parser] def «universe»     := leading_parser
  "universe" >> many1 (ppSpace >> ident)
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `inline` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`inline (f x)` is an indication to the compiler to inline the definition of `f`
at the application site itself (by comparison to the `@[inline]` attribute,
which applies to all applications of the function).
-/
@[simp] def inline {α : Sort u} (a : α) : α := a
```

### `Stream'.composition` (commanddeclaration) at `Mathlib/Data/Stream/Init.lean`
```lean
theorem composition (g : Stream' (β → δ)) (f : Stream' (α → β)) (s : Stream' α) :
    pure comp ⊛ g ⊛ f ⊛ s = g ⊛ (f ⊛ s) :=
  rfl
```

### `IO.Promise.result` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/System/Promise.lean`
```lean
/--
The result task of a `Promise`.

The task blocks until `Promise.resolve` is called.
-/
@[extern "lean_io_promise_result"]
opaque Promise.result (promise : Promise α) : Task α :=
  have : Nonempty α := promise.h
  Classical.choice inferInstance
```

### `Lean.Meta.Match.Example` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Match/Basic.lean`
```lean
inductive Example where
  | var        : FVarId → Example
  | underscore : Example
  | ctor       : Name → List Example → Example
  | val        : Expr → Example
  | arrayLit   : List Example → Example
```
