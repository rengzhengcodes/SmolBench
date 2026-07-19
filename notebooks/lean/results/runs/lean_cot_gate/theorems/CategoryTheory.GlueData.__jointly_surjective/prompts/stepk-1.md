## Current goal
```
⊢ ∃ i y, F.map (ι D i) y = x
```

## Full tactic state
```
case intro.intro
C : Type u₁
inst✝⁵ : Category.{v, u₁} C
C' : Type u₂
inst✝⁴ : Category.{v, u₂} C'
D : GlueData C
F✝ : C ⥤ C'
H : (i j k : D.J) → PreservesLimit (cospan (D.f i j) (D.f i k)) F✝
inst✝³ : HasMulticoequalizer (diagram D)
inst✝² : PreservesColimit (MultispanIndex.multispan (diagram D)) F✝
F : C ⥤ Type v
inst✝¹ : PreservesColimit (MultispanIndex.multispan (diagram D)) F
inst✝ : (i j k : D.J) → PreservesLimit (cospan (D.f i j) (D.f i k)) F
x : F.obj (glued D)
e : F.obj (glued D) ≅ glued (mapGlueData D F) := gluedIso D F
i : (mapGlueData D F).J
y : (mapGlueData D F).U i
eq : F.map (ι D i) y = 𝟙 (F.obj (glued D)) x
⊢ ∃ i y, F.map (ι D i) y = x
```
