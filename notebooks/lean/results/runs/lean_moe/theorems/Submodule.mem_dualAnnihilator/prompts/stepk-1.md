## Current goal
```
⊢ (∀ (x : ↥W), φ ↑x = 0 x) ↔ ∀ w ∈ W, φ w = 0
```

## Full tactic state
```
R : Type u
M : Type v
inst✝² : CommSemiring R
inst✝¹ : AddCommMonoid M
inst✝ : Module R M
W : Submodule R M
φ : Module.Dual R M
⊢ (∀ (x : ↥W), φ ↑x = 0 x) ↔ ∀ w ∈ W, φ w = 0
```
