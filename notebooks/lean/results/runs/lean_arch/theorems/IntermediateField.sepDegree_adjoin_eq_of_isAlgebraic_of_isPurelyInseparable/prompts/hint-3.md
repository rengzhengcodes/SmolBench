## Current goal
```
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁷ : Field F
inst✝⁶ : Field E
inst✝⁵ : Algebra F E
K : Type w
inst✝⁴ : Field K
inst✝³ : Algebra F K
inst✝² : Algebra E K
inst✝¹ : IsScalarTower F E K
S : Set K
inst✝ : IsPurelyInseparable F E
M : IntermediateField F K := adjoin F S
halg : Algebra.IsAlgebraic F ↥M
L : IntermediateField E K := adjoin E S
E' : IntermediateField F K := AlgHom.fieldRange (IsScalarTower.toAlgHom F E K)
j : E ≃ₐ[F] ↥E' := AlgEquiv.ofInjectiveField (IsScalarTower.toAlgHom F E K)
hi : M ≤ restrictScalars F L
i : ↥M →+* ↥L := Subsemiring.inclusion hi
this✝¹ : Algebra ↥M ↥L := RingHom.toAlgebra i
this✝ : SMul ↥M ↥L := Algebra.toSMul
this : IsScalarTower F ↥M ↥L
q : ℕ
h✝ : ExpChar F q
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```

## Proof so far (23 tactics)
```lean
set M := adjoin F S
set L := adjoin E S
let E' := (IsScalarTower.toAlgHom F E K).fieldRange
let j : E ≃ₐ[F] E' := AlgEquiv.ofInjectiveField (IsScalarTower.toAlgHom F E K)
have hi : M ≤ L.restrictScalars F := by
  rw [restrictScalars_adjoin_of_algEquiv (E := K) j rfl, restrictScalars_adjoin]
  exact adjoin.mono _ _ _ (Set.subset_union_right _ _)
let i : M →+* L := Subsemiring.inclusion hi
letI : Algebra M L := i.toAlgebra
letI : SMul M L := Algebra.toSMul
haveI : IsScalarTower F M L := IsScalarTower.of_algebraMap_eq (congrFun rfl)
haveI : IsPurelyInseparable M L := by
  change IsPurelyInseparable M (extendScalars hi)
  obtain ⟨q, _⟩ := ExpChar.exists F
  have : extendScalars hi = adjoin M (E' : Set K) := restrictScalars_injective F <| by
    conv_lhs => rw [extendScalars_restrictScalars, restrictScalars_adjoin_of_algEquiv
      (E := K) j rfl, ← adjoin_self F E', adjoin_adjoin_comm]
  rw [this, isPurelyInseparable_adjoin_iff_pow_mem _ _ q]
  rintro x ⟨y, hy⟩
  obtain ⟨n, z, hz⟩ := IsPurelyInseparable.pow_mem F q y
  refine ⟨n, algebraMap F M z, ?_⟩
  rw [← IsScalarTower.algebraMap_apply, IsScalarTower.algebraMap_apply F E K, hz, ← hy, map_pow,
    AlgHom.toRingHom_eq_coe, IsScalarTower.coe_toAlgHom]
have h := lift_sepDegree_mul_lift_sepDegree_of_isAlgebraic F E L
  (IsPurelyInseparable.isAlgebraic F E)
rw [IsPurelyInseparable.sepDegree_eq_one F E, Cardinal.lift_one, one_mul] at h
rw [Cardinal.lift_injective h, ← sepDegree_mul_sepDegree_of_isAlgebraic F M L halg,
  IsPurelyInseparable.sepDegree_eq_one M L, mul_one]
rw [restrictScalars_adjoin_of_algEquiv (E := K) j rfl, restrictScalars_adjoin]
exact adjoin.mono _ _ _ (Set.subset_union_right _ _)
change IsPurelyInseparable M (extendScalars hi)
obtain ⟨q, _⟩ := ExpChar.exists F
have : extendScalars hi = adjoin M (E' : Set K) := restrictScalars_injective F <| by
  conv_lhs => rw [extendScalars_restrictScalars, restrictScalars_adjoin_of_algEquiv
    (E := K) j rfl, ← adjoin_self F E', adjoin_adjoin_comm]
rw [this, isPurelyInseparable_adjoin_iff_pow_mem _ _ q]
rintro x ⟨y, hy⟩
obtain ⟨n, z, hz⟩ := IsPurelyInseparable.pow_mem F q y
refine ⟨n, algebraMap F M z, ?_⟩
rw [← IsScalarTower.algebraMap_apply, IsScalarTower.algebraMap_apply F E K, hz, ← hy, map_pow,
  AlgHom.toRingHom_eq_coe, IsScalarTower.coe_toAlgHom]
```

