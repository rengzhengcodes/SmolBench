## Current goal
```
⊢ x = id^[k] x
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
inst✝ : SuccOrder α
a b : α
k : ℕ
x : α
⊢ x = id^[k] x
```

## Proof so far (2 tactics)
```lean
conv_lhs => rw [(by simp only [Function.iterate_id, id.def] : x = id^[k] x)]
exact Monotone.le_iterate_of_le succ_mono le_succ k x
```

## Theorem
`Order.le_succ_iterate` in `Mathlib/Order/SuccPred/Basic.lean`

## Premises used in the next tactic
- `Function.iterate_id`
- `id.def`

## Premise signatures
### `Function.iterate_id` (commanddeclaration)
```lean
@[simp]
theorem iterate_id (n : ℕ) : (id : α → α)^[n] = id
```

### `id.def` (commanddeclaration)
```lean
theorem id.def {α : Sort u} (a : α) : id a = a
```

## Premise full source (with proof)
### `Function.iterate_id` (commanddeclaration) at `Mathlib/Logic/Function/Iterate.lean`
```lean
@[simp]
theorem iterate_id (n : ℕ) : (id : α → α)^[n] = id :=
  Nat.recOn n rfl fun n ihn ↦ by rw [iterate_succ, ihn, id_comp]
```

### `id.def` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem id.def {α : Sort u} (a : α) : id a = a := rfl

/--
`flip f a b` is `f b a`. It is useful for "point-free" programming,
since it can sometimes be used to avoid introducing variables.
For example, `(·<·)` is the less-than relation,
and `flip (·<·)` is the greater-than relation.
-/
```

## Transitive premise context (1-hop, 5/5 premises, ≈1350 tokens)
### `flip` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`flip f a b` is `f b a`. It is useful for "point-free" programming,
since it can sometimes be used to avoid introducing variables.
For example, `(·<·)` is the less-than relation,
and `flip (·<·)` is the greater-than relation.
-/
@[inline] def flip {α : Sort u} {β : Sort v} {φ : Sort w} (f : α → β → φ) : β → α → φ :=
  fun b a => f a b
```

### `free` (commanddeclaration) at `Mathlib/Algebra/Category/MonCat/Adjunctions.lean`
```lean
/-- The free functor `Type u ⥤ MonCat` sending a type `X` to the free monoid on `X`. -/
def free : Type u ⥤ MonCat.{u} where
  obj α := MonCat.of (FreeMonoid α)
  map := FreeMonoid.map
  map_id _ := FreeMonoid.hom_eq (fun _ => rfl)
  map_comp _ _ := FreeMonoid.hom_eq (fun _ => rfl)
```

### `Function.sometimes` (commanddeclaration) at `Mathlib/Logic/Function/Basic.lean`
```lean
/-- `sometimes f` evaluates to some value of `f`, if it exists. This function is especially
interesting in the case where `α` is a proposition, in which case `f` is necessarily a
constant function, so that `sometimes f = f a` for all `a`. -/
noncomputable def sometimes {α β} [Nonempty β] (f : α → β) : β :=
  if h : Nonempty α then f (Classical.choice h) else Classical.choice ‹_›
```

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

### `Finpartition.avoid` (commanddeclaration) at `Mathlib/Order/Partition/Finpartition.lean`
```lean
/-- Restricts a finpartition to avoid a given element. -/
@[simps!]
def avoid (b : α) : Finpartition (a \ b) :=
  ofErase
    (P.parts.image (· \ b))
    (P.disjoint.image_finset_of_le fun a ↦ sdiff_le).supIndep
    (by rw [sup_image, id_comp, Finset.sup_sdiff_right, ← Function.id_def, P.sup_parts])
```
