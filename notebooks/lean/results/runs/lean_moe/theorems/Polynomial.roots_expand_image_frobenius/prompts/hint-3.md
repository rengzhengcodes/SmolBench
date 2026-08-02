## Current goal
```
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
```

## Full tactic state
```
R : Type u_1
inst✝⁴ : CommRing R
inst✝³ : IsDomain R
p n : ℕ
inst✝² : ExpChar R p
f : R[X]
inst✝¹ : PerfectRing R p
inst✝ : DecidableEq R
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Polynomial.roots_expand_image_frobenius` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `Finset.image_toFinset`
- `Polynomial.roots_expand_map_frobenius`
- `Polynomial.roots`
- `Multiset.toFinset_nsmul`
- `expChar_pos`
- `LT.lt.ne'`

## Premise signatures
### `Finset.image_toFinset` (commanddeclaration)
```lean
theorem image_toFinset [DecidableEq α] {s : Multiset α} :
    s.toFinset.image f = (s.map f).toFinset
```

### `Polynomial.roots_expand_map_frobenius` (commanddeclaration)
```lean
theorem roots_expand_map_frobenius : (expand R p f).roots.map (frobenius R p) = p • f.roots
```

### `Polynomial.roots` (commanddeclaration)
```lean
noncomputable def roots (p : R[X]) : Multiset R
```

### `Multiset.toFinset_nsmul` (commanddeclaration)
```lean
@[simp]
theorem toFinset_nsmul (s : Multiset α) : ∀ n ≠ 0, (n • s).toFinset = s.toFinset
```

### `expChar_pos` (commanddeclaration)
```lean
theorem expChar_pos (q : ℕ) [ExpChar R q] : 0 < q
```

### `LT.lt.ne'` (commanddeclaration)
```lean
theorem ne' [Preorder α] {x y : α} (h : x < y) : y ≠ x
```

## Premise full source (with proof)
### `Finset.image_toFinset` (commanddeclaration) at `Mathlib/Data/Finset/Image.lean`
```lean
theorem image_toFinset [DecidableEq α] {s : Multiset α} :
    s.toFinset.image f = (s.map f).toFinset :=
  ext fun _ => by simp only [mem_image, Multiset.mem_toFinset, exists_prop, Multiset.mem_map]
```

### `Polynomial.roots_expand_map_frobenius` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem roots_expand_map_frobenius : (expand R p f).roots.map (frobenius R p) = p • f.roots := by
  simp [roots_expand, Multiset.map_nsmul]
```

### `Polynomial.roots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
/-- `roots p` noncomputably gives a multiset containing all the roots of `p`,
including their multiplicities. -/
noncomputable def roots (p : R[X]) : Multiset R :=
  haveI := Classical.decEq R
  haveI := Classical.dec (p = 0)
  if h : p = 0 then ∅ else Classical.choose (exists_multiset_roots h)
```

### `Multiset.toFinset_nsmul` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp]
theorem toFinset_nsmul (s : Multiset α) : ∀ n ≠ 0, (n • s).toFinset = s.toFinset
  | 0, h => by contradiction
  | n + 1, _ => by
    by_cases h : n = 0
    · rw [h, zero_add, one_nsmul]
    · rw [add_nsmul, toFinset_add, one_nsmul, toFinset_nsmul s n h, Finset.union_idempotent]
```

### `expChar_pos` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The exponential characteristic is positive. -/
theorem expChar_pos (q : ℕ) [ExpChar R q] : 0 < q := by
  rcases expChar_is_prime_or_one R q with h | rfl
  exacts [Nat.Prime.pos h, Nat.one_pos]

/-- Any power of the exponential characteristic is positive. -/
```

### `LT.lt.ne'` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem ne' [Preorder α] {x y : α} (h : x < y) : y ≠ x :=
  h.ne.symm
```

## Transitive premise context (1-hop, 25/25 premises, ≈2991 tokens)
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

### `Multiset` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
/-- `Multiset α` is the quotient of `List α` by list permutation. The result
  is a type of finite sets with duplicates allowed.  -/
def Multiset.{u} (α : Type u) : Type u :=
  Quotient (List.isSetoid α)
```

### `Multiset.mem_toFinset` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp]
theorem mem_toFinset {a : α} {s : Multiset α} : a ∈ s.toFinset ↔ a ∈ s :=
  mem_dedup
```

### `exists_prop` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
@[simp] theorem exists_prop : (∃ _h : a, b) ↔ a ∧ b :=
  ⟨fun ⟨hp, hq⟩ => ⟨hp, hq⟩, fun ⟨hp, hq⟩ => ⟨hp, hq⟩⟩
```

