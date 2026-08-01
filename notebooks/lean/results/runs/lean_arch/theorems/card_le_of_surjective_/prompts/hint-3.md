## Current goal
```
⊢ Fintype.card β ≤ Fintype.card α
```

## Full tactic state
```
R : Type u
inst✝³ : Semiring R
inst✝² : RankCondition R
α : Type u_1
β : Type u_2
inst✝¹ : Fintype α
inst✝ : Fintype β
f : (α →₀ R) →ₗ[R] β →₀ R
i : Surjective ⇑f
P : (β →₀ R) ≃ₗ[R] β → R := Finsupp.linearEquivFunOnFinite R R β
Q : (α → R) ≃ₗ[R] α →₀ R := LinearEquiv.symm (Finsupp.linearEquivFunOnFinite R R α)
⊢ Fintype.card β ≤ Fintype.card α
```

## Proof so far (2 tactics)
```lean
let P := Finsupp.linearEquivFunOnFinite R R β
let Q := (Finsupp.linearEquivFunOnFinite R R α).symm
```

## Theorem
`card_le_of_surjective'` in `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`

## Premises used in the next tactic
- `card_le_of_surjective`
- `LinearMap.comp`
- `Function.Surjective.comp`

## Premise signatures
### `card_le_of_surjective` (commanddeclaration)
```lean
theorem card_le_of_surjective [RankCondition R] {α β : Type*} [Fintype α] [Fintype β]
    (f : (α → R) →ₗ[R] β → R) (i : Surjective f) : Fintype.card β ≤ Fintype.card α
```

### `LinearMap.comp` (commanddeclaration)
```lean
def comp : M₁ →ₛₗ[σ₁₃] M₃ where
  toFun
```

### `Function.Surjective.comp` (commanddeclaration)
```lean
theorem Surjective.comp {g : β → φ} {f : α → β} (hg : Surjective g) (hf : Surjective f) :
    Surjective (g ∘ f)
```

## Premise full source (with proof)
### `card_le_of_surjective` (commanddeclaration) at `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`
```lean
theorem card_le_of_surjective [RankCondition R] {α β : Type*} [Fintype α] [Fintype β]
    (f : (α → R) →ₗ[R] β → R) (i : Surjective f) : Fintype.card β ≤ Fintype.card α := by
  let P := LinearEquiv.funCongrLeft R R (Fintype.equivFin α)
  let Q := LinearEquiv.funCongrLeft R R (Fintype.equivFin β)
  exact
    le_of_fin_surjective R ((Q.symm.toLinearMap.comp f).comp P.toLinearMap)
      (((LinearEquiv.symm Q).surjective.comp i).comp (LinearEquiv.surjective P))
```

### `LinearMap.comp` (commanddeclaration) at `Mathlib/Algebra/Module/LinearMap/Basic.lean`
```lean
/-- Composition of two linear maps is a linear map -/
def comp : M₁ →ₛₗ[σ₁₃] M₃ where
  toFun := f ∘ g
  map_add' := by simp only [map_add, forall_const, Function.comp_apply]
  -- Note that #8386 changed `map_smulₛₗ` to `map_smulₛₗ _`
  map_smul' r x := by simp only [Function.comp_apply, map_smulₛₗ _, RingHomCompTriple.comp_apply]
```

### `Function.Surjective.comp` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
theorem Surjective.comp {g : β → φ} {f : α → β} (hg : Surjective g) (hf : Surjective f) :
    Surjective (g ∘ f) := fun c : φ =>
  Exists.elim (hg c) fun b hb =>
    Exists.elim (hf b) fun a ha =>
      Exists.intro a (show g (f a) = c from Eq.trans (congr_arg g ha) hb)
```

## Transitive premise context (1-hop, 18/18 premises, ≈2350 tokens)
### `RankCondition` (commanddeclaration) at `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`
```lean
/-- We say that `R` satisfies the rank condition if `(Fin n → R) →ₗ[R] (Fin m → R)` surjective
    implies `m ≤ n`. -/
class RankCondition : Prop where
  /-- Any surjective linear map from `Rⁿ` to `Rᵐ` guarantees `m ≤ n`. -/
  le_of_fin_surjective : ∀ {n m : ℕ} (f : (Fin n → R) →ₗ[R] Fin m → R), Surjective f → m ≤ n
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

### `Function.Surjective` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
/-- A function `f : α → β` is called surjective if every `b : β` is equal to `f a`
for some `a : α`. -/
def Surjective (f : α → β) : Prop :=
  ∀ b, ∃ a, f a = b
```

### `Fintype.card` (commanddeclaration) at `Mathlib/Data/Fintype/Card.lean`
```lean
/-- `card α` is the number of elements in `α`, defined when `α` is a fintype. -/
def card (α) [Fintype α] : ℕ :=
  (@univ α _).card
