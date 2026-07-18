## Current goal
```
⊢ Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f
```

## Full tactic state
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
inst✝ : PerfectRing R p
⊢ Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Polynomial.roots_expand_pow_map_iterateFrobenius` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `coe_iterateFrobeniusEquiv`
- `Polynomial.roots_expand_pow`
- `Multiset.map_nsmul`
- `Multiset.map_map`
- `Function.comp_apply`
- `RingEquiv.apply_symm_apply`
- `Multiset.map_id'`

## Premise signatures
### `coe_iterateFrobeniusEquiv` (commanddeclaration)
```lean
@[simp]
theorem coe_iterateFrobeniusEquiv : ⇑(iterateFrobeniusEquiv R p n) = iterateFrobenius R p n
```

### `Polynomial.roots_expand_pow` (commanddeclaration)
```lean
theorem roots_expand_pow :
    (expand R (p ^ n) f).roots = p ^ n • f.roots.map (iterateFrobeniusEquiv R p n).symm
```

### `Multiset.map_nsmul` (commanddeclaration)
```lean
theorem map_nsmul (f : α → β) (n : ℕ) (s) : map f (n • s) = n • map f s
```

### `Multiset.map_map` (commanddeclaration)
```lean
@[simp]
theorem map_map (g : β → γ) (f : α → β) (s : Multiset α) : map g (map f s) = map (g ∘ f) s
```

### `Function.comp_apply` (commanddeclaration)
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x)
```

### `RingEquiv.apply_symm_apply` (commanddeclaration)
```lean
@[simp]
theorem apply_symm_apply (e : R ≃+* S) : ∀ x, e (e.symm x) = x
```

### `Multiset.map_id'` (commanddeclaration)
```lean
@[simp]
theorem map_id' (s : Multiset α) : map (fun x => x) s = s
```

## Premise full source (with proof)
### `coe_iterateFrobeniusEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
@[simp]
theorem coe_iterateFrobeniusEquiv : ⇑(iterateFrobeniusEquiv R p n) = iterateFrobenius R p n := rfl
```

### `Polynomial.roots_expand_pow` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem roots_expand_pow :
    (expand R (p ^ n) f).roots = p ^ n • f.roots.map (iterateFrobeniusEquiv R p n).symm := by
  classical
  refine ext' fun r ↦ ?_
  rw [count_roots, rootMultiplicity_expand_pow, ← count_roots, count_nsmul, count_map,
    count_eq_card_filter_eq]; congr; ext
  exact (iterateFrobeniusEquiv R p n).eq_symm_apply.symm
```

### `Multiset.map_nsmul` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
theorem map_nsmul (f : α → β) (n : ℕ) (s) : map f (n • s) = n • map f s :=
  (mapAddMonoidHom f).map_nsmul _ _
```

### `Multiset.map_map` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
@[simp]
theorem map_map (g : β → γ) (f : α → β) (s : Multiset α) : map g (map f s) = map (g ∘ f) s :=
  Quot.inductionOn s fun _l => congr_arg _ <| List.map_map _ _ _
```

### `Function.comp_apply` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x) := rfl
```

### `RingEquiv.apply_symm_apply` (commanddeclaration) at `Mathlib/Algebra/Ring/Equiv.lean`
```lean
@[simp]
theorem apply_symm_apply (e : R ≃+* S) : ∀ x, e (e.symm x) = x :=
  e.toEquiv.apply_symm_apply
```

### `Multiset.map_id'` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
@[simp]
theorem map_id' (s : Multiset α) : map (fun x => x) s = s :=
  map_id s
```

## Transitive premise context (1-hop, 14/14 premises, ≈1568 tokens)
### `iterateFrobeniusEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
/-- The iterated Frobenius automorphism for a perfect ring. -/
@[simps! apply]
noncomputable def iterateFrobeniusEquiv : R ≃+* R :=
  RingEquiv.ofBijective (iterateFrobenius R p n) (bijective_iterateFrobenius R p n)
```

### `iterateFrobenius` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The iterated frobenius map sending x to x^p^n -/
def iterateFrobenius : R →+* R where
  __ := powMonoidHom (p ^ n)
  map_zero' := zero_pow (expChar_pow_pos R p n).ne'
  map_add' := add_pow_expChar_pow R
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Polynomial.count_roots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
@[simp]
theorem count_roots [DecidableEq R] (p : R[X]) : p.roots.count a = rootMultiplicity a p := by
  classical
  by_cases hp : p = 0
  · simp [hp]
  rw [roots_def, dif_neg hp]
  exact (Classical.choose_spec (exists_multiset_roots hp)).2 a
```

### `Polynomial.rootMultiplicity_expand_pow` (commanddeclaration) at `Mathlib/Data/Polynomial/Expand.lean`
```lean
theorem rootMultiplicity_expand_pow :
    (expand R (p ^ n) f).rootMultiplicity r = p ^ n * f.rootMultiplicity (r ^ p ^ n) := by
  obtain rfl | h0 := eq_or_ne f 0; · simp
  obtain ⟨g, hg, ndvd⟩ := f.exists_eq_pow_rootMultiplicity_mul_and_not_dvd h0 (r ^ p ^ n)
  rw [dvd_iff_isRoot, ← eval_X (x := r), ← eval_pow, ← isRoot_comp, ← expand_eq_comp_X_pow] at ndvd
  conv_lhs => rw [hg, map_mul, map_pow, map_sub, expand_X, expand_C, map_pow, ← sub_pow_expChar_pow,
    ← pow_mul, mul_comm, rootMultiplicity_mul_X_sub_C_pow (expand_ne_zero (expChar_pow_pos R p n)
      |>.mpr <| right_ne_zero_of_mul <| hg ▸ h0), rootMultiplicity_eq_zero ndvd, zero_add]
```

### `Multiset.count_nsmul` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
@[simp]
theorem count_nsmul (a : α) (n s) : count a (n • s) = n * count a s := by
  induction n <;> simp [*, succ_nsmul', succ_mul, zero_nsmul]
```

### `Multiset.count_map` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
theorem count_map {α β : Type*} (f : α → β) (s : Multiset α) [DecidableEq β] (b : β) :
    count b (map f s) = card (s.filter fun a => b = f a) := by
  simp [Bool.beq_eq_decide_eq, eq_comm, count, countP_map]
```

### `Multiset.count_eq_card_filter_eq` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
theorem count_eq_card_filter_eq [DecidableEq α] (s : Multiset α) (a : α) :
    s.count a = card (s.filter (a = ·)) := by rw [count, countP_eq_card_filter]
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

### `Multiset.mapAddMonoidHom` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
/-- `Multiset.map` as an `AddMonoidHom`. -/
def mapAddMonoidHom (f : α → β) : Multiset α →+ Multiset β where
  toFun := map f
  map_zero' := map_zero _
  map_add' := map_add _
```

### `Multiset` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
/-- `Multiset α` is the quotient of `List α` by list permutation. The result
  is a type of finite sets with duplicates allowed.  -/
def Multiset.{u} (α : Type u) : Type u :=
  Quotient (List.isSetoid α)
```

### `Quot.inductionOn` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[elab_as_elim]
protected theorem inductionOn {α : Sort u} {r : α → α → Prop} {motive : Quot r → Prop}
    (q : Quot r)
    (h : (a : α) → motive (Quot.mk r a))
    : motive q :=
  ind h q
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

### `List.map_map` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Lemmas.lean`
```lean
@[simp] theorem map_map (g : β → γ) (f : α → β) (l : List α) :
  map g (map f l) = map (g ∘ f) l := by induction l <;> simp_all

/-! ### bind -/
```
