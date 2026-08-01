## Current goal
```
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```

## Full tactic state
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
inst✝³ : AddCommGroup M'
inst✝² : Module R M'
ι : Type u_4
inst✝¹ : DecidableEq ι
inst✝ : Fintype ι
e : Basis ι R M
f : M [⋀^ι]→ₗ[R] R
i : ι → ι
h : Injective i
σ : Equiv.Perm ι := Equiv.ofBijective i ⋯
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```

## Proof so far (3 tactics)
```lean
refine' Basis.ext_alternating e fun i h => _
let σ : Equiv.Perm ι := Equiv.ofBijective i (Finite.injective_iff_bijective.1 h)
change f (e ∘ σ) = (f e • e.det) (e ∘ σ)
```

## Theorem
`AlternatingMap.eq_smul_basis_det` in `Mathlib/LinearAlgebra/Determinant.lean`

## Premises used in the next tactic
- `AlternatingMap.map_perm`
- `Basis.det_self`

## Premise signatures
### `AlternatingMap.map_perm` (commanddeclaration)
```lean
theorem map_perm [DecidableEq ι] [Fintype ι] (v : ι → M) (σ : Equiv.Perm ι) :
    g (v ∘ σ) = Equiv.Perm.sign σ • g v
```

### `Basis.det_self` (commanddeclaration)
```lean
theorem Basis.det_self : e.det e = 1
```

## Premise full source (with proof)
### `AlternatingMap.map_perm` (commanddeclaration) at `Mathlib/LinearAlgebra/Alternating/Basic.lean`
```lean
theorem map_perm [DecidableEq ι] [Fintype ι] (v : ι → M) (σ : Equiv.Perm ι) :
    g (v ∘ σ) = Equiv.Perm.sign σ • g v := by
  -- Porting note: `apply` → `induction'`
  induction' σ using Equiv.Perm.swap_induction_on' with s x y hxy hI
  · simp
  · -- Porting note: `← Function.comp.assoc` & `-Equiv.Perm.sign_swap'` are required.
    simpa [← Function.comp.assoc, g.map_swap (v ∘ s) hxy,
      Equiv.Perm.sign_swap hxy, -Equiv.Perm.sign_swap'] using hI
```

### `Basis.det_self` (commanddeclaration) at `Mathlib/LinearAlgebra/Determinant.lean`
```lean
theorem Basis.det_self : e.det e = 1 := by simp [e.det_apply]
```

## Transitive premise context (1-hop, 9/9 premises, ≈1101 tokens)
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

### `Equiv.Perm` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
/-- `Perm α` is the type of bijections from `α` to itself. -/
@[reducible]
def Equiv.Perm (α : Sort*) :=
  Equiv α α
```

### `Equiv.Perm.sign` (commanddeclaration) at `Mathlib/GroupTheory/Perm/Sign.lean`
```lean
/-- `SignType.sign` of a permutation returns the signature or parity of a permutation, `1` for even
permutations, `-1` for odd permutations. It is the unique surjective group homomorphism from
`Perm α` to the group with two elements.-/
def sign [Fintype α] : Perm α →* ℤˣ :=
  MonoidHom.mk' (fun f => signAux3 f mem_univ) fun f g => (signAux3_mul_and_swap f g _ mem_univ).1
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

### `Equiv.Perm.swap_induction_on'` (commanddeclaration) at `Mathlib/GroupTheory/Perm/Sign.lean`
```lean
/-- Like `swap_induction_on`, but with the composition on the right of `f`.

An induction principle for permutations. If `P` holds for the identity permutation, and
is preserved under composition with a non-trivial swap, then `P` holds for all permutations. -/
@[elab_as_elim]
theorem swap_induction_on' [Finite α] {P : Perm α → Prop} (f : Perm α) :
    P 1 → (∀ f x y, x ≠ y → P f → P (f * swap x y)) → P f := fun h1 IH =>
  inv_inv f ▸ swap_induction_on f⁻¹ h1 fun f => IH f⁻¹
```

### `Function.comp.assoc` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
theorem comp.assoc (f : φ → δ) (g : β → φ) (h : α → β) : (f ∘ g) ∘ h = f ∘ g ∘ h :=
  rfl
```

### `Equiv.Perm.sign_swap'` (commanddeclaration) at `Mathlib/GroupTheory/Perm/Sign.lean`
```lean
@[simp]
theorem sign_swap' {x y : α} : sign (swap x y) = if x = y then 1 else -1 :=
  if H : x = y then by simp [H, swap_self] else by simp [sign_swap H, H]
```

### `Equiv.Perm.sign_swap` (commanddeclaration) at `Mathlib/GroupTheory/Perm/Sign.lean`
```lean
theorem sign_swap {x y : α} (h : x ≠ y) : sign (swap x y) = -1 :=
  (signAux3_mul_and_swap 1 1 _ mem_univ).2 h
```
