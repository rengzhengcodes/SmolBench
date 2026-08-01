## Current goal
```
⊢ (colimitCocone F).ι.app j xj =
    (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι.app j xj)
```

## Full tactic state
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
t : Cocone F
ht : IsColimit t
i j : J
xi : F.obj i
xj : F.obj j
e_1✝ : ((Functor.const J).obj (colimitCocone F).pt).obj i = (colimitCocone F).pt
⊢ (colimitCocone F).ι.app j xj =
    (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι.app j xj)
```

## Proof so far (4 tactics)
```lean
refine' Iff.trans _ (colimit_eq_iff_aux F)
rw [← (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv.injective.eq_iff]
convert Iff.rfl
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xi).symm
```

## Theorem
`CategoryTheory.Limits.Types.FilteredColimit.isColimit_eq_iff` in `Mathlib/CategoryTheory/Limits/Types.lean`

## Premises used in the next tactic
- `congrFun`
- `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom`
- `CategoryTheory.Limits.Types.colimitCoconeIsColimit`
- `Eq.symm`

## Premise signatures
### `congrFun` (commanddeclaration)
```lean
theorem congrFun {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x} (h : Eq f g) (a : α) : Eq (f a) (g a)
```

### `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem comp_coconePointUniqueUpToIso_hom {s t : Cocone F} (P : IsColimit s) (Q : IsColimit t)
    (j : J) : s.ι.app j ≫ (coconePointUniqueUpToIso P Q).hom = t.ι.app j
```

### `CategoryTheory.Limits.Types.colimitCoconeIsColimit` (commanddeclaration)
```lean
noncomputable def colimitCoconeIsColimit (F : J ⥤ Type u) [Small.{u} (Quot F)] :
    IsColimit (colimitCocone F)
```

### `Eq.symm` (commanddeclaration)
```lean
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a
```

## Premise full source (with proof)
### `congrFun` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/-- Congruence in the function part of an application: If `f = g` then `f a = g a`. -/
theorem congrFun {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x} (h : Eq f g) (a : α) : Eq (f a) (g a) :=
  h ▸ rfl

/-!
Initialize the Quotient Module, which effectively adds the following definitions:
```
opaque Quot {α : Sort u} (r : α → α → Prop) : Sort u

opaque Quot.mk {α : Sort u} (r : α → α → Prop) (a : α) : Quot r

opaque Quot.lift {α : Sort u} {r : α → α → Prop} {β : Sort v} (f : α → β) :
  (∀ a b : α, r a b → Eq (f a) (f b)) → Quot r → β

opaque Quot.ind {α : Sort u} {r : α → α → Prop} {β : Quot r → Prop} :
  (∀ a : α, β (Quot.mk r a)) → ∀ q : Quot r, β q
```
-/
init_quot

/--
Let `α` be any type, and let `r` be an equivalence relation on `α`.
It is mathematically common to form the "quotient" `α / r`, that is, the type of
elements of `α` "modulo" `r`. Set theoretically, one can view `α / r` as the set
of equivalence classes of `α` modulo `r`. If `f : α → β` is any function that
respects the equivalence relation in the sense that for every `x y : α`,
`r x y` implies `f x = f y`, then f "lifts" to a function `f' : α / r → β`
defined on each equivalence class `⟦x⟧` by `f' ⟦x⟧ = f x`.
Lean extends the Calculus of Constructions with additional constants that
perform exactly these constructions, and installs this last equation as a
definitional reduction rule.

Given a type `α` and any binary relation `r` on `α`, `Quot r` is a type. Note
that `r` is not required to be an equivalence relation. `Quot` is the basic
building block used to construct later the type `Quotient`.
-/
add_decl_doc Quot

/--
Given a type `α` and any binary relation `r` on `α`, `Quot.mk` maps `α` to `Quot r`.
So that if `r : α → α → Prop` and `a : α`, then `Quot.mk r a` is an element of `Quot r`.

See `Quot`.
-/
add_decl_doc Quot.mk

/--
Given a type `α` and any binary relation `r` on `α`,
`Quot.ind` says that every element of `Quot r` is of the form `Quot.mk r a`.

See `Quot` and `Quot.lift`.
-/
add_decl_doc Quot.ind

/--
Given a type `α`, any binary relation `r` on `α`, a function `f : α → β`, and a proof `h`
that `f` respects the relation `r`, then `Quot.lift f h` is the corresponding function on `Quot r`.

