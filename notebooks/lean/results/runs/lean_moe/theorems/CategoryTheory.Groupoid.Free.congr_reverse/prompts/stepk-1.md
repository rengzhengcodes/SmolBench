## Current goal
```
⊢ redStep (𝟙 (Paths.of.obj X✝)) (Quiver.Hom.toPath f ≫ Quiver.Hom.toPath (Quiver.reverse f))
```

## Full tactic state
```
case h
V : Type u
inst✝ : Quiver V
X✝¹ Y✝ X Y : Paths (Quiver.Symmetrify V)
X✝ Z : Quiver.Symmetrify V
f : X✝ ⟶ Z
XW : X✝¹ ⟶ Paths.of.obj X✝
WY : Paths.of.obj X✝ ⟶ Y✝
⊢ redStep (𝟙 (Paths.of.obj X✝)) (Quiver.Hom.toPath f ≫ Quiver.Hom.toPath (Quiver.reverse f))
```
