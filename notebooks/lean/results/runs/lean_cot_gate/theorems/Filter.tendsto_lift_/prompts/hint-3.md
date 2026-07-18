## Current goal
```
⊢ Tendsto m l (Filter.lift' f h) ↔ ∀ s ∈ f, ∀ᶠ (a : γ) in l, m a ∈ h s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
m : γ → β
l : Filter γ
⊢ Tendsto m l (Filter.lift' f h) ↔ ∀ s ∈ f, ∀ᶠ (a : γ) in l, m a ∈ h s
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.tendsto_lift'` in `Mathlib/Order/Filter/Lift.lean`

## Premises used in the next tactic
- `Filter.lift'`
- `Filter.tendsto_lift`
- `Filter.tendsto_principal`
- `Function.comp`

## Premise signatures
### `Filter.lift'` (commanddeclaration)
```lean
protected def lift' (f : Filter α) (h : Set α → Set β)
```

### `Filter.tendsto_lift` (commanddeclaration)
```lean
theorem tendsto_lift {m : γ → β} {l : Filter γ} :
    Tendsto m l (f.lift g) ↔ ∀ s ∈ f, Tendsto m l (g s)
```

### `Filter.tendsto_principal` (commanddeclaration)
```lean
@[simp] theorem tendsto_principal {f : α → β} {l : Filter α} {s : Set β} :
    Tendsto f l (𝓟 s) ↔ ∀ᶠ a in l, f a ∈ s
```

### `Function.comp` (commanddeclaration)
```lean
@[inline] def Function.comp {α : Sort u} {β : Sort v} {δ : Sort w} (f : β → δ) (g : α → β) : α → δ
```

## Premise full source (with proof)
### `Filter.lift'` (commanddeclaration) at `Mathlib/Order/Filter/Lift.lean`
```lean
/-- Specialize `lift` to functions `Set α → Set β`. This can be viewed as a generalization of `map`.
This is essentially a push-forward along a function mapping each set to a set. -/
protected def lift' (f : Filter α) (h : Set α → Set β) :=
  f.lift (𝓟 ∘ h)
```

### `Filter.tendsto_lift` (commanddeclaration) at `Mathlib/Order/Filter/Lift.lean`
```lean
theorem tendsto_lift {m : γ → β} {l : Filter γ} :
    Tendsto m l (f.lift g) ↔ ∀ s ∈ f, Tendsto m l (g s) := by
  simp only [Filter.lift, tendsto_iInf]
```