```

### `LinearEquiv.funCongrLeft` (commanddeclaration) at `Mathlib/LinearAlgebra/Basic.lean`
```lean
/-- Given an `R`-module `M` and an equivalence `m ≃ n` between arbitrary types,
construct a linear equivalence `(n → M) ≃ₗ[R] (m → M)` -/
def funCongrLeft (e : m ≃ n) : (n → M) ≃ₗ[R] m → M :=
  LinearEquiv.ofLinear (funLeft R M e) (funLeft R M e.symm)
    (LinearMap.ext fun x =>
      funext fun i => by rw [id_apply, ← funLeft_comp, Equiv.symm_comp_self, LinearMap.funLeft_id])
    (LinearMap.ext fun x =>
      funext fun i => by rw [id_apply, ← funLeft_comp, Equiv.self_comp_symm, LinearMap.funLeft_id])
```

### `Fintype.equivFin` (commanddeclaration) at `Mathlib/Data/Fintype/Card.lean`
```lean
/-- There is (noncomputably) an equivalence between `α` and `Fin (card α)`.

See `Fintype.truncEquivFin` for the computable version,
and `Fintype.truncEquivFinOfCardEq` and `Fintype.equivFinOfCardEq`
for an equiv `α ≃ Fin n` given `Fintype.card α = n`.
-/
noncomputable def equivFin (α) [Fintype α] : α ≃ Fin (card α) :=
  letI := Classical.decEq α
  (truncEquivFin α).out
```

### `le_of_fin_surjective` (commanddeclaration) at `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`
```lean
theorem le_of_fin_surjective [RankCondition R] {n m : ℕ} (f : (Fin n → R) →ₗ[R] Fin m → R) :
    Surjective f → m ≤ n :=
  RankCondition.le_of_fin_surjective f
```

### `LinearEquiv.symm` (commanddeclaration) at `Mathlib/Algebra/Module/Equiv.lean`
```lean
/-- Linear equivalences are symmetric. -/
@[symm]
def symm (e : M ≃ₛₗ[σ] M₂) : M₂ ≃ₛₗ[σ'] M :=
  { e.toLinearMap.inverse e.invFun e.left_inv e.right_inv,
    e.toEquiv.symm with
    toFun := e.toLinearMap.inverse e.invFun e.left_inv e.right_inv
    invFun := e.toEquiv.symm.invFun
    map_smul' := fun r x => by dsimp only; rw [map_smulₛₗ] }
```

### `LinearEquiv.surjective` (commanddeclaration) at `Mathlib/Algebra/Module/Equiv.lean`
```lean
protected theorem surjective : Function.Surjective e :=
  e.toEquiv.surjective
```

### `Composition` (commanddeclaration) at `Mathlib/Combinatorics/Composition.lean`
```lean
/-- A composition of `n` is a list of positive integers summing to `n`. -/
@[ext]
structure Composition (n : ℕ) where
  /-- List of positive integers summing to `n`-/
  blocks : List ℕ
  /-- Proof of positivity for `blocks`-/
  blocks_pos : ∀ {i}, i ∈ blocks → 0 < i
  /-- Proof that `blocks` sums to `n`-/
  blocks_sum : blocks.sum = n
```

### `forall_const` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
@[simp] theorem forall_const (α : Sort _) [i : Nonempty α] : (α → b) ↔ b :=
  ⟨i.elim, fun hb _ => hb⟩
```

### `Function.comp_apply` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x) := rfl
```

### `RingHomCompTriple.comp_apply` (commanddeclaration) at `Mathlib/Algebra/Ring/CompTypeclasses.lean`
```lean
@[simp]
theorem comp_apply [RingHomCompTriple σ₁₂ σ₂₃ σ₁₃] {x : R₁} : σ₂₃ (σ₁₂ x) = σ₁₃ x :=
  RingHom.congr_fun comp_eq x
```

### `CategoryTheory.ShortComplex.LeftHomologyData.IsPreservedBy.hg` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a left homology data is preserved by a functor `F`, this functor
preserves the kernel of `S.g : S.X₂ ⟶ S.X₃`. -/
def IsPreservedBy.hg : PreservesLimit (parallelPair S.g 0) F :=
  @IsPreservedBy.g _ _ _ _ _ _ _ h F _ _

/-- When a left homology data `h` is preserved by a functor `F`, this functor
preserves the cokernel of `h.f' : S.X₁ ⟶ h.K`. -/
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

### `Exists.elim` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem Exists.elim {α : Sort u} {p : α → Prop} {b : Prop}
   (h₁ : Exists (fun x => p x)) (h₂ : ∀ (a : α), p a → b) : b :=
  match h₁ with
  | intro a h => h₂ a h

/-! # Decidable -/
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

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```
