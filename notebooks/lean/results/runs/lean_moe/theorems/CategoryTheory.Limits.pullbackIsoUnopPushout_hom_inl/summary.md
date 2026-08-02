# CategoryTheory.Limits.pullbackIsoUnopPushout_hom_inl   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Limits/Opposites.lean`  

**Ground-truth tail (from k):**
```lean
rw [← pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]
```

**True premises at k:** `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst`, `CategoryTheory.Iso.hom_inv_id_assoc`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=383, out=831)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (pullbackIsoUnopPushout_hom_fst (f:=f) (g:=g))
```

**lean_error:** tail step 1/1 ('simpa using (pullbackIsoUnopPushout_hom_fst (f:=f) (g:=g))'): unknown identifier 'pullbackIsoUnopPushout_hom_fst'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 72.6s, verify 0.1s, in=332, out=8431)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact pullbackIsoUnopPushout_hom_inl f g
```

**lean_error:** tail step 1/1 ('exact pullbackIsoUnopPushout_hom_inl f g'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.3s, verify 0.1s, in=323, out=485)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout]
```

**final state (truncated):**
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 21.8s, verify 0.1s, in=849, out=5286)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullbackIsoUnopPushout_inv_fst, Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [pullbackIsoUnopPushout_inv_fst, Category.assoc]'): simp made no progress

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 42.8s, verify 0.1s, in=819, out=4959)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : pushout.inl.unop = (pullbackIsoUnopPushout f g).inv ≫ pullback.fst := by
  rw [← pullbackIsoUnopPushout_inv_fst]
rw [h₁]
rw [← Category.comp_assoc]
have h₂ : (pullbackIsoUnopPushout f g).hom ≫ (pullbackIsoUnopPushout f g).inv = 𝟙 (pullback f g) := by
  exact CategoryTheory.Iso.hom_inv_id (pullbackIsoUnopPushout f g)
rw [h₂]
simp [Category.comp_id]
```

**lean_error:** tail step 1/8 ('have h₁ : pushout.inl.unop = (pullbackIsoUnopPushout f g).inv ≫ pullback.fst := by'): <stdin>:1:82: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.2s, in=792, out=744)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]
rw [pullbackIsoUnopPushout_inv_fst f g]
```

**lean_error:** tail step 1/2 ('rw [← Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 25.3s, verify 0.3s, in=1496, out=6251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h' :
      pushout.inl =
        (pullback.fst).unop ≫ (pullbackIsoUnopPushout f g).hom := by
    simpa using
      congrArg Quiver.Hom.unop (pullbackIsoUnopPushout_inv_fst (f:=f) (g:=g))
  simpa [h', Category.assoc, Iso.hom_inv_id]
```

**lean_error:** tail step 1/6 ("have h' :"): <stdin>:1:9: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 182.6s, verify 0.2s, in=1477, out=21455)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : (pullbackIsoUnopPushout f g).inv ≫ pullback.fst = pushout.inl.unop := pullbackIsoUnopPushout_inv_fst f g
have h₂ : (pullback.fst).unop ≫ (pullbackIsoUnopPushout f g).inv.unop = pushout.inl := by
  have h₂₁ : ((pullbackIsoUnopPushout f g).inv ≫ pullback.fst).unop = (pushout.inl.unop).unop := by rw [h₁]
  have h₂₂ : ((pullbackIsoUnopPushout f g).inv ≫ pullback.fst).unop = (pullback.fst).unop ≫ (pullbackIsoUnopPushout f g).inv.unop := by
    simp [Category.comp_unop]
  have h₂₃ : (pushout.inl.unop).unop = pushout.inl := by simp
  rw [h₂₂] at h₂₁
  rw [h₂₃] at h₂₁
  exact h₂₁
have h₃ : pushout.inl ≫ (pullbackIsoUnopPushout f g).hom.unop = (pullback.fst).unop := by
  calc
    pushout.inl ≫ (pullbackIsoUnopPushout f g).hom.unop = ((pullback.fst).unop ≫ (pullbackIsoUnopPushout f g).inv.unop) ≫ (pullbackIsoUnopPushout f g).hom.unop := by rw [h₂]
    _ = (pullback.fst).unop ≫ ((pullbackIsoUnopPushout f g).inv.unop ≫ (pullbackIsoUnopPushout f g).hom.unop) := by
      simp [Category.comp_assoc]
    _ = (pullback.fst).unop ≫ 𝟙 _ := by
      have h₃₁ : (pullbackIsoUnopPushout f g).inv.unop ≫ (pullbackIsoUnopPushout f g).hom.unop = 𝟙 := by
        have h₃₂ : (pullbackIsoUnopPushout f g).hom ≫ (pullbackIsoUnopPushout f g).inv = 𝟙 := by
          apply Category.ext
          simp [Category.Iso.hom_comp_inv]
        calc
          (pullbackIsoUnopPushout f g).inv.unop ≫ (pullbackIsoUnopPushout f g).hom.unop = ((pullbackIsoUnopPushout f g).hom ≫ (pullbackIsoUnopPushout f g).inv).unop := by
            rw [← Category.comp_unop]
            <;> simp [Category.comp_unop]
          _ = (𝟙 : (pullback f g) ⟶ (pullback f g)).unop := by rw [h₃₂]
          _ = 𝟙 := by
            simp [Category.unop_id]
      rw [h₃₁]
    _ = (pullback.fst).unop := by simp [Category.comp_id]
exact h₃
```

**lean_error:** tail step 2/29 ('have h₂ : (pullback.fst).unop ≫ (pullbackIsoUnopPushout f g).inv.unop = pushout.inl := by'): <stdin>:1:89: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=1440, out=522)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]
rw [pullbackIsoUnopPushout_inv_fst f g]
```

**lean_error:** tail step 1/2 ('rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]'): tactic 'rewrite' failed, pattern is a metavariable

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=1438, out=2345)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Category.assoc] using
  (Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g) pullback.fst)
```

**lean_error:** tail step 1/2 ('simpa [Category.assoc] using'): <stdin>:1:28: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 84.7s, verify 0.1s, in=1583, out=10123)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = (pullbackIsoUnopPushout f g).hom ≫ ((pullbackIsoUnopPushout f g).inv ≫ pullback.fst) := by
    rw [pullbackIsoUnopPushout_inv_fst]
  _ = ((pullbackIsoUnopPushout f g).hom ≫ (pullbackIsoUnopPushout f g).inv) ≫ pullback.fst := by
    rw [← CategoryTheory.comp_assoc]
  _ = (𝟙 (pullback f g)) ≫ pullback.fst := by
    rw [CategoryTheory.Iso.hom_inv_id]
  _ = pullback.fst := by
    simp [CategoryTheory.comp_id]
```

**lean_error:** tail step 1/9 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=1445, out=699)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]
rw [pullbackIsoUnopPushout_inv_fst f g]
```

**lean_error:** tail step 1/2 ('rw [← CategoryTheory.Iso.hom_inv_id_assoc (pullbackIsoUnopPushout f g)]'): tactic 'rewrite' failed, pattern is a metavariable
