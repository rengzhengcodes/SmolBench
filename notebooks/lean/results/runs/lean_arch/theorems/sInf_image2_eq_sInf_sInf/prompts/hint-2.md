## Current goal
```
⊢ sInf (image2 u s t) = u (sInf s) (sInf t)
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type w
ι : Sort x
κ : ι → Sort u_1
a a₁ a₂ : α
b b₁ b₂ : β
inst✝² : CompleteLattice α
inst✝¹ : CompleteLattice β
inst✝ : CompleteLattice γ
f : α → β → γ
s : Set α
t : Set β
l u : α → β → γ
l₁ u₁ : β → γ → α
l₂ u₂ : α → γ → β
h₁ : ∀ (b : β), GaloisConnection (l₁ b) (swap u b)
h₂ : ∀ (a : α), GaloisConnection (l₂ a) (u a)
⊢ sInf (image2 u s t) = u (sInf s) (sInf t)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`sInf_image2_eq_sInf_sInf` in `Mathlib/Order/GaloisConnection.lean`

## Premises used in the next tactic
- `sInf_image2`
- `GaloisConnection.u_sInf`
- `GaloisConnection.u_sInf`

## Premise signatures
### `sInf_image2` (commanddeclaration)
```lean
theorem sInf_image2 {f : β → γ → α} {s : Set β} {t : Set γ} :
    sInf (image2 f s t) = ⨅ (a ∈ s) (b ∈ t), f a b
```

### `GaloisConnection.u_sInf` (commanddeclaration)
```lean
theorem u_sInf {s : Set β} : u (sInf s) = ⨅ a ∈ s, u a
```

### `GaloisConnection.u_sInf` (commanddeclaration)
```lean
theorem u_sInf {s : Set β} : u (sInf s) = ⨅ a ∈ s, u a
```

## Premise full source (with proof)
### `sInf_image2` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem sInf_image2 {f : β → γ → α} {s : Set β} {t : Set γ} :
    sInf (image2 f s t) = ⨅ (a ∈ s) (b ∈ t), f a b := by rw [← image_prod, sInf_image, biInf_prod]
```

### `GaloisConnection.u_sInf` (commanddeclaration) at `Mathlib/Order/GaloisConnection.lean`
```lean
theorem u_sInf {s : Set β} : u (sInf s) = ⨅ a ∈ s, u a :=
  gc.dual.l_sSup
```

### `GaloisConnection.u_sInf` (commanddeclaration) at `Mathlib/Order/GaloisConnection.lean`
```lean
theorem u_sInf {s : Set β} : u (sInf s) = ⨅ a ∈ s, u a :=
  gc.dual.l_sSup
```