## Theorem
`IntermediateField.sepDegree_adjoin_eq_of_isAlgebraic_of_isPurelyInseparable` in `Mathlib/FieldTheory/PurelyInseparable.lean`

## Premises used in the next tactic
- `IntermediateField.extendScalars_restrictScalars`
- `IntermediateField.restrictScalars_adjoin_of_algEquiv`
- `rfl`
- `IntermediateField.adjoin_self`
- `IntermediateField.adjoin_adjoin_comm`

## Premise signatures
### `IntermediateField.extendScalars_restrictScalars` (commanddeclaration)
```lean
@[simp]
theorem extendScalars_restrictScalars : (extendScalars h).restrictScalars K = E
```

### `IntermediateField.restrictScalars_adjoin_of_algEquiv` (commanddeclaration)
```lean
theorem restrictScalars_adjoin_of_algEquiv
    {L L' : Type*} [Field L] [Field L']
    [Algebra F L] [Algebra L E] [Algebra F L'] [Algebra L' E]
    [IsScalarTower F L E] [IsScalarTower F L' E] (i : L ≃ₐ[F] L')
    (hi : algebraMap L E = (algebraMap L' E) ∘ i) (S : Set E) :
    (adjoin L S).restrictScalars F = (adjoin L' S).restrictScalars F
```

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

### `IntermediateField.adjoin_self` (commanddeclaration)
```lean
@[simp]
theorem adjoin_self (K : IntermediateField F E) :
    adjoin F K = K
```

### `IntermediateField.adjoin_adjoin_comm` (commanddeclaration)
```lean
theorem adjoin_adjoin_comm (T : Set E) :
    (adjoin (adjoin F S) T).restrictScalars F = (adjoin (adjoin F T) S).restrictScalars F
```

