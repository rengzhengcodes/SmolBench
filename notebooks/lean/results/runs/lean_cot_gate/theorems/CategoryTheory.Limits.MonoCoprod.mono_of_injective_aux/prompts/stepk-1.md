## Current goal
```
⊢ ∀ (i₁ : J),
    (Cofan.inj c₁ i₁ ≫ Cofan.IsColimit.desc hc₁ fun i => Cofan.inj c (ι i)) =
      Cofan.inj (Cofan.mk c.pt fun i' => Cofan.inj c (e i')) (Sum.inl i₁)
```

## Full tactic state
```
C : Type u_1
inst✝¹ : Category.{u_4, u_1} C
inst✝ : MonoCoprod C
I : Type u_2
J : Type u_3
X : I → C
ι : J → I
hι : Function.Injective ι
c : Cofan X
c₁ : Cofan (X ∘ ι)
hc : IsColimit c
hc₁ : IsColimit c₁
c₂ : Cofan fun k => X ↑k
hc₂ : IsColimit c₂
e : J ⊕ ↑(Set.range ι)ᶜ ≃ I :=
  (Equiv.sumCongr (Equiv.ofInjective ι hι) (Equiv.refl ↑(Set.range ι)ᶜ)).trans (Equiv.Set.sumCompl (Set.range ι))
⊢ ∀ (i₁ : J),
    (Cofan.inj c₁ i₁ ≫ Cofan.IsColimit.desc hc₁ fun i => Cofan.inj c (ι i)) =
      Cofan.inj (Cofan.mk c.pt fun i' => Cofan.inj c (e i')) (Sum.inl i₁)
```
