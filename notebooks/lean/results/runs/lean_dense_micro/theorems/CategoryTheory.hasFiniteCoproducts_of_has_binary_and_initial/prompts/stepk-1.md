## Current goal
```
⊢ HasColimit K
```

## Full tactic state
```
J : Type v
inst✝⁴ : SmallCategory J
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasBinaryCoproducts C
inst✝ : HasInitial C
n : ℕ
K : Discrete (Fin n) ⥤ C
this : HasCoproduct fun n_1 => K.obj { as := n_1 } := CategoryTheory.hasCoproduct_fin n fun n_1 => K.obj { as := n_1 }
that : K ≅ Discrete.functor fun n_1 => K.obj { as := n_1 } :=
  Discrete.natIso fun x =>
    match x with
    | { as := i } => Iso.refl (K.obj { as := i })
⊢ HasColimit K
```