## Premise full source (with proof)
### `IntermediateField.extendScalars_restrictScalars` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
@[simp]
theorem extendScalars_restrictScalars : (extendScalars h).restrictScalars K = E := rfl
```

### `IntermediateField.restrictScalars_adjoin_of_algEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- If `E / L / F` and `E / L' / F` are two field extension towers, `L ≃ₐ[F] L'` is an isomorphism
compatible with `E / L` and `E / L'`, then for any subset `S` of `E`, `L(S)` and `L'(S)` are
equal as intermediate fields of `E / F`. -/
theorem restrictScalars_adjoin_of_algEquiv
    {L L' : Type*} [Field L] [Field L']
    [Algebra F L] [Algebra L E] [Algebra F L'] [Algebra L' E]
    [IsScalarTower F L E] [IsScalarTower F L' E] (i : L ≃ₐ[F] L')
    (hi : algebraMap L E = (algebraMap L' E) ∘ i) (S : Set E) :
    (adjoin L S).restrictScalars F = (adjoin L' S).restrictScalars F := by
  apply_fun toSubfield using (fun K K' h ↦ by
    ext x; change x ∈ K.toSubfield ↔ x ∈ K'.toSubfield; rw [h])
  change Subfield.closure _ = Subfield.closure _
  congr
  ext x
  exact ⟨fun ⟨y, h⟩ ↦ ⟨i y, by rw [← h, hi]; rfl⟩,
    fun ⟨y, h⟩ ↦ ⟨i.symm y, by rw [← h, hi, Function.comp_apply, AlgEquiv.apply_symm_apply]⟩⟩
```

### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```

### `IntermediateField.adjoin_self` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
@[simp]
theorem adjoin_self (K : IntermediateField F E) :
    adjoin F K = K := le_antisymm (adjoin_le_iff.2 fun _ ↦ id) (subset_adjoin F _)
```

### `IntermediateField.adjoin_adjoin_comm` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- `F[S][T] = F[T][S]` -/
theorem adjoin_adjoin_comm (T : Set E) :
    (adjoin (adjoin F S) T).restrictScalars F = (adjoin (adjoin F T) S).restrictScalars F := by
  rw [adjoin_adjoin_left, adjoin_adjoin_left, Set.union_comm]
```

## Transitive premise context (1-hop, 16/16 premises, ≈2442 tokens)
### `StructureGroupoid.compatible` (commanddeclaration) at `Mathlib/Geometry/Manifold/ChartedSpace.lean`
```lean
/-- Reformulate in the `StructureGroupoid` namespace the compatibility condition of charts in a
charted space admitting a structure groupoid, to make it more easily accessible with dot
notation. -/
theorem StructureGroupoid.compatible {H : Type*} [TopologicalSpace H] (G : StructureGroupoid H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M] [HasGroupoid M G]
    {e e' : PartialHomeomorph M H} (he : e ∈ atlas H M) (he' : e' ∈ atlas H M) : e.symm ≫ₕ e' ∈ G :=
  HasGroupoid.compatible he he'
```

### `Lean.Elab.Term.StructInst.Struct.fields` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Elab/StructInst.lean`
```lean
def Struct.fields : Struct → Fields
  | ⟨_, _, _, fields, _⟩ => fields
```

### `Field` (commanddeclaration) at `Mathlib/Algebra/Field/Defs.lean`
```lean
/-- A `Field` is a `CommRing` with multiplicative inverses for nonzero elements.

An instance of `Field K` includes maps `ratCast : ℚ → K` and `qsmul : ℚ → K → K`.
Those two fields are needed to implement the `DivisionRing K → Algebra ℚ K` instance since we need
to control the specific definitions for some special cases of `K` (in particular `K = ℚ` itself).
See also note [forgetful inheritance].

If the field has positive characteristic `p`, our division by zero convention forces
`ratCast (1 / p) = 1 / 0 = 0`. -/
class Field (K : Type u) extends CommRing K, DivisionRing K
```

### `Algebra` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- An associative unital `R`-algebra is a semiring `A` equipped with a map into its center `R → A`.

See the implementation notes in this file for discussion of the details of this definition.
-/
-- Porting note: unsupported @[nolint has_nonempty_instance]
class Algebra (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] extends SMul R A,
  R →+* A where
  commutes' : ∀ r x, toRingHom r * x = x * toRingHom r
  smul_def' : ∀ r x, r • x = toRingHom r * x
```

### `IsScalarTower` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
/-- An instance of `IsScalarTower M N α` states that the multiplicative
action of `M` on `α` is determined by the multiplicative actions of `M` on `N`
and `N` on `α`. -/
@[to_additive VAddAssocClass] -- TODO auto-translating
class IsScalarTower (M N α : Type*) [SMul M N] [SMul N α] [SMul M α] : Prop where
  /-- Associativity of `•` -/
  smul_assoc : ∀ (x : M) (y : N) (z : α), (x • y) • z = x • y • z
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `Turing.PartrecToTM2.K'` (commanddeclaration) at `Mathlib/Computability/TMToPartrec.lean`
```lean
/-- The four stacks used by the program. `main` is used to store the input value in `trNormal`
mode and the output value in `Λ'.ret` mode, while `stack` is used to keep all the data for the
continuations. `rev` is used to store reversed lists when transferring values between stacks, and
`aux` is only used once in `cons₁`. See the section documentation. -/
inductive K'
  | main
  | rev
  | aux
  | stack
  deriving DecidableEq, Inhabited
```

### `Subfield.closure` (commanddeclaration) at `Mathlib/FieldTheory/Subfield.lean`
```lean
/-- The `Subfield` generated by a set. -/
def closure (s : Set K) : Subfield K := sInf {S | s ⊆ S}
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

### `Function.comp_apply` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x) := rfl
```

### `AlgEquiv.apply_symm_apply` (commanddeclaration) at `Mathlib/Algebra/Algebra/Equiv.lean`
```lean
@[simp]
theorem apply_symm_apply (e : A₁ ≃ₐ[R] A₂) : ∀ x, e (e.symm x) = x :=
  e.toEquiv.apply_symm_apply
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

### `IntermediateField` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
/-- `S : IntermediateField K L` is a subset of `L` such that there is a field
tower `L / S / K`. -/
structure IntermediateField extends Subalgebra K L where
  inv_mem' : ∀ x ∈ carrier, x⁻¹ ∈ carrier
```

### `le_antisymm` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem le_antisymm : ∀ {a b : α}, a ≤ b → b ≤ a → a = b :=
  PartialOrder.le_antisymm _ _
```

### `IntermediateField.adjoin_adjoin_left` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- `F[S][T] = F[S ∪ T]` -/
theorem adjoin_adjoin_left (T : Set E) :
    (adjoin (adjoin F S) T).restrictScalars _ = adjoin F (S ∪ T) := by
  rw [SetLike.ext'_iff]
  change (↑(adjoin (adjoin F S) T) : Set E) = _
  apply Set.eq_of_subset_of_subset <;> rw [adjoin_subset_adjoin_iff] <;> constructor
  · rintro _ ⟨⟨x, hx⟩, rfl⟩; exact adjoin.mono _ _ _ (Set.subset_union_left _ _) hx
  · exact subset_adjoin_of_subset_right _ _ (Set.subset_union_right _ _)
-- Porting note: orginal proof times out
  · rintro x ⟨f, rfl⟩
    refine' Subfield.subset_closure _
    left
    exact ⟨f, rfl⟩
-- Porting note: orginal proof times out
  · refine' Set.union_subset (fun x hx => Subfield.subset_closure _)
      (fun x hx => Subfield.subset_closure _)
    · left
      refine' ⟨⟨x, Subfield.subset_closure _⟩, rfl⟩
      right
      exact hx
    · right
      exact hx
```

### `Set.union_comm` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
theorem union_comm (a b : Set α) : a ∪ b = b ∪ a :=
  ext fun _ => or_comm
```
