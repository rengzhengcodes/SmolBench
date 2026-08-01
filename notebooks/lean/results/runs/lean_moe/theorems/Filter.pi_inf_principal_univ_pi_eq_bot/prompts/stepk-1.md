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
