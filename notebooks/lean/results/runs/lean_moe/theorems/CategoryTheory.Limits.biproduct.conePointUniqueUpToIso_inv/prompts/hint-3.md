## Current goal
```
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```

## Full tactic state
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
inst✝¹ : HasZeroMorphisms D
f : J → C
inst✝ : HasBiproduct f
b : Bicone f
hb : Bicone.IsBilimit b
j : J
j' : Discrete J
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```

## Proof so far (1 tactic)
```lean
refine' biproduct.hom_ext' _ _ fun j => hb.isLimit.hom_ext fun j' => _
```

## Theorem
`CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv` in `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`
- `CategoryTheory.Limits.Bicone.toCone_π_app`
- `CategoryTheory.Limits.biproduct.bicone_π`
- `CategoryTheory.Limits.biproduct.ι_desc`
- `CategoryTheory.Limits.biproduct.ι_π`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem conePointUniqueUpToIso_inv_comp {s t : Cone F} (P : IsLimit s) (Q : IsLimit t) (j : J) :
    (conePointUniqueUpToIso P Q).inv ≫ s.π.app j = t.π.app j
```

### `CategoryTheory.Limits.Bicone.toCone_π_app` (commanddeclaration)
```lean
@[simp]
theorem toCone_π_app (B : Bicone F) (j : Discrete J) : B.toCone.π.app j = B.π j.as
```

### `CategoryTheory.Limits.biproduct.bicone_π` (commanddeclaration)
```lean
@[simp]
theorem biproduct.bicone_π (f : J → C) [HasBiproduct f] (b : J) :
    (biproduct.bicone f).π b = biproduct.π f b
```

### `CategoryTheory.Limits.biproduct.ι_desc` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem biproduct.ι_desc {f : J → C} [HasBiproduct f] {P : C} (p : ∀ b, f b ⟶ P) (j : J) :
    biproduct.ι f j ≫ biproduct.desc p = p j
```

### `CategoryTheory.Limits.biproduct.ι_π` (commanddeclaration)
```lean
@[reassoc]
theorem biproduct.ι_π [DecidableEq J] (f : J → C) [HasBiproduct f] (j j' : J) :
    biproduct.ι f j ≫ biproduct.π f j' = if h : j = j' then eqToHom (congr_arg f h) else 0
```

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
@[reassoc (attr := simp)]
theorem conePointUniqueUpToIso_inv_comp {s t : Cone F} (P : IsLimit s) (Q : IsLimit t) (j : J) :
    (conePointUniqueUpToIso P Q).inv ≫ s.π.app j = t.π.app j :=
  (uniqueUpToIso P Q).inv.w _
```

### `CategoryTheory.Limits.Bicone.toCone_π_app` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[simp]
theorem toCone_π_app (B : Bicone F) (j : Discrete J) : B.toCone.π.app j = B.π j.as := rfl
```

### `CategoryTheory.Limits.biproduct.bicone_π` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[simp]
theorem biproduct.bicone_π (f : J → C) [HasBiproduct f] (b : J) :
    (biproduct.bicone f).π b = biproduct.π f b := rfl
```

### `CategoryTheory.Limits.biproduct.ι_desc` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc (attr := simp)]
theorem biproduct.ι_desc {f : J → C} [HasBiproduct f] {P : C} (p : ∀ b, f b ⟶ P) (j : J) :
    biproduct.ι f j ≫ biproduct.desc p = p j := (biproduct.isColimit f).fac _ ⟨j⟩
```

### `CategoryTheory.Limits.biproduct.ι_π` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
/-- Note that as this lemma has an `if` in the statement, we include a `DecidableEq` argument.
This means you may not be able to `simp` using this lemma unless you `open scoped Classical`. -/
@[reassoc]
theorem biproduct.ι_π [DecidableEq J] (f : J → C) [HasBiproduct f] (j j' : J) :
    biproduct.ι f j ≫ biproduct.π f j' = if h : j = j' then eqToHom (congr_arg f h) else 0 := by
  convert (biproduct.bicone f).ι_π j j'
```

## Transitive premise context (1-hop, 9/9 premises, ≈1744 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.Cone` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Cones.lean`
```lean
/-- A `c : Cone F` is:
* an object `c.pt` and
* a natural transformation `c.π : c.pt ⟶ F` from the constant `c.pt` functor to `F`.

Example: if `J` is a category coming from a poset then the data required to make
a term of type `Cone F` is morphisms `πⱼ : c.pt ⟶ F j` for all `j : J` and,
for all `i ≤ j` in `J`, morphisms `πᵢⱼ : F i ⟶ F j` such that `πᵢ ≫ πᵢⱼ = πᵢ`.

`Cone F` is equivalent, via `cone.equiv` below, to `Σ X, F.cones.obj X`.
-/
structure Cone (F : J ⥤ C) where
  /-- An object of `C` -/
  pt : C
  /-- A natural transformation from the constant functor at `X` to `F` -/
  π : (const J).obj pt ⟶ F
```

### `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
/-- Limits of `F` are unique up to isomorphism. -/
def conePointUniqueUpToIso {s t : Cone F} (P : IsLimit s) (Q : IsLimit t) : s.pt ≅ t.pt :=
  (Cones.forget F).mapIso (uniqueUpToIso P Q)
```

### `CategoryTheory.Discrete` (commanddeclaration) at `Mathlib/CategoryTheory/DiscreteCategory.lean`
```lean
/-- A wrapper for promoting any type to a category,
with the only morphisms being equalities.
-/
@[ext, aesop safe cases (rule_sets := [CategoryTheory])]
structure Discrete (α : Type u₁) where
  /-- A wrapper for promoting any type to a category,
  with the only morphisms being equalities. -/
  as : α
```

### `CategoryTheory.Limits.HasBiproduct` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
/-- `HasBiproduct F` expresses the mere existence of a bicone which is
simultaneously a limit and a colimit of the diagram `F`.
-/
class HasBiproduct (F : J → C) : Prop where mk' ::
  exists_biproduct : Nonempty (LimitBicone F)
```

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

### `Lean.Parser.Term.scoped` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
def «scoped» := leading_parser "scoped "
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```
