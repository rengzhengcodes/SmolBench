## Current goal
```
⊢ Submodule.map (LinearMap.snd R F E) (Submodule.map (LinearEquiv.prodComm R E F) (graph f)) =
    Submodule.map (LinearMap.snd R F E) (Submodule.map (↑(LinearEquiv.prodComm R E F)) (graph f))
```

## Full tactic state
```
R : Type u_1
inst✝⁶ : Ring R
E : Type u_2
inst✝⁵ : AddCommGroup E
inst✝⁴ : Module R E
F : Type u_3
inst✝³ : AddCommGroup F
inst✝² : Module R F
G : Type u_4
inst✝¹ : AddCommGroup G
inst✝ : Module R G
f : E →ₗ.[R] F
hf : LinearMap.ker f.toFun = ⊥
⊢ Submodule.map (LinearMap.snd R F E) (Submodule.map (LinearEquiv.prodComm R E F) (graph f)) =
    Submodule.map (LinearMap.snd R F E) (Submodule.map (↑(LinearEquiv.prodComm R E F)) (graph f))
```
