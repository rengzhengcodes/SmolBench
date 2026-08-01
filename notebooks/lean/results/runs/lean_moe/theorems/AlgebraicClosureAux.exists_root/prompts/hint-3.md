## Current goal
```
⊢ ∃ n p, map (ofStep k n) p = f
```

## Full tactic state
```
k : Type u
inst✝ : Field k
f : (AlgebraicClosureAux k)[X]
hfm : Monic f
hfi : Irreducible f
⊢ ∃ n p, map (ofStep k n) p = f
```

## Proof so far (7 tactics)
```lean
have : ∃ n p, Polynomial.map (ofStep k n) p = f := by
  convert Ring.DirectLimit.Polynomial.exists_of f
obtain ⟨n, p, rfl⟩ := this
rw [monic_map_iff] at hfm
have := hfm.irreducible_of_irreducible_map (ofStep k n) p hfi
obtain ⟨x, hx⟩ := toStepSucc.exists_root k hfm this
refine' ⟨ofStep k (n + 1) x, _⟩
rw [← ofStep_succ k n, eval_map, ← hom_eval₂, hx, RingHom.map_zero]
```

## Theorem
`AlgebraicClosureAux.exists_root` in `Mathlib/FieldTheory/IsAlgClosed/AlgebraicClosure.lean`

## Premises used in the next tactic
- `Ring.DirectLimit.Polynomial.exists_of`

## Premise signatures
### `Ring.DirectLimit.Polynomial.exists_of` (commanddeclaration)
```lean
nonrec theorem Polynomial.exists_of [Nonempty ι] [IsDirected ι (· ≤ ·)]
    (q : Polynomial (DirectLimit G fun i j h => f' i j h)) :
    ∃ i p, Polynomial.map (of G (fun i j h => f' i j h) i) p = q
```

## Premise full source (with proof)
### `Ring.DirectLimit.Polynomial.exists_of` (commanddeclaration) at `Mathlib/Algebra/DirectLimit.lean`
```lean
nonrec theorem Polynomial.exists_of [Nonempty ι] [IsDirected ι (· ≤ ·)]
    (q : Polynomial (DirectLimit G fun i j h => f' i j h)) :
    ∃ i p, Polynomial.map (of G (fun i j h => f' i j h) i) p = q :=
  Polynomial.induction_on q
    (fun z =>
      let ⟨i, x, h⟩ := exists_of z
      ⟨i, C x, by rw [map_C, h]⟩)
    (fun q₁ q₂ ⟨i₁, p₁, ih₁⟩ ⟨i₂, p₂, ih₂⟩ =>
      let ⟨i, h1, h2⟩ := exists_ge_ge i₁ i₂
      ⟨i, p₁.map (f' i₁ i h1) + p₂.map (f' i₂ i h2), by
        rw [Polynomial.map_add, map_map, map_map, ← ih₁, ← ih₂]
        congr 2 <;> ext x <;> simp_rw [RingHom.comp_apply, of_f]⟩)
    fun n z _ =>
    let ⟨i, x, h⟩ := exists_of z
    ⟨i, C x * X ^ (n + 1), by rw [Polynomial.map_mul, map_C, h, Polynomial.map_pow, map_X]⟩
```

## Transitive premise context (1-hop, 12/12 premises, ≈1813 tokens)
### `Lean.Parser.Command.nonrec` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
def «nonrec»         := leading_parser "nonrec "

/-- `declModifiers` is the collection of modifiers on a declaration:
* a doc comment `/-- ... -/`
* a list of attributes `@[attr1, attr2]`
* a visibility specifier, `private` or `protected`
* `noncomputable`
* `unsafe`
* `partial` or `nonrec`

All modifiers are optional, and have to come in the listed order.

`nestedDeclModifiers` is the same as `declModifiers`, but attributes are printed
on the same line as the declaration. It is used for declarations nested inside other syntax,
such as inductive constructors, structure projections, and `let rec` / `where` definitions. -/
```

### `Nonempty` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Nonempty α` is a typeclass that says that `α` is not an empty type,
that is, there exists an element in the type. It differs from `Inhabited α`
in that `Nonempty α` is a `Prop`, which means that it does not actually carry
an element of `α`, only a proof that *there exists* such an element.
Given `Nonempty α`, you can construct an element of `α` *nonconstructively*
using `Classical.choice`.
-/
class inductive Nonempty (α : Sort u) : Prop where
  /-- If `val : α`, then `α` is nonempty. -/
  | intro (val : α) : Nonempty α

