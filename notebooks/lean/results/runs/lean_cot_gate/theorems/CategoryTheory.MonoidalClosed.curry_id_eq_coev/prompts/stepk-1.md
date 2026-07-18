## Current goal
```
⊢ (ihom.coev A).app ((𝟭 C).obj X) ≫ 𝟙 ((ihom A).obj (A ⊗ (𝟭 C).obj X)) = (ihom.coev A).app X
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : MonoidalCategory C
A B X X' Y Y' Z : C
inst✝ : Closed A
⊢ (ihom.coev A).app ((𝟭 C).obj X) ≫ 𝟙 ((ihom A).obj (A ⊗ (𝟭 C).obj X)) = (ihom.coev A).app X
```