The idea is that for each element `a` in `α`, the function `Quot.lift f h` maps `Quot.mk r a`
(the `r`-class containing `a`) to `f a`, wherein `h` shows that this function is well defined.
In fact, the computation principle is declared as a reduction rule.
-/
add_decl_doc Quot.lift

/--
Unsafe auxiliary constant used by the compiler to erase `Quot.lift`.
-/
unsafe axiom Quot.lcInv {α : Sort u} {r : α → α → Prop} (q : Quot r) : α

/--
Heterogeneous equality. `HEq a b` asserts that `a` and `b` have the same
type, and casting `a` across the equality yields `b`, and vice versa.

You should avoid using this type if you can. Heterogeneous equality does not
have all the same properties as `Eq`, because the assumption that the types of
`a` and `b` are equal is often too weak to prove theorems of interest. One
important non-theorem is the analogue of `congr`: If `HEq f g` and `HEq x y`
and `f x` and `g y` are well typed it does not follow that `HEq (f x) (g y)`.
(This does follow if you have `f = g` instead.) However if `a` and `b` have
the same type then `a = b` and `HEq a b` are equivalent.
-/
```

### `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
@[reassoc (attr := simp)]
theorem comp_coconePointUniqueUpToIso_hom {s t : Cocone F} (P : IsColimit s) (Q : IsColimit t)
    (j : J) : s.ι.app j ≫ (coconePointUniqueUpToIso P Q).hom = t.ι.app j :=
  (uniqueUpToIso P Q).hom.w _
```

### `CategoryTheory.Limits.Types.colimitCoconeIsColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Types.lean`
```lean
/-- (internal implementation) the fact that the proposed colimit cocone is the colimit -/
noncomputable def colimitCoconeIsColimit (F : J ⥤ Type u) [Small.{u} (Quot F)] :
    IsColimit (colimitCocone F) :=
  Nonempty.some <| by
    rw [isColimit_iff_bijective_desc, Quot.desc_colimitCocone]
    exact (equivShrink _).bijective
```

### `Eq.symm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Equality is symmetric: if `a = b` then `b = a`.

Because this is in the `Eq` namespace, if you have a variable `h : a = b`,
`h.symm` can be used as shorthand for `Eq.symm h` as a proof of `b = a`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a :=
  h ▸ rfl

/--
Equality is transitive: if `a = b` and `b = c` then `a = c`.

