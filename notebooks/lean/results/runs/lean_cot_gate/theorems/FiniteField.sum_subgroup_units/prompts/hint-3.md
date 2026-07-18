## Current goal
```
⊢ ∑ x : ↥G, ↑↑x = 0
```

## Full tactic state
```
case neg
K : Type u_1
R : Type u_2
inst✝³ : Ring K
inst✝² : NoZeroDivisors K
G : Subgroup Kˣ
inst✝¹ : Fintype ↥G
inst✝ : Decidable (G = ⊥)
G_bot : ¬G = ⊥
⊢ ∑ x : ↥G, ↑↑x = 0
```

## Proof so far (4 tactics)
```lean
by_cases G_bot : G = ⊥
subst G_bot
simp only [ite_true, Subgroup.mem_bot, Fintype.card_ofSubsingleton, Nat.cast_ite, Nat.cast_one,
  Nat.cast_zero, univ_unique, Set.default_coe_singleton, sum_singleton, Units.val_one]
simp only [G_bot, ite_false]
```

## Theorem
`FiniteField.sum_subgroup_units` in `Mathlib/FieldTheory/Finite/Basic.lean`

## Premises used in the next tactic
- `FiniteField.sum_subgroup_units_eq_zero`

## Premise signatures
### `FiniteField.sum_subgroup_units_eq_zero` (commanddeclaration)
```lean
theorem sum_subgroup_units_eq_zero [Ring K] [NoZeroDivisors K]
    {G : Subgroup Kˣ} [Fintype G] (hg : G ≠ ⊥) :
    ∑ x : G, (x.val : K) = 0
```

## Premise full source (with proof)
### `FiniteField.sum_subgroup_units_eq_zero` (commanddeclaration) at `Mathlib/FieldTheory/Finite/Basic.lean`
```lean
/-- The sum of a nontrivial subgroup of the units of a field is zero. -/
theorem sum_subgroup_units_eq_zero [Ring K] [NoZeroDivisors K]
    {G : Subgroup Kˣ} [Fintype G] (hg : G ≠ ⊥) :
    ∑ x : G, (x.val : K) = 0 := by
  rw [Subgroup.ne_bot_iff_exists_ne_one] at hg
  rcases hg with ⟨a, ha⟩
  -- The action of a on G as an embedding
  let a_mul_emb : G ↪ G := mulLeftEmbedding a
  -- ... and leaves G unchanged
  have h_unchanged : Finset.univ.map a_mul_emb = Finset.univ := by simp
  -- Therefore the sum of x over a G is the sum of a x over G
  have h_sum_map := Finset.univ.sum_map a_mul_emb fun x => ((x : Kˣ) : K)
  -- ... and the former is the sum of x over G.
  -- By algebraic manipulation, we have Σ G, x = ∑ G, a x = a ∑ G, x
  simp only [a_mul_emb, h_unchanged, Function.Embedding.coeFn_mk, Function.Embedding.toFun_eq_coe,
    mulLeftEmbedding_apply, Submonoid.coe_mul, Subgroup.coe_toSubmonoid, Units.val_mul,
    ← Finset.mul_sum] at h_sum_map
  -- thus one of (a - 1) or ∑ G, x is zero
  have hzero : (((a : Kˣ) : K) - 1) = 0 ∨ ∑ x : ↥G, ((x : Kˣ) : K) = 0 := by
    rw [← mul_eq_zero, sub_mul, ← h_sum_map, one_mul, sub_self]
  apply Or.resolve_left hzero
  contrapose! ha
  ext
  rwa [← sub_eq_zero]

/-- The sum of a subgroup of the units of a field is 1 if the subgroup is trivial and 1 otherwise -/
```

## Transitive premise context (1-hop, 19/19 premises, ≈1821 tokens)
### `Ring` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
/-- A `Ring` is a `Semiring` with negation making it an additive group. -/
class Ring (R : Type u) extends Semiring R, AddCommGroup R, AddGroupWithOne R
```

### `NoZeroDivisors` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/Defs.lean`
```lean
/-- Predicate typeclass for expressing that `a * b = 0` implies `a = 0` or `b = 0`
for all `a` and `b` of type `G₀`. -/
class NoZeroDivisors (M₀ : Type*) [Mul M₀] [Zero M₀] : Prop where
  /-- For all `a` and `b` of `G₀`, `a * b = 0` implies `a = 0` or `b = 0`. -/
  eq_zero_or_eq_zero_of_mul_eq_zero : ∀ {a b : M₀}, a * b = 0 → a = 0 ∨ b = 0
```