### `Filter.tendsto_principal` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp] theorem tendsto_principal {f : α → β} {l : Filter α} {s : Set β} :
    Tendsto f l (𝓟 s) ↔ ∀ᶠ a in l, f a ∈ s := by
  simp only [Tendsto, le_principal_iff, mem_map', Filter.Eventually]
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

## Transitive premise context (1-hop, 15/15 premises, ≈2621 tokens)
### `Std.Format.be` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Format/Basic.lean`
```lean
private partial def be (w : Nat) [Monad m] [MonadPrettyFormat m] : List WorkGroup → m Unit
  | []                           => pure ()
  |   { items := [],    .. }::gs => be w gs
  | g@{ items := i::is, .. }::gs => do
    let gs' (is' : List WorkItem) := { g with items := is' }::gs;
    match i.f with
    | nil =>
      endTags i.activeTags
      be w (gs' is)
    | tag t f =>
      startTag t
      be w (gs' ({ i with f, activeTags := i.activeTags + 1 }::is))
    | append f₁ f₂ => be w (gs' ({ i with f := f₁, activeTags := 0 }::{ i with f := f₂ }::is))
    | nest n f => be w (gs' ({ i with f, indent := i.indent + n }::is))
    | text s =>
      let p := s.posOf '\n'
      if p == s.endPos then
        pushOutput s
        endTags i.activeTags
        be w (gs' is)
      else
        pushOutput (s.extract {} p)
        pushNewline i.indent.toNat
        let is := { i with f := text (s.extract (s.next p) s.endPos) }::is
        -- after a hard line break, re-evaluate whether to flatten the remaining group
        pushGroup g.flb is gs w >>= be w
    | line =>
      match g.flb with
      | FlattenBehavior.allOrNone =>
        if g.flatten then
          -- flatten line = text " "
          pushOutput " "
          endTags i.activeTags
          be w (gs' is)
        else
          pushNewline i.indent.toNat
          endTags i.activeTags
          be w (gs' is)
      | FlattenBehavior.fill =>
        let breakHere := do
          pushNewline i.indent.toNat
          -- make new `fill` group and recurse
          endTags i.activeTags
          pushGroup FlattenBehavior.fill is gs w >>= be w
        -- if preceding fill item fit in a single line, try to fit next one too
        if g.flatten then
          let gs'@(g'::_) ← pushGroup FlattenBehavior.fill is gs (w - " ".length)
            | panic "unreachable"
          if g'.flatten then
            pushOutput " "
            endTags i.activeTags
            be w gs'  -- TODO: use `return`
          else
            breakHere
        else
          breakHere
    | align force =>
      if g.flatten && !force then
        -- flatten (align false) = nil
        endTags i.activeTags
        be w (gs' is)
      else
        let k ← currColumn
        if k < i.indent then
          pushOutput ("".pushn ' ' (i.indent - k).toNat)
          endTags i.activeTags
          be w (gs' is)
        else
          pushNewline i.indent.toNat
          endTags i.activeTags
          be w (gs' is)
    | group f flb =>
      if g.flatten then
        -- flatten (group f) = flatten f
        be w (gs' ({ i with f }::is))
      else
        pushGroup flb [{ i with f }] (gs' is) w >>= be w

/-- Render the given `f : Format` with a line width of `w`.
`indent` is the starting amount to indent each line by. -/
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `Filter` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
/-- A filter `F` on a type `α` is a collection of sets of `α` which contains the whole `α`,
is upwards-closed, and is stable under intersection. We do not forbid this collection to be
all sets of `α`. -/
structure Filter (α : Type*) where
  /-- The set of sets that belong to the filter. -/
  sets : Set (Set α)
  /-- The set `Set.univ` belongs to any filter. -/
  univ_sets : Set.univ ∈ sets
  /-- If a set belongs to a filter, then its superset belongs to the filter as well. -/
  sets_of_superset {x y} : x ∈ sets → x ⊆ y → y ∈ sets
  /-- If two sets belong to a filter, then their intersection belongs to the filter as well. -/
  inter_sets {x y} : x ∈ sets → y ∈ sets → x ∩ y ∈ sets
```

### `Filter.lift` (commanddeclaration) at `Mathlib/Order/Filter/Lift.lean`
```lean
/-- A variant on `bind` using a function `g` taking a set instead of a member of `α`.
This is essentially a push-forward along a function mapping each set to a filter. -/
protected def lift (f : Filter α) (g : Set α → Filter β) :=
  ⨅ s ∈ f, g s
```

### `Filter.tendsto_iInf` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem tendsto_iInf {f : α → β} {x : Filter α} {y : ι → Filter β} :
    Tendsto f x (⨅ i, y i) ↔ ∀ i, Tendsto f x (y i) := by
  simp only [Tendsto, iff_self_iff, le_iInf_iff]
```

### `Filter.le_principal_iff` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem le_principal_iff {s : Set α} {f : Filter α} : f ≤ 𝓟 s ↔ s ∈ f :=
  ⟨fun h => h Subset.rfl, fun hs _ ht => mem_of_superset hs ht⟩
```

### `Filter.Eventually` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
/-- `f.Eventually p` or `∀ᶠ x in f, p x` mean that `{x | p x} ∈ f`. E.g., `∀ᶠ x in atTop, p x`
means that `p` holds true for sufficiently large `x`. -/
protected def Eventually (p : α → Prop) (f : Filter α) : Prop :=
  { x | p x } ∈ f
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
