## Current goal
```
⊢ ∃ φ, φ { val := x, property := hx } = y
```

## Full tactic state
```
case intro
F : Type u_1
E : Type u_2
K : Type u_3
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Field K
inst✝¹ : Algebra F E
inst✝ : Algebra F K
S : Set E
hK : ∀ s ∈ S, IsIntegral F s ∧ Splits (algebraMap F K) (minpoly F s)
hK' : ∀ (s : E), IsIntegral F s ∧ Splits (algebraMap F K) (minpoly F s)
L : IntermediateField F E
f : ↥L →ₐ[F] K
hL : L ≤ adjoin F S
hS : adjoin F S = ⊤
x : E
hx : x ∈ adjoin F S
y : K
hy : (aeval y) (minpoly F x) = 0
ix : IsIntegral F ↑{ val := x, property := hx }
φ : ↥(adjoin F S) →ₐ[F] K
hφ : AlgHom.comp φ (inclusion ⋯) = (algHomAdjoinIntegralEquiv F ix).symm { val := y, property := ⋯ }
⊢ ∃ φ, φ { val := x, property := hx } = y
```

## Proof so far (3 tactics)
```lean
have ix := isAlgebraic_adjoin (fun s hs ↦ (hK s hs).1) ⟨x, hx⟩
rw [isAlgebraic_iff_isIntegral, isIntegral_iff] at ix
obtain ⟨φ, hφ⟩ := exists_algHom_adjoin_of_splits hK ((algHomAdjoinIntegralEquiv F ix).symm
  ⟨y, mem_aroots.mpr ⟨minpoly.ne_zero ix, hy⟩⟩) (adjoin_simple_le_iff.mpr hx)
```

## Theorem
`IntermediateField.exists_algHom_adjoin_of_splits_of_aeval` in `Mathlib/FieldTheory/Extension.lean`

## Premises used in the next tactic
- `DFunLike.congr_fun`
- `IntermediateField.AdjoinSimple.gen`
- `Eq.trans`
- `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen`

## Premise signatures
### `DFunLike.congr_fun` (commanddeclaration)
```lean
protected theorem congr_fun {f g : F} (h₁ : f = g) (x : α) : f x = g x
```

### `IntermediateField.AdjoinSimple.gen` (commanddeclaration)
```lean
def AdjoinSimple.gen : F⟮α⟯
```

### `Eq.trans` (commanddeclaration)
```lean
theorem Eq.trans {α : Sort u} {a b c : α} (h₁ : Eq a b) (h₂ : Eq b c) : Eq a c
```

### `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen` (lemma)
```lean
lemma algHomAdjoinIntegralEquiv_symm_apply_gen (h : IsIntegral F α)
    (x : { x // x ∈ (minpoly F α).aroots K }) :
    (algHomAdjoinIntegralEquiv F h).symm x (AdjoinSimple.gen F α) = x
```

## Premise full source (with proof)
### `DFunLike.congr_fun` (commanddeclaration) at `Mathlib/Data/FunLike/Basic.lean`
```lean
protected theorem congr_fun {f g : F} (h₁ : f = g) (x : α) : f x = g x :=
  congr_fun (congr_arg _ h₁) x
```

### `IntermediateField.AdjoinSimple.gen` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- generator of `F⟮α⟯` -/
def AdjoinSimple.gen : F⟮α⟯ :=
  ⟨α, mem_adjoin_simple_self F α⟩
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

