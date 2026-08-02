# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.3s, verify 0.5s, in=508, out=1225)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 248.2s, verify 0.1s, in=456, out=29550)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.3s, in=442, out=517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
<;> simp [pullbackFstFstIso, map]
<;> rw [category.assoc]
<;> simp
```

**lean_error:** tail step 2/4 ('<;> simp [pullbackFstFstIso, map]'): <stdin>:1:0: expected tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 13.3s, verify 0.6s, in=980, out=2764)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
· simp [map, pullbackFstFstIso, Category.assoc]
· simp [map, pullbackFstFstIso, Category.assoc]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 194.2s, verify 0.2s, in=952, out=22331)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.pullbackFstFstIso_inv]
<;> simp_all [CategoryTheory.Limits.pullback.lift_snd_assoc, CategoryTheory.Limits.pullback.lift_fst]
```

**lean_error:** tail step 2/2 ('<;> simp_all [CategoryTheory.Limits.pullback.lift_snd_assoc, CategoryTheory.Limits.pullback.lift_fst]'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=906, out=553)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;> simp [pullbackFstFstIso, pullback.map, CategoryTheory.iso.inv_eq_symm]
<;> associativity
<;> simp_all [pullback.lift_fst, pullback.lift_snd]
<;> category
```

**lean_error:** tail step 1/4 ('ext <;> simp [pullbackFstFstIso, pullback.map, CategoryTheory.iso.inv_eq_symm]'): unknown identifier 'CategoryTheory.iso.inv_eq_symm'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.6s, verify 0.5s, in=1122, out=3265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext
· simp [Category.assoc]
· simp [Category.assoc]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 146.4s, verify 0.1s, in=1095, out=16575)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : (map f g f' g' i₁ i₂ i₃ e₁ e₂) ≫ (pullback f' g').fst = i₁ ≫ (pullback f g).fst := by sorry
have h2 : (map f g f' g' i₁ i₂ i₃ e₁ e₂) ≫ (pullback f' g').snd = i₂ ≫ (pullback f g).snd := by sorry
have h3 : ((pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst) ≫ (pullback f' g').fst = i₁ ≫ (pullback f g).fst := by sorry
have h4 : ((pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst) ≫ (pullback f' g').snd = i₂ ≫ (pullback f g).snd := by sorry
have h5 : map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst := by sorry
exact h5
```

**lean_error:** tail step 1/6 ("have h1 : (map f g f' g' i₁ i₂ i₃ e₁ e₂) ≫ (pullback f' g').fst = i₁ ≫ (pullback f g).fst := by sorry"): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.7s, verify 0.2s, in=1046, out=560)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <;> simp [pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.4s, verify 0.2s, in=1128, out=1750)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 165.6s, verify 0.1s, in=1138, out=18919)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv {C : Type u_1} [Category.{u_2, u_1} C] {X✝ Y✝ Z : C} {inst✝¹ : HasPullbacks C} {X Y S X' Y' S' : C} {f : X ⟶ S} {g : Y ⟶ S} {f' : X' ⟶ S'} {g' : Y' ⟶ S'} {i₁ : X ⟶ X'} {i₂ : Y ⟶ Y'} {i₃ : S ⟶ S'} {e₁ : f ≫ i₃ = i₁ ≫ f'} {e₂ : g ≫ i₃ = i₂ ≫ g'} {inst✝ : Mono i₃} :
    map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst := by
  have h₁ : (map f g f' g' i₁ i₂ i₃ e₁ e₂) ≫ pullback.fst' = i₁ ≫ pullback.fst := by sorry
  have h₂ : (map f g f' g' i₁ i₂ i₃ e₁ e₂) ≫ pullback.snd' = i₂ ≫ pullback.snd := by sorry
  have h₃ : ((pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst) ≫ pullback.fst' = i₁ ≫ pullback.fst := by sorry
  have h₄ : ((pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst) ≫ pullback.snd' = i₂ ≫ pullback.snd := by sorry
  have h₅ : map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst := by sorry
  exact h₅
```

**lean_error:** tail step 1/8 ("theorem CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv {C : Type u_1} [Category.{u_2, u_1} C] {X✝ Y✝ Z : C} {inst✝¹ : HasPullbacks C} {X Y S X' Y' S' : C} {f : X ⟶ S} {g : Y ⟶ S} {f' : X' ⟶ S'} {g' : Y' ⟶ S'} {i₁ : X ⟶ X'} {i₂ : Y ⟶ Y'} {i₃ : S ⟶ S'} {e₁ : f ≫ i₃ = i₁ ≫ 

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=1067, out=490)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst, CategoryTheory.assoc]
```

**lean_error:** tail step 1/1 ('ext <;> simp [pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst, CategoryTheory.assoc]'): unknown identifier 'CategoryTheory.assoc'
