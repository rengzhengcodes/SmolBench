## Current goal
```
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁵ : Field F
inst✝⁴ : Field E
inst✝³ : Algebra F E
K : Type w
inst✝² : Field K
inst✝¹ : Algebra F K
q n : ℕ
hF : ExpChar F q
ι : Type u_1
v : ι → E
inst✝ : IsSeparable F E
h : ∀ (s : Finset ι), LinearIndependent F (v ∘ Subtype.val)
halg : Algebra.IsAlgebraic F E
s : Finset ι
E' : IntermediateField F E := adjoin F ↑(Finset.image v s)
this✝ : FiniteDimensional F ↥E'
this : IsSeparable F ↥E'
v' : { x // x ∈ s } → ↥E' := fun i => { val := v ↑i, property := ⋯ }
h' : LinearIndependent F v'
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```

## Proof so far (9 tactics)
```lean
classical
have halg := IsSeparable.isAlgebraic F E
rw [linearIndependent_iff_finset_linearIndependent] at h ⊢
intro s
let E' := adjoin F (s.image v : Set E)
haveI : FiniteDimensional F E' := finiteDimensional_adjoin fun x _ ↦ (halg x).isIntegral
haveI : IsSeparable F E' := isSeparable_tower_bot_of_isSeparable F E' E
let v' (i : s) : E' := ⟨v i.1, subset_adjoin F _ (Finset.mem_image.2 ⟨i.1, i.2, rfl⟩)⟩
have h' : LinearIndependent F v' := (h s).of_comp E'.val.toLinearMap
exact (h'.map_pow_expChar_pow_of_fd_isSeparable q n).map'
  E'.val.toLinearMap (LinearMap.ker_eq_bot_of_injective E'.val.injective)
have halg := IsSeparable.isAlgebraic F E
rw [linearIndependent_iff_finset_linearIndependent] at h ⊢
intro s
let E' := adjoin F (s.image v : Set E)
haveI : FiniteDimensional F E' := finiteDimensional_adjoin fun x _ ↦ (halg x).isIntegral
haveI : IsSeparable F E' := isSeparable_tower_bot_of_isSeparable F E' E
let v' (i : s) : E' := ⟨v i.1, subset_adjoin F _ (Finset.mem_image.2 ⟨i.1, i.2, rfl⟩)⟩
have h' : LinearIndependent F v' := (h s).of_comp E'.val.toLinearMap
```

## Theorem
`LinearIndependent.map_pow_expChar_pow_of_isSeparable` in `Mathlib/FieldTheory/PurelyInseparable.lean`

## Premises used in the next tactic
- `LinearIndependent.map'`
- `LinearMap.ker_eq_bot_of_injective`

## Premise signatures
### `LinearIndependent.map'` (commanddeclaration)
```lean
theorem LinearIndependent.map' (hv : LinearIndependent R v) (f : M →ₗ[R] M')
    (hf_inj : LinearMap.ker f = ⊥) : LinearIndependent R (f ∘ v)
```

### `LinearMap.ker_eq_bot_of_injective` (commanddeclaration)
```lean
theorem ker_eq_bot_of_injective {f : F} (hf : Injective f) : ker f = ⊥
```

## Premise full source (with proof)
### `LinearIndependent.map'` (commanddeclaration) at `Mathlib/LinearAlgebra/LinearIndependent.lean`
```lean
/-- An injective linear map sends linearly independent families of vectors to linearly independent
families of vectors. See also `LinearIndependent.map` for a more general statement. -/
theorem LinearIndependent.map' (hv : LinearIndependent R v) (f : M →ₗ[R] M')
    (hf_inj : LinearMap.ker f = ⊥) : LinearIndependent R (f ∘ v) :=
  hv.map <| by simp [hf_inj]
```

### `LinearMap.ker_eq_bot_of_injective` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
theorem ker_eq_bot_of_injective {f : F} (hf : Injective f) : ker f = ⊥ := by
  have : Disjoint ⊤ (ker f) := by
    -- Porting note: `← map_zero f` should work here, but it needs to be directly applied to H.
    rw [disjoint_ker]
    intros _ _ H
    rw [← map_zero f] at H
    exact hf H
  simpa [disjoint_iff_inf_le]
```

## Transitive premise context (1-hop, 9/9 premises, ≈1951 tokens)
### `LinearIndependent.map` (commanddeclaration) at `Mathlib/LinearAlgebra/LinearIndependent.lean`
```lean
/-- If `v` is a linearly independent family of vectors and the kernel of a linear map `f` is
disjoint with the submodule spanned by the vectors of `v`, then `f ∘ v` is a linearly independent
family of vectors. See also `LinearIndependent.map'` for a special case assuming `ker f = ⊥`. -/
theorem LinearIndependent.map (hv : LinearIndependent R v) {f : M →ₗ[R] M'}
    (hf_inj : Disjoint (span R (range v)) (LinearMap.ker f)) : LinearIndependent R (f ∘ v) := by
  rw [disjoint_iff_inf_le, ← Set.image_univ, Finsupp.span_image_eq_map_total,
    map_inf_eq_map_inf_comap, map_le_iff_le_comap, comap_bot, Finsupp.supported_univ, top_inf_eq]
      at hf_inj
  unfold LinearIndependent at hv ⊢
  rw [hv, le_bot_iff] at hf_inj
  haveI : Inhabited M := ⟨0⟩
  rw [Finsupp.total_comp, Finsupp.lmapDomain_total _ _ f, LinearMap.ker_comp,
    hf_inj]
  exact fun _ => rfl
```

### `LinearIndependent` (commanddeclaration) at `Mathlib/LinearAlgebra/LinearIndependent.lean`
```lean
/-- `LinearIndependent R v` states the family of vectors `v` is linearly independent over `R`. -/
def LinearIndependent : Prop :=
  LinearMap.ker (Finsupp.total ι M R v) = ⊥
```

### `LinearMap.ker` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
/-- The kernel of a linear map `f : M → M₂` is defined to be `comap f ⊥`. This is equivalent to the
set of `x : M` such that `f x = 0`. The kernel is a submodule of `M`. -/
def ker (f : F) : Submodule R M :=
  comap f ⊥
```

### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `Disjoint` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
/-- Two elements of a lattice are disjoint if their inf is the bottom element.
  (This generalizes disjoint sets, viewed as members of the subset lattice.)

Note that we define this without reference to `⊓`, as this allows us to talk about orders where
the infimum is not unique, or where implementing `Inf` would require additional `Decidable`
arguments. -/
def Disjoint (a b : α) : Prop :=
  ∀ ⦃x⦄, x ≤ a → x ≤ b → x ≤ ⊥
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

### `LinearMap.disjoint_ker` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
theorem disjoint_ker {f : F} {p : Submodule R M} :
    Disjoint p (ker f) ↔ ∀ x ∈ p, f x = 0 → x = 0 := by
  simp [disjoint_def]
```

### `disjoint_iff_inf_le` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem disjoint_iff_inf_le : Disjoint a b ↔ a ⊓ b ≤ ⊥ :=
  ⟨fun hd ↦ hd inf_le_left inf_le_right, fun h _ ha hb ↦ (le_inf ha hb).trans h⟩
```