### `Multiset.mem_map` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
@[simp]
theorem mem_map {f : α → β} {b : β} {s : Multiset α} : b ∈ map f s ↔ ∃ a, a ∈ s ∧ f a = b :=
  Quot.inductionOn s fun _l => List.mem_map
```

### `frobenius` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The frobenius map that sends x to x^p -/
def frobenius : R →+* R where
  __ := powMonoidHom p
  map_zero' := zero_pow (expChar_pos R p).ne'
  map_add' := add_pow_expChar R
```

### `Polynomial.roots_expand` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem roots_expand : (expand R p f).roots = p • f.roots.map (frobeniusEquiv R p).symm := by
  conv_lhs => rw [← pow_one p, roots_expand_pow, iterateFrobeniusEquiv_eq_pow, pow_one]
```

### `Multiset.map_nsmul` (commanddeclaration) at `Mathlib/Data/Multiset/Basic.lean`
```lean
theorem map_nsmul (f : α → β) (n : ℕ) (s) : map f (n • s) = n • map f s :=
  (mapAddMonoidHom f).map_nsmul _ _
```

### `Denumerable.multiset` (commanddeclaration) at `Mathlib/Logic/Equiv/List.lean`
```lean
/-- If `α` is denumerable, then so is `Multiset α`. Warning: this is *not* the same encoding as used
in `Multiset.encodable`. -/
instance multiset : Denumerable (Multiset α) :=
  mk'
    ⟨fun s : Multiset α => encode <| lower ((s.map encode).sort (· ≤ ·)) 0,
     fun n =>
      Multiset.map (ofNat α) (raise (ofNat (List ℕ) n) 0),
     fun s => by
      have :=
        raise_lower (List.sorted_cons.2 ⟨fun n _ => Nat.zero_le n, (s.map encode).sort_sorted _⟩)
      simp [-Multiset.map_coe, this],
     fun n => by
      simp [-Multiset.map_coe, List.mergeSort_eq_self _ (raise_sorted _ _), lower_raise]⟩
```

### `Lean.Parser.Term.haveI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `haveI` behaves like `have`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «haveI» := leading_parser
  withPosition ("haveI " >> haveDecl) >> optSemicolon termParser
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
```

### `Classical.decEq` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
/-- Any type `α` has decidable equality classically. -/
noncomputable def decEq (α : Sort u) : DecidableEq α := by infer_instance
```

### `Classical.dec` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
/-- Any prop `p` is decidable classically. A shorthand for `Classical.propDecidable`. -/
noncomputable def dec (p : Prop) : Decidable p := by infer_instance
```

### `Classical.choose` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Classical.lean`
```lean
noncomputable def choose {α : Sort u} {p : α → Prop} (h : ∃ x, p x) : α :=
  (indefiniteDescription p h).val
```

### `Polynomial.exists_multiset_roots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
theorem exists_multiset_roots [DecidableEq R] :
    ∀ {p : R[X]} (_ : p ≠ 0), ∃ s : Multiset R,
      (Multiset.card s : WithBot ℕ) ≤ degree p ∧ ∀ a, s.count a = rootMultiplicity a p
  | p, hp =>
    haveI := Classical.propDecidable (∃ x, IsRoot p x)
    if h : ∃ x, IsRoot p x then
      let ⟨x, hx⟩ := h
      have hpd : 0 < degree p := degree_pos_of_root hp hx
      have hd0 : p /ₘ (X - C x) ≠ 0 := fun h => by
        rw [← mul_divByMonic_eq_iff_isRoot.2 hx, h, mul_zero] at hp; exact hp rfl
      have wf : degree (p /ₘ (X - C x)) < degree p :=
        degree_divByMonic_lt _ (monic_X_sub_C x) hp ((degree_X_sub_C x).symm ▸ by decide)
      let ⟨t, htd, htr⟩ := @exists_multiset_roots _ (p /ₘ (X - C x)) hd0
      have hdeg : degree (X - C x) ≤ degree p := by
        rw [degree_X_sub_C, degree_eq_natDegree hp]
        rw [degree_eq_natDegree hp] at hpd
        exact WithBot.coe_le_coe.2 (WithBot.coe_lt_coe.1 hpd)
      have hdiv0 : p /ₘ (X - C x) ≠ 0 :=
        mt (divByMonic_eq_zero_iff (monic_X_sub_C x)).1 <| not_lt.2 hdeg
      ⟨x ::ₘ t,
        calc
          (card (x ::ₘ t) : WithBot ℕ) = Multiset.card t + 1 := by
            congr
            exact mod_cast Multiset.card_cons _ _
          _ ≤ degree p := by
            rw [← degree_add_divByMonic (monic_X_sub_C x) hdeg, degree_X_sub_C, add_comm];
              exact add_le_add (le_refl (1 : WithBot ℕ)) htd,
        by
          change ∀ (a : R), count a (x ::ₘ t) = rootMultiplicity a p
          intro a
          conv_rhs => rw [← mul_divByMonic_eq_iff_isRoot.mpr hx]
          rw [rootMultiplicity_mul (mul_ne_zero (X_sub_C_ne_zero x) hdiv0),
            rootMultiplicity_X_sub_C, ← htr a]
          split_ifs with ha
          · rw [ha, count_cons_self, add_comm]
          · rw [count_cons_of_ne ha, zero_add]⟩
    else
      ⟨0, (degree_eq_natDegree hp).symm ▸ WithBot.coe_le_coe.2 (Nat.zero_le _), by
        intro a
        rw [count_zero, rootMultiplicity_eq_zero (not_exists.mp h a)]⟩
