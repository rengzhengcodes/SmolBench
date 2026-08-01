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
