## Current goal
```
⊢ Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f)
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
⊢ Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Polynomial.roots_expand_image_iterateFrobenius` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `Finset.image_toFinset`
- `Polynomial.roots_expand_pow_map_iterateFrobenius`
- `Polynomial.roots`
- `Multiset.toFinset_nsmul`
- `expChar_pow_pos`
- `LT.lt.ne'`

## Premise signatures
### `Finset.image_toFinset` (commanddeclaration)
```lean
theorem image_toFinset [DecidableEq α] {s : Multiset α} :
    s.toFinset.image f = (s.map f).toFinset
```

### `Polynomial.roots_expand_pow_map_iterateFrobenius` (commanddeclaration)
```lean
theorem roots_expand_pow_map_iterateFrobenius :
    (expand R (p ^ n) f).roots.map (iterateFrobenius R p n) = p ^ n • f.roots
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

### `expChar_pow_pos` (commanddeclaration)
```lean
theorem expChar_pow_pos (q : ℕ) [ExpChar R q] (n : ℕ) : 0 < q ^ n
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

### `Polynomial.roots_expand_pow_map_iterateFrobenius` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem roots_expand_pow_map_iterateFrobenius :
    (expand R (p ^ n) f).roots.map (iterateFrobenius R p n) = p ^ n • f.roots := by
  simp_rw [← coe_iterateFrobeniusEquiv, roots_expand_pow, Multiset.map_nsmul,
    Multiset.map_map, comp_apply, RingEquiv.apply_symm_apply, map_id']
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

### `expChar_pow_pos` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- Any power of the exponential characteristic is positive. -/
theorem expChar_pow_pos (q : ℕ) [ExpChar R q] (n : ℕ) : 0 < q ^ n :=
  Nat.pos_pow_of_pos n (expChar_pos R q)
```

### `LT.lt.ne'` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem ne' [Preorder α] {x y : α} (h : x < y) : y ≠ x :=
  h.ne.symm
```

## Transitive premise context (1-hop, 27/27 premises, ≈3320 tokens)
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

### `iterateFrobenius` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The iterated frobenius map sending x to x^p^n -/
def iterateFrobenius : R →+* R where
  __ := powMonoidHom (p ^ n)
  map_zero' := zero_pow (expChar_pow_pos R p n).ne'
  map_add' := add_pow_expChar_pow R
```

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

### `RingEquiv.apply_symm_apply` (commanddeclaration) at `Mathlib/Algebra/Ring/Equiv.lean`
```lean
@[simp]
theorem apply_symm_apply (e : R ≃+* S) : ∀ x, e (e.symm x) = x :=
  e.toEquiv.apply_symm_apply
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

### `Nat.pos_pow_of_pos` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem pos_pow_of_pos {n : Nat} (m : Nat) (h : 0 < n) : 0 < n^m :=
  pow_le_pow_of_le_right h (Nat.zero_le _)

/-! # min/max -/

/--
`Nat.min a b` is the minimum of `a` and `b`:
* if `a ≤ b` then `Nat.min a b = a`
* if `b ≤ a` then `Nat.min a b = b`
-/
```

### `expChar_pos` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- The exponential characteristic is positive. -/
theorem expChar_pos (q : ℕ) [ExpChar R q] : 0 < q := by
  rcases expChar_is_prime_or_one R q with h | rfl
  exacts [Nat.Prime.pos h, Nat.one_pos]

/-- Any power of the exponential characteristic is positive. -/
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
