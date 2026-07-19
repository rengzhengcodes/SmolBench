## Current goal
```
⊢ η.app (op (op X).unop) (val p) = yonedaEquiv s
```

## Full tactic state
```
C : Type u
inst✝ : Category.{v, u} C
A : Cᵒᵖ ⥤ Type v
Y : C
η : yoneda.obj Y ⟶ A
X : C
s : yoneda.obj X ⟶ A
p : OverArrows η s
⊢ η.app (op (op X).unop) (val p) = yonedaEquiv s
```
