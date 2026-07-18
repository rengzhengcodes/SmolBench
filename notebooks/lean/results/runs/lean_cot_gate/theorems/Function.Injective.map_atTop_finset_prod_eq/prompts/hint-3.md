## Current goal
```
⊢ ∃ u', s ⊆ u' ∧ ∏ x in u', f (g x) = ∏ x in Finset.preimage t g ⋯, f (g x)
```

## Full tactic state
```
case a
ι : Type u_1
ι' : Type u_2
α : Type u_3
β : Type u_4
γ : Type u_5
inst✝ : CommMonoid α
g : γ → β
hg : Injective g
f : β → α
hf : ∀ x ∉ Set.range g, f x = 1
this : DecidableEq β
s : Finset γ
t : Finset β
ht : Finset.image g s ⊆ t
⊢ ∃ u', s ⊆ u' ∧ ∏ x in u', f (g x) = ∏ x in Finset.preimage t g ⋯, f (g x)
```

## Proof so far (12 tactics)
```lean
haveI := Classical.decEq β
apply le_antisymm <;> refine' map_atTop_finset_prod_le_of_prod_eq fun s => _
refine' ⟨s.preimage g (hg.injOn _), fun t ht => _⟩
refine' ⟨t.image g ∪ s, Finset.subset_union_right _ _, _⟩
rw [← Finset.prod_image (hg.injOn _)]
refine' (prod_subset (subset_union_left _ _) _).symm
simp only [Finset.mem_union, Finset.mem_image]
refine' fun y hy hyt => hf y (mt _ hyt)
rintro ⟨x, rfl⟩
exact ⟨x, ht (Finset.mem_preimage.2 <| hy.resolve_left hyt), rfl⟩
refine' ⟨s.image g, fun t ht => _⟩
simp only [← prod_preimage _ _ (hg.injOn _) _ fun x _ => hf x]
```

## Theorem
`Function.Injective.map_atTop_finset_prod_eq` in `Mathlib/Order/Filter/AtTopBot.lean`

## Premises used in the next tactic
- `Finset.image_subset_iff_subset_preimage`
- `rfl`

## Premise signatures
### `Finset.image_subset_iff_subset_preimage` (commanddeclaration)
```lean
theorem image_subset_iff_subset_preimage [DecidableEq β] {f : α → β} {s : Finset α} {t : Finset β}
    (hf : Set.InjOn f (f ⁻¹' ↑t)) : s.image f ⊆ t ↔ s ⊆ t.preimage f hf
```

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

## Premise full source (with proof)
### `Finset.image_subset_iff_subset_preimage` (commanddeclaration) at `Mathlib/Data/Finset/Preimage.lean`
```lean
theorem image_subset_iff_subset_preimage [DecidableEq β] {f : α → β} {s : Finset α} {t : Finset β}
    (hf : Set.InjOn f (f ⁻¹' ↑t)) : s.image f ⊆ t ↔ s ⊆ t.preimage f hf :=
  image_subset_iff.trans <| by simp only [subset_iff, mem_preimage]
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

## Transitive premise context (1-hop, 5/5 premises, ≈978 tokens)
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

### `Finset` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
/-- `Finset α` is the type of finite sets of elements of `α`. It is implemented
  as a multiset (a list up to permutation) which has no duplicate elements. -/
structure Finset (α : Type*) where
  /-- The underlying multiset -/
  val : Multiset α
  /-- `val` contains no duplicates -/
  nodup : Nodup val
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

### `Set.InjOn` (commanddeclaration) at `Mathlib/Data/Set/Defs.lean`
```lean
/-- `f` is injective on `a` if the restriction of `f` to `a` is injective. -/
def InjOn (f : α → β) (s : Set α) : Prop :=
  ∀ ⦃x₁ : α⦄, x₁ ∈ s → ∀ ⦃x₂ : α⦄, x₂ ∈ s → f x₁ = f x₂ → x₁ = x₂
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
