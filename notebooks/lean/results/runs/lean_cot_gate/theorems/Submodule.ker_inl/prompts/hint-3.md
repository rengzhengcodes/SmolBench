## Current goal
```
⊢ ker (inl R M M₂) = ⊥
```

## Full tactic state
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
M₃ : Type y
V₃ : Type y'
M₄ : Type z
ι : Type x
M₅ : Type u_1
M₆ : Type u_2
inst✝⁴ : Semiring R
inst✝³ : AddCommMonoid M
inst✝² : AddCommMonoid M₂
inst✝¹ : Module R M
inst✝ : Module R M₂
p : Submodule R M
q : Submodule R M₂
⊢ ker (inl R M M₂) = ⊥
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Submodule.ker_inl` in `Mathlib/LinearAlgebra/Prod.lean`

## Premises used in the next tactic
- `LinearMap.ker`
- `Submodule.prod_bot`
- `Submodule.prod_comap_inl`

## Premise signatures
### `LinearMap.ker` (commanddeclaration)
```lean
def ker (f : F) : Submodule R M
```

### `Submodule.prod_bot` (commanddeclaration)
```lean
@[simp]
theorem prod_bot : (prod ⊥ ⊥ : Submodule R (M × M')) = ⊥
```

### `Submodule.prod_comap_inl` (commanddeclaration)
```lean
@[simp]
theorem prod_comap_inl : (prod p q).comap (inl R M M₂) = p
```

## Premise full source (with proof)
### `LinearMap.ker` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
/-- The kernel of a linear map `f : M → M₂` is defined to be `comap f ⊥`. This is equivalent to the
set of `x : M` such that `f x = 0`. The kernel is a submodule of `M`. -/
def ker (f : F) : Submodule R M :=
  comap f ⊥
```

### `Submodule.prod_bot` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
@[simp]
theorem prod_bot : (prod ⊥ ⊥ : Submodule R (M × M')) = ⊥ := by ext ⟨x, y⟩; simp [Prod.zero_eq_mk]
```

### `Submodule.prod_comap_inl` (commanddeclaration) at `Mathlib/LinearAlgebra/Prod.lean`
```lean
@[simp]
theorem prod_comap_inl : (prod p q).comap (inl R M M₂) = p := by ext; simp
```

## Transitive premise context (1-hop, 2/2 premises, ≈934 tokens)
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

### `Submodule` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Basic.lean`
```lean
/-- A submodule of a module is one which is closed under vector operations.
  This is a sufficient condition for the subset of vectors in the submodule
  to themselves form a module. -/
structure Submodule (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M] [Module R M] extends
  AddSubmonoid M, SubMulAction R M : Type v
```
