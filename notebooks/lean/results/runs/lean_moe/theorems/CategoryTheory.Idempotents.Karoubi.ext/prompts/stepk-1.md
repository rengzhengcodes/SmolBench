## Current goal
```
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```

## Full tactic state
```
case mk.mk
C : Type u_1
inst✝ : Category.{u_2, u_1} C
X✝ : C
p✝¹ : X✝ ⟶ X✝
idem✝¹ : p✝¹ ≫ p✝¹ = p✝¹
p✝ : X✝ ⟶ X✝
idem✝ : p✝ ≫ p✝ = p✝
h_p : p✝¹ ≫ eqToHom ⋯ = eqToHom ⋯ ≫ p✝
⊢ { X := X✝, p := p✝¹, idem := idem✝¹ } = { X := X✝, p := p✝, idem := idem✝ }
```