/--
**The axiom of choice**. `Nonempty α` is a proof that `α` has an element,
but the element itself is erased. The axiom `choice` supplies a particular
element of `α` given only this proof.

The textbook axiom of choice normally makes a family of choices all at once,
but that is implied from this formulation, because if `α : ι → Type` is a
family of types and `h : ∀ i, Nonempty (α i)` is a proof that they are all
nonempty, then `fun i => Classical.choice (h i) : ∀ i, α i` is a family of
chosen elements. This is actually a bit stronger than the ZFC choice axiom;
this is sometimes called "[global choice](https://en.wikipedia.org/wiki/Axiom_of_global_choice)".

In Lean, we use the axiom of choice to derive the law of excluded middle
(see `Classical.em`), so it will often show up in axiom listings where you
may not expect. You can use `#print axioms my_thm` to find out if a given
```

### `IsDirected` (commanddeclaration) at `Mathlib/Order/Directed.lean`
```lean
/-- `IsDirected α r` states that for any elements `a`, `b` there exists an element `c` such that
`r a c` and `r b c`. -/
class IsDirected (α : Type*) (r : α → α → Prop) : Prop where
  /-- For every pair of elements `a` and `b` there is a `c` such that `r a c` and `r b c` -/
  directed (a b : α) : ∃ c, r a c ∧ r b c
```

### `Polynomial` (commanddeclaration) at `Mathlib/Data/Polynomial/Basic.lean`
```lean
/-- `Polynomial R` is the type of univariate polynomials over `R`.

Polynomials should be seen as (semi-)rings with the additional constructor `X`.
The embedding from `R` is called `C`. -/
structure Polynomial (R : Type*) [Semiring R] where ofFinsupp ::
  toFinsupp : AddMonoidAlgebra R ℕ
```

### `Polynomial.map` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
/-- `map f p` maps a polynomial `p` across a ring hom `f` -/
def map : R[X] → S[X] :=
  eval₂ (C.comp f) X
```

### `Polynomial.induction_on` (commanddeclaration) at `Mathlib/Data/Polynomial/Induction.lean`
```lean
@[elab_as_elim]
protected theorem induction_on {M : R[X] → Prop} (p : R[X]) (h_C : ∀ a, M (C a))
    (h_add : ∀ p q, M p → M q → M (p + q))
    (h_monomial : ∀ (n : ℕ) (a : R), M (C a * X ^ n) → M (C a * X ^ (n + 1))) : M p := by
  have A : ∀ {n : ℕ} {a}, M (C a * X ^ n) := by
    intro n a
    induction' n with n ih
    · rw [pow_zero, mul_one]; exact h_C a
    · exact h_monomial _ _ ih
  have B : ∀ s : Finset ℕ, M (s.sum fun n : ℕ => C (p.coeff n) * X ^ n) := by
    apply Finset.induction
    · convert h_C 0
      exact C_0.symm
    · intro n s ns ih
      rw [sum_insert ns]
      exact h_add _ _ A ih
  rw [← sum_C_mul_X_pow_eq p, Polynomial.sum]
  exact B (support p)
```

### `exists_ge_ge` (commanddeclaration) at `Mathlib/Order/Directed.lean`
```lean
theorem exists_ge_ge [LE α] [IsDirected α (· ≤ ·)] (a b : α) : ∃ c, a ≤ c ∧ b ≤ c :=
  directed_of (· ≤ ·) a b
```

### `Polynomial.map_add` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
@[simp]
protected theorem map_add : (p + q).map f = p.map f + q.map f :=
  eval₂_add _ _
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

### `RingHom.comp_apply` (commanddeclaration) at `Mathlib/Algebra/Ring/Hom/Defs.lean`
```lean
theorem comp_apply (hnp : β →+* γ) (hmn : α →+* β) (x : α) :
    (hnp.comp hmn : α → γ) x = hnp (hmn x) :=
  rfl
```

### `Polynomial.map_mul` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
@[simp]
protected theorem map_mul : (p * q).map f = p.map f * q.map f := by
  rw [map, eval₂_mul_noncomm]
  exact fun k => (commute_X _).symm
```

### `Polynomial.map_pow` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
@[simp]
protected theorem map_pow (n : ℕ) : (p ^ n).map f = p.map f ^ n :=
  (mapRingHom f).map_pow _ _
```
