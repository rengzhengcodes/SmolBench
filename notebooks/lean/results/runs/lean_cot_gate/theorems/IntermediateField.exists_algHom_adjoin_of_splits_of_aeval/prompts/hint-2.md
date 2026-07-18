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
