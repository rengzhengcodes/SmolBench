## Current goal
```
⊢ swap (iSup f) = ⨆ i, swap (f i)
```

## Full tactic state
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
κ : ι → Sort u_7
κ' : ι' → Sort u_8
inst✝¹ : SupSet α
inst✝ : SupSet β
f : ι → α × β
⊢ swap (iSup f) = ⨆ i, swap (f i)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Prod.swap_iSup` in `Mathlib/Order/CompleteLattice.lean`

## Premises used in the next tactic
- `iSup`
- `Prod.swap_sSup`
- `Set.range_comp`
- `Function.comp`

## Premise signatures
### `iSup` (commanddeclaration)
```lean
def iSup [SupSet α] (s : ι → α) : α
```

### `Prod.swap_sSup` (commanddeclaration)
```lean
theorem swap_sSup [SupSet α] [SupSet β] (s : Set (α × β)) : (sSup s).swap = sSup (Prod.swap '' s)
```

### `Set.range_comp` (commanddeclaration)
```lean
theorem range_comp (g : α → β) (f : ι → α) : range (g ∘ f) = g '' range f
```

### `Function.comp` (commanddeclaration)
```lean
@[inline] def Function.comp {α : Sort u} {β : Sort v} {δ : Sort w} (f : β → δ) (g : α → β) : α → δ
```

## Premise full source (with proof)
### `iSup` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
/-- Indexed supremum -/
def iSup [SupSet α] (s : ι → α) : α :=
  sSup (range s)
```

### `Prod.swap_sSup` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem swap_sSup [SupSet α] [SupSet β] (s : Set (α × β)) : (sSup s).swap = sSup (Prod.swap '' s) :=
  ext (congr_arg sSup <| image_comp Prod.fst swap s : _)
    (congr_arg sSup <| image_comp Prod.snd swap s : _)
```

### `Set.range_comp` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
theorem range_comp (g : α → β) (f : ι → α) : range (g ∘ f) = g '' range f := by aesop
```

### `Function.comp` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Function composition is the act of pipelining the result of one function, to the input of another, creating an entirely new function.
Example:
```
#eval Function.comp List.reverse (List.drop 2) [3, 2, 4, 1]
-- [1, 4]
```
You can use the notation `f ∘ g` as shorthand for `Function.comp f g`.
```
#eval (List.reverse ∘ List.drop 2) [3, 2, 4, 1]
-- [1, 4]
```
A simpler way of thinking about it, is that `List.reverse ∘ List.drop 2`
is equivalent to `fun xs => List.reverse (List.drop 2 xs)`,
the benefit is that the meaning of composition is obvious,
and the representation is compact.
-/
@[inline] def Function.comp {α : Sort u} {β : Sort v} {δ : Sort w} (f : β → δ) (g : α → β) : α → δ :=
  fun x => f (g x)

/--
The constant function. If `a : α`, then `Function.const β a : β → α` is the
"constant function with value `a`", that is, `Function.const β a b = a`.
```
```

## Transitive premise context (1-hop, 12/12 premises, ≈1365 tokens)
### `SupSet` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
/-- Class for the `sSup` operator -/
class SupSet (α : Type*) where
  sSup : Set α → α
```

### `Prod.swap` (commanddeclaration) at `Mathlib/Data/Prod/Basic.lean`
```lean
/-- Swap the factors of a product. `swap (a, b) = (b, a)` -/
def swap : α × β → β × α := fun p ↦ (p.2, p.1)
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
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

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
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

### `List.reverse` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
/--
`O(|as|)`. Reverse of a list:
* `[1, 2, 3, 4].reverse = [4, 3, 2, 1]`

Note that because of the "functional but in place" optimization implemented by Lean's compiler,
this function works without any allocations provided that the input list is unshared:
it simply walks the linked list and reverses all the node pointers.
-/
def reverse (as : List α) : List α :=
  reverseAux as []
```

### `List.drop` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
/--
`O(min n |xs|)`. Removes the first `n` elements of `xs`.
* `drop 0 [a, b, c, d, e] = [a, b, c, d, e]`
* `drop 3 [a, b, c, d, e] = [d, e]`
* `drop 6 [a, b, c, d, e] = []`
-/
def drop : Nat → List α → List α
  | 0,   a     => a
  | _+1, []    => []
  | n+1, _::as => drop n as
```

### `Lean.Parser.Command.notation` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Syntax.lean`
```lean
@[builtin_command_parser] def «notation»    := leading_parser
  optional docComment >> optional Term.«attributes» >> Term.attrKind >>
  "notation" >> optPrecedence >> optNamedName >> optNamedPrio >> many notationItem >> darrow >> termParser
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

### `Function.const` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The constant function. If `a : α`, then `Function.const β a : β → α` is the
"constant function with value `a`", that is, `Function.const β a b = a`.
```
example (b : Bool) : Function.const Bool 10 b = 10 :=
  rfl

#check Function.const Bool 10
-- Bool → Nat
```
-/
@[inline] def Function.const {α : Sort u} (β : Sort v) (a : α) : β → α :=
  fun _ => a

/--
The encoding of `let_fun x := v; b` is `letFun v (fun x => b)`.
This is equal to `(fun x => b) v`, so the value of `x` is not accessible to `b`.
This is in contrast to `let x := v; b`, where the value of `x` is accessible to `b`.

There is special support for `letFun`.
Both WHNF and `simp` are aware of `letFun` and can reduce it when zeta reduction is enabled,
despite the fact it is marked `irreducible`.
For metaprogramming, the function `Lean.Expr.letFun?` can be used to recognize a `let_fun` expression
to extract its parts as if it were a `let` expression.
-/
```
