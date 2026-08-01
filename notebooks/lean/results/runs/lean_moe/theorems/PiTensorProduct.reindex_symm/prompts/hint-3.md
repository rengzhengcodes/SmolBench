## Current goal
```
⊢ (LinearEquiv.symm (reindex R (fun x => M) e)) x = (reindex R (fun x => M) e.symm) x
```

## Full tactic state
```
case h
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝⁶ : (i : ι) → AddCommMonoid (s i)
inst✝⁵ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁴ : AddCommMonoid M
inst✝³ : Module R M
E : Type u_9
inst✝² : AddCommMonoid E
inst✝¹ : Module R E
F : Type u_10
inst✝ : AddCommMonoid F
e : ι ≃ ι₂
x : ⨂[R] (i : ι₂), M
⊢ (LinearEquiv.symm (reindex R (fun x => M) e)) x = (reindex R (fun x => M) e.symm) x
```

## Proof so far (1 tactic)
```lean
ext x
```

## Theorem
`PiTensorProduct.reindex_symm` in `Mathlib/LinearAlgebra/PiTensorProduct.lean`

## Premises used in the next tactic
- `PiTensorProduct.reindex`
- `MultilinearMap.domDomCongrLinearEquiv'`
- `LinearEquiv.coe_symm_mk`
- `LinearEquiv.coe_mk`
- `LinearEquiv.ofLinear_symm_apply`
- `Equiv.symm_symm_apply`
- `LinearEquiv.ofLinear_apply`
- `Equiv.piCongrLeft'_symm`

## Premise signatures
### `PiTensorProduct.reindex` (commanddeclaration)
```lean
def reindex (e : ι ≃ ι₂) : (⨂[R] i : ι, s i) ≃ₗ[R] ⨂[R] i : ι₂, s (e.symm i)
```

### `MultilinearMap.domDomCongrLinearEquiv'` (commanddeclaration)
```lean
@[simps apply symm_apply]
def domDomCongrLinearEquiv' {ι' : Type*} (σ : ι ≃ ι') :
    MultilinearMap R M₁ M₂ ≃ₗ[S] MultilinearMap R (fun i => M₁ (σ.symm i)) M₂ where
  toFun f
```

### `LinearEquiv.coe_symm_mk` (commanddeclaration)
```lean
@[simp]
theorem coe_symm_mk [Module R M] [Module R M₂]
    {to_fun inv_fun map_add map_smul left_inv right_inv} :
    ⇑(⟨⟨⟨to_fun, map_add⟩, map_smul⟩, inv_fun, left_inv, right_inv⟩ : M ≃ₗ[R] M₂).symm = inv_fun
```

### `LinearEquiv.coe_mk` (commanddeclaration)
```lean
@[simp]
theorem coe_mk {to_fun inv_fun map_add map_smul left_inv right_inv} :
    (⟨⟨⟨to_fun, map_add⟩, map_smul⟩, inv_fun, left_inv, right_inv⟩ : M ≃ₛₗ[σ] M₂) = to_fun
```

### `LinearEquiv.ofLinear_symm_apply` (commanddeclaration)
```lean
@[simp]
theorem ofLinear_symm_apply {h₁ h₂} (x : M₂) : (ofLinear f g h₁ h₂ : M ≃ₛₗ[σ₁₂] M₂).symm x = g x
```

### `Equiv.symm_symm_apply` (commanddeclaration)
```lean
@[simp, nolint simpNF] theorem symm_symm_apply (f : α ≃ β) (b : α) : f.symm.symm b = f b
```

### `LinearEquiv.ofLinear_apply` (commanddeclaration)
```lean
@[simp]
theorem ofLinear_apply {h₁ h₂} (x : M) : (ofLinear f g h₁ h₂ : M ≃ₛₗ[σ₁₂] M₂) x = f x
```

### `Equiv.piCongrLeft'_symm` (commanddeclaration)
```lean
@[simp]
theorem piCongrLeft'_symm (P : Sort*) (e : α ≃ β) :
    (piCongrLeft' (fun _ => P) e).symm = piCongrLeft' _ e.symm
```

## Premise full source (with proof)
### `PiTensorProduct.reindex` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- Re-index the components of the tensor power by `e`.-/
def reindex (e : ι ≃ ι₂) : (⨂[R] i : ι, s i) ≃ₗ[R] ⨂[R] i : ι₂, s (e.symm i) :=
  let f := domDomCongrLinearEquiv' R R s (⨂[R] (i : ι₂), s (e.symm i)) e
  let g := domDomCongrLinearEquiv' R R s (⨂[R] (i : ι), s i) e
  LinearEquiv.ofLinear (lift <| f.symm <| tprod R) (lift <| g <| tprod R)
    -- Adaptation note: v4.7.0-rc1
    -- An alternative here would be `aesop (simp_config := {zetaDelta := true})`
    -- or a wrapper macro to that effect.
    (by aesop (add norm simp [f, g]))
    (by aesop (add norm simp [f, g]))
