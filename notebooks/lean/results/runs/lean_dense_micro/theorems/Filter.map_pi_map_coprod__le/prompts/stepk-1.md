## Current goal
```
⊢ ∃ t₁ ∈ f i, eval i ⁻¹' t₁ ⊆ (fun k i => m i (k i)) ⁻¹' s
```

## Full tactic state
```
case intro.intro
ι : Type u_1
α : ι → Type u_2
f f₁ f₂ : (i : ι) → Filter (α i)
s✝ : (i : ι) → Set (α i)
p : (i : ι) → α i → Prop
β : ι → Type u_3
m : (i : ι) → α i → β i
s : Set ((i : ι) → β i)
h : ∀ (i : ι), ∃ t₁, m i ⁻¹' t₁ ∈ f i ∧ eval i ⁻¹' t₁ ⊆ s
i : ι
t : Set (β i)
H : m i ⁻¹' t ∈ f i
hH : eval i ⁻¹' t ⊆ s
⊢ ∃ t₁ ∈ f i, eval i ⁻¹' t₁ ⊆ (fun k i => m i (k i)) ⁻¹' s
```