Because this is in the `Eq` namespace, if you have variables or expressions
`h₁ : a = b` and `h₂ : b = c`, you can use `h₁.trans h₂ : a = c` as shorthand
for `Eq.trans h₁ h₂`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```

## Transitive premise context (1-hop, 34/34 premises, ≈6168 tokens)
### `CategoryTheory.Congruence` (commanddeclaration) at `Mathlib/CategoryTheory/Quotient.lean`
```lean
/-- A `HomRel` is a congruence when it's an equivalence on every hom-set, and it can be composed
from left and right. -/
class Congruence : Prop where
  /-- `r` is an equivalence on every hom-set. -/
  equivalence : ∀ {X Y}, _root_.Equivalence (@r X Y)
  /-- Precomposition with an arrow respects `r`. -/
  compLeft : ∀ {X Y Z} (f : X ⟶ Y) {g g' : Y ⟶ Z}, r g g' → r (f ≫ g) (f ≫ g')
  /-- Postcomposition with an arrow respects `r`. -/
  compRight : ∀ {X Y Z} {f f' : X ⟶ Y} (g : Y ⟶ Z), r f f' → r (f ≫ g) (f' ≫ g)
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

### `Quotient` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`Quotient α s` is the same as `Quot α r`, but it is specialized to a setoid `s`
(that is, an equivalence relation) instead of an arbitrary relation.
Prefer `Quotient` over `Quot` if your relation is actually an equivalence relation.
-/
def Quotient {α : Sort u} (s : Setoid α) :=
  @Quot α Setoid.r
```

### `Module` (commanddeclaration) at `Mathlib/Algebra/Module/Basic.lean`
```lean
/-- A module is a generalization of vector spaces to a scalar semiring.
  It consists of a scalar semiring `R` and an additive monoid of "vectors" `M`,
  connected by a "scalar multiplication" operation `r • x : M`
  (where `r : R` and `x : M`) with some natural associativity and
  distributivity axioms similar to those on a ring. -/
@[ext]
class Module (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M] extends
  DistribMulAction R M where
  /-- Scalar multiplication distributes over addition from the right. -/
  protected add_smul : ∀ (r s : R) (x : M), (r + s) • x = r • x + s • x
  /-- Scalar multiplication by zero gives zero. -/
  protected zero_smul : ∀ x : M, (0 : R) • x = 0
```

### `Lean.Parser.Command.opaque` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
def «opaque»         := leading_parser
  "opaque " >> recover declId skipUntilWsOrDelim >> ppIndent declSig >> optional declValSimple
/- As `declSig` starts with a space, "instance" does not need a trailing space
  if we put `ppSpace` in the optional fragments. -/
```

### `CategoryTheory.Limits.Types.Quot` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Types.lean`
```lean
/-- A quotient type implementing the colimit of a functor `F : J ⥤ Type u`,
as pairs `⟨j, x⟩` where `x : F.obj j`, modulo the equivalence relation generated by
`⟨j, x⟩ ~ ⟨j', x'⟩` whenever there is a morphism `f : j ⟶ j'` so `F.map f x = x'`.
-/
def Quot (F : J ⥤ Type u) : Type (max v u) :=
  _root_.Quot (Quot.Rel F)
```

### `Lean.Parser.Command.init_quot` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
@[builtin_command_parser] def «init_quot»    := leading_parser
  "init_quot"
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

### `LLVM.Linkage.common` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Compiler/IR/LLVMBindings.lean`
```lean
/-- Tentative definitions -/
def Linkage.common : Linkage := { val := 14 }
/-- Like Private, but linker removes. -/
```

### `Setoid.classes` (commanddeclaration) at `Mathlib/Data/Setoid/Partition.lean`
```lean
/-- Makes the equivalence classes of an equivalence relation. -/
def classes (r : Setoid α) : Set (Set α) :=
  { s | ∃ y, s = { x | r.Rel x y } }
```

### `Sat.Valuation.implies` (commanddeclaration) at `Mathlib/Tactic/Sat/FromLRAT.lean`
```lean
/-- `v.implies p [a, b, c] 0` definitionally unfolds to `(v 0 ↔ a) → (v 1 ↔ b) → (v 2 ↔ c) → p`.
This is used to introduce assumptions about the first `n` values of `v` during reification. -/
def Valuation.implies (v : Valuation) (p : Prop) : List Prop → Nat → Prop
  | [], _ => p
  | a::as, n => (v n ↔ a) → v.implies p as (n+1)

/-- `Valuation.mk [a, b, c]` is a valuation which is `a` at 0, `b` at 1 and `c` at 2, and false
everywhere else. -/
```

### `Polynomial.lifts` (commanddeclaration) at `Mathlib/Data/Polynomial/Lifts.lean`
```lean
/-- We define the subsemiring of polynomials that lifts as the image of `RingHom.of (map f)`. -/
def lifts (f : R →+* S) : Subsemiring S[X] :=
  RingHom.rangeS (mapRingHom f)
```

### `Lean.Parser.Command.extends` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
def «extends»            := leading_parser
  " extends " >> sepBy1 termParser ", "
```

### `WeierstrassCurve.Affine.equation` (commanddeclaration) at `Mathlib/AlgebraicGeometry/EllipticCurve/Affine.lean`
```lean
/-- The proposition that an affine point $(x, y)$ lies in `W`. In other words, $W(x, y) = 0$. -/
@[pp_dot]
def equation (x y : R) : Prop :=
  (W.polynomial.eval <| C y).eval x = 0
```

### `Compactum.basic` (commanddeclaration) at `Mathlib/Topology/Category/Compactum.lean`
```lean
/-- A local definition used only in the proofs. -/
private def basic {X : Compactum} (A : Set X) : Set (Ultrafilter X) :=
  { F | A ∈ F }

/-- A local definition used only in the proofs. -/
```

### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Quot.lcInv` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Unsafe auxiliary constant used by the compiler to erase `Quot.lift`.
-/
unsafe axiom Quot.lcInv {α : Sort u} {r : α → α → Prop} (q : Quot r) : α

/--
Heterogeneous equality. `HEq a b` asserts that `a` and `b` have the same
type, and casting `a` across the equality yields `b`, and vice versa.

You should avoid using this type if you can. Heterogeneous equality does not
have all the same properties as `Eq`, because the assumption that the types of
`a` and `b` are equal is often too weak to prove theorems of interest. One
important non-theorem is the analogue of `congr`: If `HEq f g` and `HEq x y`
and `f x` and `g y` are well typed it does not follow that `HEq (f x) (g y)`.
(This does follow if you have `f = g` instead.) However if `a` and `b` have
the same type then `a = b` and `HEq a b` are equivalent.
-/
```

### `HEq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Heterogeneous equality. `HEq a b` asserts that `a` and `b` have the same
type, and casting `a` across the equality yields `b`, and vice versa.

You should avoid using this type if you can. Heterogeneous equality does not
have all the same properties as `Eq`, because the assumption that the types of
`a` and `b` are equal is often too weak to prove theorems of interest. One
important non-theorem is the analogue of `congr`: If `HEq f g` and `HEq x y`
and `f x` and `g y` are well typed it does not follow that `HEq (f x) (g y)`.
(This does follow if you have `f = g` instead.) However if `a` and `b` have
the same type then `a = b` and `HEq a b` are equivalent.
-/
inductive HEq : {α : Sort u} → α → {β : Sort u} → β → Prop where
  /-- Reflexivity of heterogeneous equality. -/
  | refl (a : α) : HEq a a

/-- A version of `HEq.refl` with an implicit argument. -/
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

### `Ordnode.Bounded.weak` (commanddeclaration) at `Mathlib/Data/Ordmap/Ordset.lean`
```lean
theorem Bounded.weak {t : Ordnode α} {o₁ o₂} (h : Bounded t o₁ o₂) : Bounded t ⊥ ⊤ :=
  h.weak_left.weak_right
```

### `Lean.Elab.Tactic.NormCast.prove` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Elab/Tactic/NormCast.lean`
```lean
/--
Discharging function used during simplification in the "squash" step.
-/
-- TODO: normCast takes a list of expressions to use as lemmas for the discharger
-- TODO: a tactic to print the results the discharger fails to prove
def prove (e : Expr) : SimpM (Option Expr) := do
  withTraceNode `Tactic.norm_cast (return m!"{exceptOptionEmoji ·} discharging: {e}") do
  return (← findLocalDeclWithType? e).map mkFVar

/--
Core rewriting function used in the "squash" step, which moves casts upwards
and eliminates them.

It tries to rewrite an expression using the elim and move lemmas.
On failure, it calls the splitting procedure heuristic.
-/
```

### `One` (commanddeclaration) at `Mathlib/Init/ZeroOne.lean`
```lean
@[to_additive]
class One (α : Type u) where
  one : α
```

### `congr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congr {α : Sort u} {β : Sort v} {f₁ f₂ : α → β} {a₁ a₂ : α} (h₁ : Eq f₁ f₂) (h₂ : Eq a₁ a₂) : Eq (f₁ a₁) (f₂ a₂) :=
  h₁ ▸ h₂ ▸ rfl

/-- Congruence in the function part of an application: If `f = g` then `f a = g a`. -/
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.Cocone` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Cones.lean`
```lean
/-- A `c : Cocone F` is
* an object `c.pt` and
* a natural transformation `c.ι : F ⟶ c.pt` from `F` to the constant `c.pt` functor.

For example, if the source `J` of `F` is a partially ordered set, then to give
`c : Cocone F` is to give a collection of morphisms `ιⱼ : F j ⟶ c.pt` and, for
all `j ≤ k` in `J`, morphisms `ιⱼₖ : F j ⟶ F k` such that `Fⱼₖ ≫ Fₖ = Fⱼ` for all `j ≤ k`.

`Cocone F` is equivalent, via `Cone.equiv` below, to `Σ X, F.cocones.obj X`.
-/
structure Cocone (F : J ⥤ C) where
  /-- An object of `C` -/
  pt : C
  /-- A natural transformation from `F` to the constant functor at `pt` -/
  ι : F ⟶ (const J).obj pt
```

### `CategoryTheory.Limits.IsColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
/-- A cocone `t` on `F` is a colimit cocone if each cocone on `F` admits a unique
cocone morphism from `t`.

See <https://stacks.math.columbia.edu/tag/002F>.
-/
-- Porting note: remove @[nolint has_nonempty_instance]
structure IsColimit (t : Cocone F) where
  /-- `t.pt` maps to all other cocone covertices -/
  desc : ∀ s : Cocone F, t.pt ⟶ s.pt
  /-- The map `desc` makes the diagram with the natural transformations commute -/
  fac : ∀ (s : Cocone F) (j : J), t.ι.app j ≫ desc s = s.ι.app j := by aesop_cat
  /-- `desc` is the unique such map -/
  uniq :
    ∀ (s : Cocone F) (m : t.pt ⟶ s.pt) (_ : ∀ j : J, t.ι.app j ≫ m = s.ι.app j), m = desc s := by
    aesop_cat
```

### `CategoryTheory.Limits.IsColimit.coconePointUniqueUpToIso` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
/-- Colimits of `F` are unique up to isomorphism. -/
def coconePointUniqueUpToIso {s t : Cocone F} (P : IsColimit s) (Q : IsColimit t) : s.pt ≅ t.pt :=
  (Cocones.forget F).mapIso (uniqueUpToIso P Q)
```

### `LLVM.Linkage.internal` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Compiler/IR/LLVMBindings.lean`
```lean
/-- Rename collisions when linking (static functions) -/
def Linkage.internal : Linkage := { val := 8 }
/-- Like Internal, but omit from symbol table -/
```

### `Nonempty.some` (commanddeclaration) at `Mathlib/Logic/Nonempty.lean`
```lean
/-- Using `Classical.choice`, extracts a term from a `Nonempty` type. -/
@[reducible]
protected noncomputable def Nonempty.some {α} (h : Nonempty α) : α :=
  Classical.choice h
```

### `CategoryTheory.Limits.Types.isColimit_iff_bijective_desc` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Types.lean`
```lean
theorem isColimit_iff_bijective_desc : Nonempty (IsColimit c) ↔ (Quot.desc c).Bijective := by
  classical
  refine ⟨?_, ?_⟩
  · refine fun ⟨hc⟩ => ⟨fun x y h => ?_, fun x => ?_⟩
    · let f : Quot F → ULift.{u} Bool := fun z => ULift.up (x = z)
      suffices f x = f y by simpa [f] using this
      rw [← Quot.desc_toCocone_desc c f hc x, h, Quot.desc_toCocone_desc]
    · let f₁ : c.pt ⟶ ULift.{u} Bool := fun _ => ULift.up true
      let f₂ : c.pt ⟶ ULift.{u} Bool := fun x => ULift.up (∃ a, Quot.desc c a = x)
      suffices f₁ = f₂ by simpa [f₁, f₂] using congrFun this x
      refine hc.hom_ext fun j => funext fun x => ?_
      simpa [f₁, f₂] using ⟨Quot.ι F j x, by simp⟩
  · refine fun h => ⟨?_⟩
    let e := Equiv.ofBijective _ h
    have h : ∀ j x, e.symm (c.ι.app j x) = Quot.ι F j x :=
      fun j x => e.injective (Equiv.ofBijective_apply_symm_apply _ _ _)
    exact
      { desc := fun s => Quot.desc s ∘ e.symm
        fac := fun s j => by
          ext x
          simp [h]
        uniq := fun s m hm => by
          ext x
          obtain ⟨x, rfl⟩ := e.surjective x
          obtain ⟨j, x, rfl⟩ := Quot.jointly_surjective x
          rw [← h, Equiv.apply_symm_apply]
          simpa [h] using congrFun (hm j) x }
```

### `equivShrink` (commanddeclaration) at `Mathlib/Logic/Small/Defs.lean`
```lean
/-- The noncomputable equivalence between a `w`-small type and a model.
-/
noncomputable def equivShrink (α : Type v) [Small.{w} α] : α ≃ Shrink α :=
  Nonempty.some (Classical.choose_spec (@Small.equiv_small α _))
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `Eq.trans` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Equality is transitive: if `a = b` and `b = c` then `a = c`.

Because this is in the `Eq` namespace, if you have variables or expressions
`h₁ : a = b` and `h₂ : b = c`, you can use `h₁.trans h₂ : a = c` as shorthand
for `Eq.trans h₁ h₂`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem Eq.trans {α : Sort u} {a b c : α} (h₁ : Eq a b) (h₂ : Eq b c) : Eq a c :=
  h₂ ▸ h₁

/--
Cast across a type equality. If `h : α = β` is an equality of types, and
`a : α`, then `a : β` will usually not typecheck directly, but this function
will allow you to work around this and embed `a` in type `β` as `cast h a : β`.

It is best to avoid this function if you can, because it is more complicated
to reason about terms containing casts, but if the types don't match up
definitionally sometimes there isn't anything better you can do.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```
