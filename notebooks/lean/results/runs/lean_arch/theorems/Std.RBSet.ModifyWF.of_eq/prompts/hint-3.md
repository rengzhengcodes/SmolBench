## Current goal
```
⊢ (∀ {x : α}, root? (zoom cut t.val).fst = some x → cmpEq cmp (f x) x) →
    OnRoot (fun x => cmpEq cmp (f x) x) (zoom cut t.val).fst
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
cut : α → Ordering
f : α → α
t : RBSet α cmp
⊢ (∀ {x : α}, root? (zoom cut t.val).fst = some x → cmpEq cmp (f x) x) →
    OnRoot (fun x => cmpEq cmp (f x) x) (zoom cut t.val).fst
```

## Proof so far (3 tactics)
```lean
refine ⟨.modify ?_ t.2⟩
revert H
rw [find?_eq_zoom]
```

## Theorem
`Std.RBSet.ModifyWF.of_eq` in `.lake/packages/std/Std/Data/RBMap/Alter.lean`

## Premises used in the next tactic
- `Std.RBNode.zoom`
- `rfl`

## Premise signatures
### `Std.RBNode.zoom` (commanddeclaration)
```lean
@[specialize] def zoom (cut : α → Ordering) : RBNode α → (e : Path α := .root) → RBNode α × Path α
  | nil, path => (nil, path)
  | n@(node c a y b), path =>
    match cut y with
    | .lt => zoom cut a (.left c path y b)
    | .gt => zoom cut b (.right c a y path)
    | .eq => (n, path)
```

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

## Premise full source (with proof)
### `Std.RBNode.zoom` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/--
Like `find?`, but instead of just returning the element, it returns the entire subtree
at the element and a path back to the root for reconstructing the tree.
-/
@[specialize] def zoom (cut : α → Ordering) : RBNode α → (e : Path α := .root) → RBNode α × Path α
  | nil, path => (nil, path)
  | n@(node c a y b), path =>
    match cut y with
    | .lt => zoom cut a (.left c path y b)
    | .gt => zoom cut b (.right c a y path)
    | .eq => (n, path)

/--
This function does the second part of `RBNode.ins`,
which unwinds the stack and rebuilds the tree.
-/
```

### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```

## Transitive premise context (1-hop, 5/5 premises, ≈802 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Ordering` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Ord.lean`
```lean
inductive Ordering where
  | lt | eq | gt
deriving Inhabited, BEq
```

### `Path` (commanddeclaration) at `Mathlib/Topology/Connected/PathConnected.lean`
```lean
/-- Continuous path connecting two points `x` and `y` in a topological space -/
-- porting note (#10927): removed @[nolint has_nonempty_instance]
structure Path (x y : X) extends C(I, X) where
  /-- The start point of a `Path`. -/
  source' : toFun 0 = x
  /-- The end point of a `Path`. -/
  target' : toFun 1 = y
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `Eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The equality relation. It has one introduction rule, `Eq.refl`.
We use `a = b` as notation for `Eq a b`.
A fundamental property of equality is that it is an equivalence relation.
```
variable (α : Type) (a b c d : α)
variable (hab : a = b) (hcb : c = b) (hcd : c = d)

example : a = d :=
  Eq.trans (Eq.trans hab (Eq.symm hcb)) hcd
```
Equality is much more than an equivalence relation, however. It has the important property that every assertion
respects the equivalence, in the sense that we can substitute equal expressions without changing the truth value.
That is, given `h1 : a = b` and `h2 : p a`, we can construct a proof for `p b` using substitution: `Eq.subst h1 h2`.
Example:
```
example (α : Type) (a b : α) (p : α → Prop)
        (h1 : a = b) (h2 : p a) : p b :=
  Eq.subst h1 h2

example (α : Type) (a b : α) (p : α → Prop)
    (h1 : a = b) (h2 : p a) : p b :=
  h1 ▸ h2
```
The triangle in the second presentation is a macro built on top of `Eq.subst` and `Eq.symm`, and you can enter it by typing `\t`.
For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
inductive Eq : α → α → Prop where
  /-- `Eq.refl a : a = a` is reflexivity, the unique constructor of the
  equality type. See also `rfl`, which is usually used instead. -/
  | refl (a : α) : Eq a a

/-- Non-dependent recursor for the equality type. -/
```