### `IntermediateField.algHomAdjoinIntegralEquiv_symm_apply_gen` (lemma) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
lemma algHomAdjoinIntegralEquiv_symm_apply_gen (h : IsIntegral F α)
    (x : { x // x ∈ (minpoly F α).aroots K }) :
    (algHomAdjoinIntegralEquiv F h).symm x (AdjoinSimple.gen F α) = x :=
  (adjoin.powerBasis h).lift_gen x.val <| by
    rw [adjoin.powerBasis_gen, minpoly_gen]; exact (mem_aroots.mp x.2).2

/-- Fintype of algebra homomorphism `F⟮α⟯ →ₐ[F] K` -/
```

## Transitive premise context (1-hop, 20/20 premises, ≈2686 tokens)
### `congr_fun` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

### `Submodule.IsPrincipal.generator` (commanddeclaration) at `Mathlib/RingTheory/PrincipalIdealDomain.lean`
```lean
/-- `generator I`, if `I` is a principal submodule, is an `x ∈ M` such that `span R {x} = I` -/
noncomputable def generator (S : Submodule R M) [S.IsPrincipal] : M :=
  Classical.choose (principal S)
```

### `IntermediateField.mem_adjoin_simple_self` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
theorem mem_adjoin_simple_self : α ∈ F⟮α⟯ :=
  subset_adjoin F {α} (Set.mem_singleton α)
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

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `PSet.embed` (commanddeclaration) at `Mathlib/SetTheory/ZFC/Basic.lean`
```lean
/-- Embedding of one universe in another -/
@[nolint checkUnivs]
def embed : PSet.{max (u + 1) v} :=
  ⟨ULift.{v, u + 1} PSet, fun ⟨x⟩ => PSet.Lift.{u, max (u + 1) v} x⟩
```

### `cast` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Cast across a type equality. If `h : α = β` is an equality of types, and
`a : α`, then `a : β` will usually not typecheck directly, but this function
will allow you to work around this and embed `a` in type `β` as `cast h a : β`.

It is best to avoid this function if you can, because it is more complicated
to reason about terms containing casts, but if the types don't match up
definitionally sometimes there isn't anything better you can do.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
@[macro_inline] def cast {α β : Sort u} (h : Eq α β) (a : α) : β :=
  h.rec a

/--
Congruence in the function argument: if `a₁ = a₂` then `f a₁ = f a₂` for
any (nondependent) function `f`. This is more powerful than it might look at first, because
you can also use a lambda expression for `f` to prove that
`<something containing a₁> = <something containing a₂>`. This function is used
internally by tactics like `congr` and `simp` to apply equalities inside
subterms.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
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

### `Function.sometimes` (commanddeclaration) at `Mathlib/Logic/Function/Basic.lean`
```lean
/-- `sometimes f` evaluates to some value of `f`, if it exists. This function is especially
interesting in the case where `α` is a proposition, in which case `f` is necessarily a
constant function, so that `sometimes f = f a` for all `a`. -/
noncomputable def sometimes {α β} [Nonempty β] (f : α → β) : β :=
  if h : Nonempty α then f (Classical.choice h) else Classical.choice ‹_›
```

### `IsIntegral` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
/-- An element `x` of an algebra `A` over a commutative ring `R` is said to be *integral*,
if it is a root of some monic polynomial `p : R[X]`.
Equivalently, the element is integral over `R` with respect to the induced `algebraMap` -/
def IsIntegral (x : A) : Prop :=
  (algebraMap R A).IsIntegralElem x
```

### `minpoly` (commanddeclaration) at `Mathlib/FieldTheory/Minpoly/Basic.lean`
```lean
/-- Suppose `x : B`, where `B` is an `A`-algebra.

The minimal polynomial `minpoly A x` of `x`
is a monic polynomial with coefficients in `A` of smallest degree that has `x` as its root,
if such exists (`IsIntegral A x`) or zero otherwise.

For example, if `V` is a `𝕜`-vector space for some field `𝕜` and `f : V →ₗ[𝕜] V` then
the minimal polynomial of `f` is `minpoly 𝕜 f`.
-/
noncomputable def minpoly (x : B) : A[X] :=
  if hx : IsIntegral A x then degree_lt_wf.min _ hx else 0
```

### `Polynomial.aroots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
/-- Given a polynomial `p` with coefficients in a ring `T` and a `T`-algebra `S`, `aroots p S` is
the multiset of roots of `p` regarded as a polynomial over `S`. -/
noncomputable abbrev aroots (p : T[X]) (S) [CommRing S] [IsDomain S] [Algebra T S] : Multiset S :=
  (p.map (algebraMap T S)).roots
```

### `IntermediateField.algHomAdjoinIntegralEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- Algebra homomorphism `F⟮α⟯ →ₐ[F] K` are in bijection with the set of roots
of `minpoly α` in `K`. -/
noncomputable def algHomAdjoinIntegralEquiv (h : IsIntegral F α) :
    (F⟮α⟯ →ₐ[F] K) ≃ { x // x ∈ (minpoly F α).aroots K } :=
  (adjoin.powerBasis h).liftEquiv'.trans
    ((Equiv.refl _).subtypeEquiv fun x => by
      rw [adjoin.powerBasis_gen, minpoly_gen, Equiv.refl_apply])
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `PowerBasis.lift_gen` (commanddeclaration) at `Mathlib/RingTheory/PowerBasis.lean`
```lean
@[simp]
theorem lift_gen (pb : PowerBasis A S) (y : S') (hy : aeval y (minpoly A pb.gen) = 0) :
    pb.lift y hy pb.gen = y :=
  pb.constr_pow_gen hy
```

### `IntermediateField.minpoly_gen` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
theorem minpoly_gen (α : E) :
    minpoly F (AdjoinSimple.gen F α) = minpoly F α := by
  rw [← minpoly.algebraMap_eq (algebraMap F⟮α⟯ E).injective, AdjoinSimple.algebraMap_gen]
```

### `Fintype` (commanddeclaration) at `Mathlib/Data/Fintype/Basic.lean`
```lean
/-- `Fintype α` means that `α` is finite, i.e. there are only
  finitely many distinct elements of type `α`. The evidence of this
  is a finset `elems` (a list up to permutation without duplicates),
  together with a proof that everything of type `α` is in the list. -/
class Fintype (α : Type*) where
  /-- The `Finset` containing all elements of a `Fintype` -/
  elems : Finset α
  /-- A proof that `elems` contains every element of the type -/
  complete : ∀ x : α, x ∈ elems
```

### `Stream'.homomorphism` (commanddeclaration) at `Mathlib/Data/Stream/Init.lean`
```lean
theorem homomorphism (f : α → β) (a : α) : pure f ⊛ pure a = pure (f a) :=
  rfl
```
