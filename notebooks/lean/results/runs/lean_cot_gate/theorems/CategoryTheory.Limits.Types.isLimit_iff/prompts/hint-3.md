## Current goal
```
⊢ IsLimit c
```

## Full tactic state
```
case refine_2
J : Type v
inst✝ : Category.{w, v} J
F : J ⥤ Type u
c : Cone F
h : ∀ s ∈ Functor.sections F, ∃! x, ∀ (j : J), c.π.app j x = s j
x : (c_1 : Cone F) → c_1.pt → c.pt
hx :
  ∀ (c_1 : Cone F) (y : c_1.pt),
    (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) (x c_1 y) ∧
      ∀ (y_1 : c.pt), (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) y_1 → y_1 = x c_1 y
⊢ IsLimit c
```

## Proof so far (4 tactics)
```lean
refine ⟨fun ⟨t⟩ s hs ↦ ?_, fun h ↦ ⟨?_⟩⟩
let cs := coneOfSection hs
exact ⟨t.lift cs ⟨⟩, fun j ↦ congr_fun (t.fac cs j) ⟨⟩,
  fun x hx ↦ congr_fun (t.uniq cs (fun _ ↦ x) fun j ↦ funext fun _ ↦ hx j) ⟨⟩⟩
choose x hx using fun c y ↦ h _ (sectionOfCone c y).2
```

## Theorem
`CategoryTheory.Limits.Types.isLimit_iff` in `Mathlib/CategoryTheory/Limits/Types.lean`

## Premises used in the next tactic
- `funext`
- `funext`
- `congr_fun`

## Premise signatures
### `funext` (commanddeclaration)
```lean
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g
```

### `funext` (commanddeclaration)
```lean
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g
```

### `congr_fun` (stdtacticaliasalias)
```lean
alias congr_fun
```

## Premise full source (with proof)
### `funext` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
**Function extensionality** is the statement that if two functions take equal values
every point, then the functions themselves are equal: `(∀ x, f x = g x) → f = g`.
It is called "extensionality" because it talks about how to prove two objects are equal
based on the properties of the object (compare with set extensionality,
which is `(∀ x, x ∈ s ↔ x ∈ t) → s = t`).

This is often an axiom in dependent type theory systems, because it cannot be proved
from the core logic alone. However in lean's type theory this follows from the existence
of quotient types (note the `Quot.sound` in the proof, as well as the `show` line
which makes use of the definitional equality `Quot.lift f h (Quot.mk x) = f x`).
-/
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g := by
  let eqv (f g : (x : α) → β x) := ∀ x, f x = g x
  let extfunApp (f : Quot eqv) (x : α) : β x :=
    Quot.liftOn f
      (fun (f : ∀ (x : α), β x) => f x)
      (fun _ _ h => h x)
  show extfunApp (Quot.mk eqv f) = extfunApp (Quot.mk eqv g)
  exact congrArg extfunApp (Quot.sound h)
```

### `funext` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
**Function extensionality** is the statement that if two functions take equal values
every point, then the functions themselves are equal: `(∀ x, f x = g x) → f = g`.
It is called "extensionality" because it talks about how to prove two objects are equal
based on the properties of the object (compare with set extensionality,
which is `(∀ x, x ∈ s ↔ x ∈ t) → s = t`).

This is often an axiom in dependent type theory systems, because it cannot be proved
from the core logic alone. However in lean's type theory this follows from the existence
of quotient types (note the `Quot.sound` in the proof, as well as the `show` line
which makes use of the definitional equality `Quot.lift f h (Quot.mk x) = f x`).
-/
theorem funext {α : Sort u} {β : α → Sort v} {f g : (x : α) → β x}
    (h : ∀ x, f x = g x) : f = g := by
  let eqv (f g : (x : α) → β x) := ∀ x, f x = g x
  let extfunApp (f : Quot eqv) (x : α) : β x :=
    Quot.liftOn f
      (fun (f : ∀ (x : α), β x) => f x)
      (fun _ _ h => h x)
  show extfunApp (Quot.mk eqv f) = extfunApp (Quot.mk eqv g)
  exact congrArg extfunApp (Quot.sound h)
```

### `congr_fun` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

## Transitive premise context (1-hop, 9/9 premises, ≈3579 tokens)
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

### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `Quot.sound` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
The **quotient axiom**, or at least the nontrivial part of the quotient
axiomatization. Quotient types are introduced by the `init_quot` command
in `Init.Prelude` which introduces the axioms:

```
opaque Quot {α : Sort u} (r : α → α → Prop) : Sort u

opaque Quot.mk {α : Sort u} (r : α → α → Prop) (a : α) : Quot r

opaque Quot.lift {α : Sort u} {r : α → α → Prop} {β : Sort v} (f : α → β) :
  (∀ a b : α, r a b → f a = f b) → Quot r → β

opaque Quot.ind {α : Sort u} {r : α → α → Prop} {β : Quot r → Prop} :
  (∀ a : α, β (Quot.mk r a)) → ∀ q : Quot r, β q
```
All of these axioms are true if we assume `Quot α r = α` and `Quot.mk` and
`Quot.lift` are identity functions, so they do not add much. However this axiom
cannot be explained in that way (it is false for that interpretation), so the
real power of quotient types come from this axiom.

It says that the quotient by `r` maps elements which are related by `r` to equal
values in the quotient. Together with `Quot.lift` which says that functions
which respect `r` can be lifted to functions on the quotient, we can deduce that
`Quot α r` exactly consists of the equivalence classes with respect to `r`.

It is important to note that `r` need not be an equivalence relation in this axiom.
When `r` is not an equivalence relation, we are actually taking a quotient with
respect to the equivalence relation generated by `r`.
-/
axiom sound : ∀ {α : Sort u} {r : α → α → Prop} {a b : α}, r a b → Quot.mk r a = Quot.mk r b
```

### `ProofWidgets.Svg.line` (commanddeclaration) at `.lake/packages/proofwidgets/ProofWidgets/Data/Svg.lean`
```lean
  def line {f} (p q : Point f) : Element f := { shape := .line p q }
  def circle {f} (c : Point f) (r : Size f) : Element f := { shape := .circle c r }
  def polyline {f} (pts : Array (Point f)) : Element f := { shape := .polyline pts }
  def polygon {f} (pts : Array (Point f)) : Element f := { shape := .polygon pts }
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

### `Quot.liftOn` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`Quot.liftOn q f h` is the same as `Quot.lift f h q`. It just reorders
the argument `q : Quot r` to be first.
-/
protected abbrev liftOn {α : Sort u} {β : Sort v} {r : α → α → Prop}
  (q : Quot r) (f : α → β) (c : (a b : α) → r a b → f a = f b) : β :=
  lift f c q
```

### `congrArg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in the function argument: if `a₁ = a₂` then `f a₁ = f a₂` for
any (nondependent) function `f`. This is more powerful than it might look at first, because
you can also use a lambda expression for `f` to prove that
`<something containing a₁> = <something containing a₂>`. This function is used
internally by tactics like `congr` and `simp` to apply equalities inside
subterms.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congrArg {α : Sort u} {β : Sort v} {a₁ a₂ : α} (f : α → β) (h : Eq a₁ a₂) : Eq (f a₁) (f a₂) :=
  h ▸ rfl

/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```

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
