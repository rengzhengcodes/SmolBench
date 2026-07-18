## Current goal
```
⊢ (Set.pi univ s)ᶜ ∈ pi f
```

## Full tactic state
```
case mpr.intro
ι : Type u_1
α : ι → Type u_2
f f₁ f₂ : (i : ι) → Filter (α i)
s : (i : ι) → Set (α i)
p : (i : ι) → α i → Prop
i : ι
hi : (s i)ᶜ ∈ f i
⊢ (Set.pi univ s)ᶜ ∈ pi f
```

## Proof so far (9 tactics)
```lean
constructor
simp only [inf_principal_eq_bot, mem_pi]
contrapose!
rintro (hsf : ∀ i, ∃ᶠ x in f i, x ∈ s i) I - t htf hts
have : ∀ i, (s i ∩ t i).Nonempty := fun i => ((hsf i).and_eventually (htf i)).exists
choose x hxs hxt using this
exact hts (fun i _ => hxt i) (mem_univ_pi.2 hxs)
simp only [inf_principal_eq_bot]
rintro ⟨i, hi⟩
```

## Theorem
`Filter.pi_inf_principal_univ_pi_eq_bot` in `Mathlib/Order/Filter/Pi.lean`

## Premises used in the next tactic
- `Filter.mem_pi_of_mem`
- `mt`
- `trivial`

## Premise signatures
### `Filter.mem_pi_of_mem` (commanddeclaration)
```lean
theorem mem_pi_of_mem (i : ι) {s : Set (α i)} (hs : s ∈ f i) : eval i ⁻¹' s ∈ pi f
```

### `mt` (commanddeclaration)
```lean
theorem mt {a b : Prop} (h₁ : a → b) (h₂ : ¬b) : ¬a
```

### `trivial` (commanddeclaration)
```lean
@[inherit_doc True.intro] def trivial : True
```

## Premise full source (with proof)
### `Filter.mem_pi_of_mem` (commanddeclaration) at `Mathlib/Order/Filter/Pi.lean`
```lean
theorem mem_pi_of_mem (i : ι) {s : Set (α i)} (hs : s ∈ f i) : eval i ⁻¹' s ∈ pi f :=
  mem_iInf_of_mem i <| preimage_mem_comap hs
```

### `mt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem mt {a b : Prop} (h₁ : a → b) (h₂ : ¬b) : ¬a :=
  fun ha => h₂ (h₁ ha)
```

### `trivial` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[inherit_doc True.intro] def trivial : True := ⟨⟩
```

## Transitive premise context (1-hop, 2/2 premises, ≈148 tokens)
### `Filter.mem_iInf_of_mem` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem mem_iInf_of_mem {f : ι → Filter α} (i : ι) {s} (hs : s ∈ f i) : s ∈ ⨅ i, f i :=
  iInf_le f i hs
```

### `Filter.preimage_mem_comap` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem preimage_mem_comap (ht : t ∈ g) : m ⁻¹' t ∈ comap m g :=
  ⟨t, ht, Subset.rfl⟩
```
