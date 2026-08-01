## Current goal
```
⊢ colimit.ι ((CategoryOfElements.π Y).leftOp ⋙ A)
      (Opposite.op { fst := J.unop.fst, snd := f.app J.unop.fst J.unop.snd }) =
    colimit.ι ((CategoryOfElements.π Y).leftOp ⋙ A) (Opposite.op ((CategoryOfElements.map f).obj J.unop))
```

## Full tactic state
```
case w
C : Type u₁
inst✝² : SmallCategory C
ℰ : Type u₂
inst✝¹ : Category.{u₁, u₂} ℰ
A : C ⥤ ℰ
inst✝ : HasColimits ℰ
X Y : Cᵒᵖ ⥤ Type u₁
f : X ⟶ Y
J : (Functor.Elements X)ᵒᵖ
⊢ colimit.ι ((CategoryOfElements.π Y).leftOp ⋙ A)
      (Opposite.op { fst := J.unop.fst, snd := f.app J.unop.fst J.unop.snd }) =
    colimit.ι ((CategoryOfElements.π Y).leftOp ⋙ A) (Opposite.op ((CategoryOfElements.map f).obj J.unop))
```
