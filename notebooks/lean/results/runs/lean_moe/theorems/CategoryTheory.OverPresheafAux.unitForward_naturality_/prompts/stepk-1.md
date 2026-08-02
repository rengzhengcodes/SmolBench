## Current goal
```
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```

## Full tactic state
```
C : Type u
inst✝ : Category.{v, u} C
A F G : Cᵒᵖ ⥤ Type v
η : F ⟶ A
μ : G ⟶ A
ε : F ⟶ G
hε : ε ≫ μ = η
X : C
p : YonedaCollection (restrictedYonedaObj η) X
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```
