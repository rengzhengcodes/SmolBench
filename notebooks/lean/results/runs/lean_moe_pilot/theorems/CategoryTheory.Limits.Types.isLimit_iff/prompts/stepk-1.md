## Current goal
```
⊢ IsLimit c
```

## Full tactic state
```
case refine_2
J : Type v
inst✝ : Category.{w, v} J
F : J ⥤ Type u
c : Cone F
h : ∀ s ∈ Functor.sections F, ∃! x, ∀ (j : J), c.π.app j x = s j
x : (c_1 : Cone F) → c_1.pt → c.pt
hx :
  ∀ (c_1 : Cone F) (y : c_1.pt),
    (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) (x c_1 y) ∧
      ∀ (y_1 : c.pt), (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c_1 y) j) y_1 → y_1 = x c_1 y
⊢ IsLimit c
```
