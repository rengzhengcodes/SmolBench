## Current goal
```
⊢ ∃ i_1 y_1, (ι f i_1) y_1 = (ι f i) y
```

## Full tactic state
```
case inr.intro.intro
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : ConcreteCategory C
B : C
α : Type v
inst✝² : Nonempty α
X : α → C
f : (j : α) → B ⟶ X j
inst✝¹ : HasWidePushout B X f
inst✝ : PreservesColimit (wideSpan B X f) (forget C)
i : α
y : (forget C).obj (X i)
⊢ ∃ i_1 y_1, (ι f i_1) y_1 = (ι f i) y
```