### `Subgroup` (commanddeclaration) at `Mathlib/GroupTheory/Subgroup/Basic.lean`
```lean
/-- A subgroup of a group `G` is a subset containing 1, closed under multiplication
and closed under multiplicative inverse. -/
structure Subgroup (G : Type*) [Group G] extends Submonoid G where
  /-- `G` is closed under inverses -/
  inv_mem' {x} : x ∈ carrier → x⁻¹ ∈ carrier
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

### `CategoryTheory.ShortComplex.LeftHomologyData.IsPreservedBy.hg` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a left homology data is preserved by a functor `F`, this functor
preserves the kernel of `S.g : S.X₂ ⟶ S.X₃`. -/
def IsPreservedBy.hg : PreservesLimit (parallelPair S.g 0) F :=
  @IsPreservedBy.g _ _ _ _ _ _ _ h F _ _

/-- When a left homology data `h` is preserved by a functor `F`, this functor
preserves the cokernel of `h.f' : S.X₁ ⟶ h.K`. -/
```

### `Subgroup.ne_bot_iff_exists_ne_one` (lemma) at `Mathlib/GroupTheory/Subgroup/Basic.lean`
```lean
@[to_additive]
lemma ne_bot_iff_exists_ne_one {H : Subgroup G} : H ≠ ⊥ ↔ ∃ a : ↥H, a ≠ 1 := by
  rw [← nontrivial_iff_ne_bot, nontrivial_iff_exists_ne_one]
  simp only [ne_eq, Subtype.exists, mk_eq_one, exists_prop]

/-- The inf of two subgroups is their intersection. -/
```

### `mulLeftEmbedding` (commanddeclaration) at `Mathlib/Algebra/Group/Embedding.lean`
```lean
/-- If left-multiplication by any element is cancellative, left-multiplication by `g` is an
embedding. -/
@[to_additive (attr := simps)
      "If left-addition by any element is cancellative, left-addition by `g` is an
        embedding."]
def mulLeftEmbedding [Mul G] [IsLeftCancelMul G] (g : G) : G ↪ G where
  toFun h := g * h
  inj' := mul_right_injective g
```

### `Finset.univ` (commanddeclaration) at `Mathlib/Data/Fintype/Basic.lean`
```lean
/-- `univ` is the universal finite set of type `Finset α` implied from
  the assumption `Fintype α`. -/
def univ : Finset α :=
  @Fintype.elems α _
```

### `Function.Embedding.coeFn_mk` (commanddeclaration) at `Mathlib/Logic/Embedding/Basic.lean`
```lean
@[simp]
theorem coeFn_mk {α β} (f : α → β) (i) : (@mk _ _ f i : α → β) = f :=
  rfl
```

### `Function.Embedding.toFun_eq_coe` (commanddeclaration) at `Mathlib/Logic/Embedding/Basic.lean`
```lean
@[simp]
theorem toFun_eq_coe {α β} (f : α ↪ β) : toFun f = f :=
  rfl
```

### `Submonoid.coe_mul` (commanddeclaration) at `Mathlib/GroupTheory/Submonoid/Operations.lean`
```lean
@[to_additive (attr := simp, norm_cast)]
theorem coe_mul (x y : S) : (↑(x * y) : M) = ↑x * ↑y :=
  rfl
```

### `Subgroup.coe_toSubmonoid` (commanddeclaration) at `Mathlib/GroupTheory/Subgroup/Basic.lean`
```lean
@[to_additive (attr := simp)]
theorem coe_toSubmonoid (K : Subgroup G) : (K.toSubmonoid : Set G) = K :=
  rfl
```

### `Units.val_mul` (commanddeclaration) at `Mathlib/Algebra/Group/Units.lean`
```lean
@[to_additive (attr := simp, norm_cast)]
theorem val_mul : (↑(a * b) : α) = a * b :=
  rfl
```

### `Finset.mul_sum` (lemma) at `Mathlib/Algebra/BigOperators/Ring.lean`
```lean
lemma mul_sum (s : Finset ι) (f : ι → α) (a : α) :
    a * ∑ i in s, f i = ∑ i in s, a * f i := map_sum (AddMonoidHom.mulLeft a) _ s
```

### `mul_eq_zero` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/Defs.lean`
```lean
/-- If `α` has no zero divisors, then the product of two elements equals zero iff one of them
equals zero. -/
@[simp]
theorem mul_eq_zero : a * b = 0 ↔ a = 0 ∨ b = 0 :=
  ⟨eq_zero_or_eq_zero_of_mul_eq_zero,
    fun o => o.elim (fun h => mul_eq_zero_of_left h b) (mul_eq_zero_of_right a)⟩
```

### `sub_mul` (stdtacticaliasalias) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
alias sub_mul := mul_sub_right_distrib
```

### `one_mul` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem one_mul : ∀ a : M, 1 * a = a :=
  MulOneClass.one_mul
```

### `Or.resolve_left` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
theorem Or.resolve_left  (h: Or a b) (na : Not a) : b := h.elim (absurd · na) id
```

### `Int.sub_eq_zero` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem sub_eq_zero {a b : Int} : a - b = 0 ↔ a = b :=
  ⟨Int.eq_of_sub_eq_zero, Int.sub_eq_zero_of_eq⟩
```