```

### `MultilinearMap.domDomCongrLinearEquiv'` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
/-- The dependent version of `MultilinearMap.domDomCongrLinearEquiv`. -/
@[simps apply symm_apply]
def domDomCongrLinearEquiv' {ι' : Type*} (σ : ι ≃ ι') :
    MultilinearMap R M₁ M₂ ≃ₗ[S] MultilinearMap R (fun i => M₁ (σ.symm i)) M₂ where
  toFun f :=
    { toFun := f ∘ (σ.piCongrLeft' M₁).symm
      map_add' := fun m i => by
        letI := σ.decidableEq
        rw [← σ.apply_symm_apply i]
        intro x y
        simp only [comp_apply, piCongrLeft'_symm_update, f.map_add]
      map_smul' := fun m i c => by
        letI := σ.decidableEq
        rw [← σ.apply_symm_apply i]
        intro x
        simp only [Function.comp, piCongrLeft'_symm_update, f.map_smul] }
  invFun f :=
    { toFun := f ∘ σ.piCongrLeft' M₁
      map_add' := fun m i => by
        letI := σ.symm.decidableEq
        rw [← σ.symm_apply_apply i]
        intro x y
        simp only [comp_apply, piCongrLeft'_update, f.map_add]
      map_smul' := fun m i c => by
        letI := σ.symm.decidableEq
        rw [← σ.symm_apply_apply i]
        intro x
        simp only [Function.comp, piCongrLeft'_update, f.map_smul] }
  map_add' f₁ f₂ := by
    ext
    simp only [Function.comp, coe_mk, add_apply]
  map_smul' c f := by
    ext
    simp only [Function.comp, coe_mk, smul_apply, RingHom.id_apply]
  left_inv f := by
    ext
    simp only [coe_mk, comp_apply, Equiv.symm_apply_apply]
  right_inv f := by
    ext
    simp only [coe_mk, comp_apply, Equiv.apply_symm_apply]
```

### `LinearEquiv.coe_symm_mk` (commanddeclaration) at `Mathlib/Algebra/Module/Equiv.lean`
```lean
@[simp]
theorem coe_symm_mk [Module R M] [Module R M₂]
    {to_fun inv_fun map_add map_smul left_inv right_inv} :
    ⇑(⟨⟨⟨to_fun, map_add⟩, map_smul⟩, inv_fun, left_inv, right_inv⟩ : M ≃ₗ[R] M₂).symm = inv_fun :=
  rfl
```

### `LinearEquiv.coe_mk` (commanddeclaration) at `Mathlib/Algebra/Module/Equiv.lean`
```lean
@[simp]
theorem coe_mk {to_fun inv_fun map_add map_smul left_inv right_inv} :
    (⟨⟨⟨to_fun, map_add⟩, map_smul⟩, inv_fun, left_inv, right_inv⟩ : M ≃ₛₗ[σ] M₂) = to_fun := rfl
```

### `LinearEquiv.ofLinear_symm_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
@[simp]
theorem ofLinear_symm_apply {h₁ h₂} (x : M₂) : (ofLinear f g h₁ h₂ : M ≃ₛₗ[σ₁₂] M₂).symm x = g x :=
  rfl
```

### `Equiv.symm_symm_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
@[simp, nolint simpNF] theorem symm_symm_apply (f : α ≃ β) (b : α) : f.symm.symm b = f b := rfl
```

### `LinearEquiv.ofLinear_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
@[simp]
theorem ofLinear_apply {h₁ h₂} (x : M) : (ofLinear f g h₁ h₂ : M ≃ₛₗ[σ₁₂] M₂) x = f x :=
  rfl
```

### `Equiv.piCongrLeft'_symm` (commanddeclaration) at `Mathlib/Logic/Equiv/Basic.lean`
```lean
/-- This lemma is impractical to state in the dependent case. -/
@[simp]
theorem piCongrLeft'_symm (P : Sort*) (e : α ≃ β) :
    (piCongrLeft' (fun _ => P) e).symm = piCongrLeft' _ e.symm := by ext; simp [piCongrLeft']

/-- Note: the "obvious" statement `(piCongrLeft' P e).symm g a = g (e a)` doesn't typecheck: the
LHS would have type `P a` while the RHS would have type `P (e.symm (e a))`. This lemma is a way
around it in the case where `a` is of the form `e.symm b`, so we can use `g b` instead of
`g (e (e.symm b))`. -/
```

## Transitive premise context (1-hop, 17/17 premises, ≈4237 tokens)
### `LinearEquiv.ofLinear` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
/-- If a linear map has an inverse, it is a linear equivalence. -/
def ofLinear (h₁ : f.comp g = LinearMap.id) (h₂ : g.comp f = LinearMap.id) : M ≃ₛₗ[σ₁₂] M₂ :=
  { f with
    invFun := g
    left_inv := LinearMap.ext_iff.1 h₂
    right_inv := LinearMap.ext_iff.1 h₁ }
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

### `Lake.Manifest.version` (commanddeclaration) at `.lake/packages/lean4/src/lean/lake/Lake/Load/Manifest.lean`
```lean
/-- Current version of the manifest format. -/
def Manifest.version : Nat := 7

/-- An entry for a package stored in the manifest. -/
```

### `MultilinearMap.domDomCongrLinearEquiv` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
/-- `MultilinearMap.domDomCongr` as a `LinearEquiv`. -/
@[simps apply symm_apply]
def domDomCongrLinearEquiv {ι₁ ι₂} (σ : ι₁ ≃ ι₂) :
    MultilinearMap R (fun _ : ι₁ => M₂) M₃ ≃ₗ[S] MultilinearMap R (fun _ : ι₂ => M₂) M₃ :=
  { (domDomCongrEquiv σ :
      MultilinearMap R (fun _ : ι₁ => M₂) M₃ ≃+ MultilinearMap R (fun _ : ι₂ => M₂) M₃) with
    map_smul' := fun c f => by
      ext
      simp [MultilinearMap.domDomCongr] }
```

### `MultilinearMap` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
/-- Multilinear maps over the ring `R`, from `∀ i, M₁ i` to `M₂` where `M₁ i` and `M₂` are modules
over `R`. -/
structure MultilinearMap (R : Type uR) {ι : Type uι} (M₁ : ι → Type v₁) (M₂ : Type v₂) [Semiring R]
  [∀ i, AddCommMonoid (M₁ i)] [AddCommMonoid M₂] [∀ i, Module R (M₁ i)] [Module R M₂] where
  /-- The underlying multivariate function of a multilinear map. -/
  toFun : (∀ i, M₁ i) → M₂
  /-- A multilinear map is additive in every argument. -/
  map_add' :
    ∀ [DecidableEq ι] (m : ∀ i, M₁ i) (i : ι) (x y : M₁ i),
      toFun (update m i (x + y)) = toFun (update m i x) + toFun (update m i y)
  /-- A multilinear map is compatible with scalar multiplication in every argument. -/
  map_smul' :
    ∀ [DecidableEq ι] (m : ∀ i, M₁ i) (i : ι) (c : R) (x : M₁ i),
      toFun (update m i (c • x)) = c • toFun (update m i x)
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Lean.Parser.Term.letI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «letI» := leading_parser
  withPosition ("letI " >> haveDecl) >> optSemicolon termParser
```

### `Function.piCongrLeft'_symm_update` (commanddeclaration) at `Mathlib/Logic/Equiv/Basic.lean`
```lean
theorem piCongrLeft'_symm_update [DecidableEq α] [DecidableEq β] (P : α → Sort*) (e : α ≃ β)
    (f : ∀ b, P (e.symm b)) (b : β) (x : P (e.symm b)) :
    (e.piCongrLeft' P).symm (update f b x) = update ((e.piCongrLeft' P).symm f) (e.symm b) x := by
  simp [(e.piCongrLeft' P).symm_apply_eq, piCongrLeft'_update]
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

### `Function.piCongrLeft'_update` (commanddeclaration) at `Mathlib/Logic/Equiv/Basic.lean`
```lean
theorem piCongrLeft'_update [DecidableEq α] [DecidableEq β] (P : α → Sort*) (e : α ≃ β)
    (f : ∀ a, P a) (b : β) (x : P (e.symm b)) :
    e.piCongrLeft' P (update f (e.symm b) x) = update (e.piCongrLeft' P f) b x := by
  ext b'
  rcases eq_or_ne b' b with (rfl | h)
  · simp
  · simp only [Equiv.piCongrLeft'_apply, ne_eq, h, not_false_iff, update_noteq]
    rw [update_noteq _]
    rw [ne_eq]
    intro h'
    /- an example of something that should work, or also putting `EmbeddingLike.apply_eq_iff_eq`
      in the `simp` should too:
    have := (EmbeddingLike.apply_eq_iff_eq e).mp h' -/
    cases e.symm.injective h' |> h
```

### `RingHom.id_apply` (commanddeclaration) at `Mathlib/Algebra/Ring/Hom/Defs.lean`
```lean
@[simp]
theorem id_apply (x : α) : RingHom.id α x = x :=
  rfl
```

### `Equiv.symm_apply_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
@[simp] theorem symm_apply_apply (e : α ≃ β) (x : α) : e.symm (e x) = x := e.left_inv x
```

### `Equiv.apply_symm_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
@[simp] theorem apply_symm_apply (e : α ≃ β) (x : β) : e (e.symm x) = x := e.right_inv x
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

### `Std.Tactic.Lint.simpNF` (commanddeclaration) at `.lake/packages/std/Std/Tactic/Lint/Simp.lean`
```lean
/-- A linter for simp lemmas whose lhs is not in simp-normal form, and which hence never fire. -/
@[std_linter] def simpNF : Linter where
  noErrorsFound := "All left-hand sides of simp lemmas are in simp-normal form."
  errorsFound := "SOME SIMP LEMMAS ARE NOT IN SIMP-NORMAL FORM.
see note [simp-normal form] for tips how to debug this.
https://leanprover-community.github.io/mathlib_docs/notes.html#simp-normal%20form"
  test := fun declName => do
    unless ← isSimpTheorem declName do return none
    let ctx := { ← Simp.Context.mkDefault with config.decide := false }
    checkAllSimpTheoremInfos (← getConstInfo declName).type fun {lhs, rhs, isConditional, ..} => do
      let ({ expr := lhs', proof? := prf1, .. }, prf1Lems) ←
        decorateError "simplify fails on left-hand side:" <| simp lhs ctx
      if prf1Lems.contains (.decl declName) then return none
      let ({ expr := rhs', .. }, used_lemmas) ←
        decorateError "simplify fails on right-hand side:" <| simp rhs ctx (usedSimps := prf1Lems)
      let lhs'EqRhs' ← isSimpEq lhs' rhs' (whnfFirst := false)
      let lhsInNF ← isSimpEq lhs' lhs
      if lhs'EqRhs' then
        if prf1.isNone then return none -- TODO: FP rewriting foo.eq_2 using `simp only [foo]`
        return m!"simp can prove this:
  by {← formatLemmas used_lemmas}
One of the lemmas above could be a duplicate.
If that's not the case try reordering lemmas or adding @[priority].
"
      else if ¬ lhsInNF then
        return m!"Left-hand side simplifies from
  {lhs}
to
  {lhs'}
using
  {← formatLemmas prf1Lems}
Try to change the left-hand side to the simplified term!
"
      else if !isConditional && lhs == lhs' then
        return m!"Left-hand side does not simplify, when using the simp lemma on itself.
This usually means that it will never apply.
"
      else
        return none

library_note "simp-normal form" /--
This note gives you some tips to debug any errors that the simp-normal form linter raises.

The reason that a lemma was considered faulty is because its left-hand side is not in simp-normal
form.
These lemmas are hence never used by the simplifier.

This linter gives you a list of other simp lemmas: look at them!

Here are some tips depending on the error raised by the linter:

  1. 'the left-hand side reduces to XYZ':
     you should probably use XYZ as the left-hand side.

  2. 'simp can prove this':
     This typically means that lemma is a duplicate, or is shadowed by another lemma:

     2a. Always put more general lemmas after specific ones:
      ```
      @[simp] lemma zero_add_zero : 0 + 0 = 0 := rfl
      @[simp] lemma add_zero : x + 0 = x := rfl
      ```

      And not the other way around!  The simplifier always picks the last matching lemma.

     2b. You can also use `@[priority]` instead of moving simp-lemmas around in the file.

      Tip: the default priority is 1000.
      Use `@[priority 1100]` instead of moving a lemma down,
      and `@[priority 900]` instead of moving a lemma up.

     2c. Conditional simp lemmas are tried last. If they are shadowed
         just remove the `simp` attribute.

     2d. If two lemmas are duplicates, the linter will complain about the first one.
         Try to fix the second one instead!
         (You can find it among the other simp lemmas the linter prints out!)

  3. 'try_for tactic failed, timeout':
     This typically means that there is a loop of simp lemmas.
     Try to apply squeeze_simp to the right-hand side (removing this lemma from the simp set) to see
     what lemmas might be causing the loop.

     Another trick is to `set_option trace.simplify.rewrite true` and
     then apply `try_for 10000 { simp }` to the right-hand side.  You will
     see a periodic sequence of lemma applications in the trace message.
-/

/--
A linter for simp lemmas whose lhs has a variable as head symbol,
and which hence never fire.
-/
```

### `LieAlgebra.Orthogonal.so` (commanddeclaration) at `Mathlib/Algebra/Lie/Classical.lean`
```lean
/-- The definite orthogonal Lie subalgebra: skew-adjoint matrices with respect to the symmetric
bilinear form defined by the identity matrix. -/
def so [Fintype n] : LieSubalgebra R (Matrix n n R) :=
  skewAdjointMatricesLieSubalgebra (1 : Matrix n n R)
```