termination_by p => natDegree p
decreasing_by {
  simp_wf
  apply (Nat.cast_lt (α := WithBot ℕ)).mp
  simp only [degree_eq_natDegree hp, degree_eq_natDegree hd0] at wf;
  assumption}
```

### `by_cases` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem by_cases {q : Prop} (hpq : p → q) (hnpq : ¬p → q) : q :=
if hp : p then hpq hp else hnpq hp
```

### `one_nsmul` (commanddeclaration) at `Mathlib/Algebra/GroupPower/Basic.lean`
```lean
@[simp]
theorem one_nsmul (a : A) : 1 • a = a := by rw [succ_nsmul, zero_nsmul, add_zero]
```

### `add_nsmul` (commanddeclaration) at `Mathlib/Algebra/GroupPower/Basic.lean`
```lean
theorem add_nsmul (a : A) (m n : ℕ) : (m + n) • a = m • a + n • a := by
  induction m with
  | zero => rw [Nat.zero_add, zero_nsmul, zero_add]
  | succ m ih => rw [Nat.succ_add, Nat.succ_eq_add_one, succ_nsmul, ih, succ_nsmul, add_assoc]
```

### `Multiset.toFinset_add` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp]
theorem toFinset_add (s t : Multiset α) : toFinset (s + t) = toFinset s ∪ toFinset t :=
  Finset.ext <| by simp
```

### `Finset.union_idempotent` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
@[simp]
theorem union_idempotent (s : Finset α) : s ∪ s = s := sup_idem _
```

### `Subgroup.Centralizer.characteristic` (commanddeclaration) at `Mathlib/GroupTheory/Subgroup/Basic.lean`
```lean
@[to_additive]
instance Centralizer.characteristic [hH : H.Characteristic] :
    (centralizer (H : Set G)).Characteristic := by
  refine' Subgroup.characteristic_iff_comap_le.mpr fun ϕ g hg h hh => ϕ.injective _
  rw [map_mul, map_mul]
  exact hg (ϕ h) (Subgroup.characteristic_iff_le_comap.mp hH ϕ hh)
```

### `ExpChar` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The definition of the exponential characteristic of a semiring. -/
class inductive ExpChar (R : Type u) [Semiring R] : ℕ → Prop
  | zero [CharZero R] : ExpChar R 1
  | prime {q : ℕ} (hprime : q.Prime) [hchar : CharP R q] : ExpChar R q
```

### `expChar_is_prime_or_one` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The exponential characteristic is a prime number or one.
See also `CharP.char_is_prime_or_zero`. -/
theorem expChar_is_prime_or_one (q : ℕ) [hq : ExpChar R q] : Nat.Prime q ∨ q = 1 := by
  cases hq with
  | zero => exact .inr rfl
  | prime hp => exact .inl hp
```

### `Nat.Prime.pos` (commanddeclaration) at `Mathlib/Data/Nat/Prime.lean`
```lean
theorem Prime.pos {p : ℕ} (pp : Prime p) : 0 < p :=
  Nat.pos_of_ne_zero pp.ne_zero
```

### `Nat.one_pos` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected abbrev one_pos := @Nat.zero_lt_one
```

### `Preorder` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
/-- A preorder is a reflexive, transitive relation `≤` with `a < b` defined in the obvious way. -/
class Preorder (α : Type u) extends LE α, LT α where
  le_refl : ∀ a : α, a ≤ a
  le_trans : ∀ a b c : α, a ≤ b → b ≤ c → a ≤ c
  lt := fun a b => a ≤ b ∧ ¬b ≤ a
  lt_iff_le_not_le : ∀ a b : α, a < b ↔ a ≤ b ∧ ¬b ≤ a := by intros; rfl
```
