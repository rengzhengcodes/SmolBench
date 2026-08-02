# CategoryTheory.braiding_rightUnitor   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [← whiskerLeft_iff, MonoidalCategory.whiskerLeft_comp, braiding_rightUnitor_aux₂]
```

**True premises at k:** `CategoryTheory.MonoidalCategory.whiskerLeft_iff`, `CategoryTheory.MonoidalCategory.whiskerLeft_comp`, `CategoryTheory.braiding_rightUnitor_aux₂`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.5s, verify 0.1s, in=335, out=1867)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa
```

**lean_error:** tail step 1/1 ('simpa'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 92.6s, verify 0.1s, in=284, out=12940)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : β_ (𝟙 C) X = (λ_ X) ≫ (ρ_ X)⁻¹ := by
  apply BraidedCategory.braiding_one
have h₂ : (ρ X)⁻¹.hom ≫ (ρ X).hom = id := by
  apply inv_inv
  exact ρ X.iso_iso
simp [h, h₂, Category.comp_hom, Category.comp_assoc, id_right]
```

**lean_error:** tail step 1/6 ('have h : β_ (𝟙 C) X = (λ_ X) ≫ (ρ_ X)⁻¹ := by'): <stdin>:1:45: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=277, out=528)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [braiding_one_left]
```

**lean_error:** tail step 1/1 ('simp [braiding_one_left]'): unknown identifier 'braiding_one_left'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.1s, in=1516, out=1433)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (whiskerLeft_iff (𝟙_ C) ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) ((λ_ X).hom)).mp
  simpa [whiskerLeft_comp] using braiding_rightUnitor_aux₂ X
```

**lean_error:** tail step 1/2 ('apply (whiskerLeft_iff (𝟙_ C) ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) ((λ_ X).hom)).mp'): application type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.9s, verify 0.1s, in=1525, out=5755)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
(β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom := by
  apply (whiskerLeft_iff _ _).mpr
  calc
    𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) := by rw [whiskerLeft_comp]
    _ = 𝟙_ C ◁ (λ_ X).hom := by rw [braiding_rightUnitor_aux₂]
```

**lean_error:** tail step 1/5 ('(β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom := by'): <stdin>:1:1: expected '{' or tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=1448, out=647)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply whiskerLeft_iff.1
rw [← whiskerLeft_comp (𝟙_ C) ((β_ (𝟙_ C) X).hom) ((ρ_ X).hom)]
exact braiding_rightUnitor_aux₂ X
```

**lean_error:** tail step 1/3 ('apply whiskerLeft_iff.1'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.1s, in=1763, out=2834)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h' :
      (𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom)) = 𝟙_ C ◁ (λ_ X).hom := by
    simpa [← whiskerLeft_comp (𝟙_ C) (β_ (𝟙_ C) X).hom (ρ_ X).hom] using
      (braiding_rightUnitor_aux₂ X)
  exact
    ((whiskerLeft_iff ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) (λ_ X).hom).1 h')
```

**lean_error:** tail step 1/6 ("have h' :"): <stdin>:1:9: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 60.0s, verify 0.1s, in=1780, out=7939)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₂ : (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom := by
  apply braiding_rightUnitor_aux₂
have h₃ : 𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) := by
  rw [whiskerLeft_comp]
have h₄ : 𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom := by
  calc
    𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) := by rw [h₃]
    _ = 𝟙_ C ◁ (λ_ X).hom := h₂
have h₅ : (β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom := by
  apply (whiskerLeft_iff _ _).mp h₄
exact h₅
```

**lean_error:** tail step 1/11 ('have h₂ : (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom := by'): <stdin>:1:84: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.2s, in=1693, out=602)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← whiskerLeft_iff ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) ((λ_ X).hom)]
rw [whiskerLeft_comp 𝟙_ C ((β_ (𝟙_ C) X).hom) ((ρ_ X).hom)]
exact braiding_rightUnitor_aux₂ X
```

**lean_error:** tail step 2/3 ('rw [whiskerLeft_comp 𝟙_ C ((β_ (𝟙_ C) X).hom) ((ρ_ X).hom)]'): <stdin>:1:21: expected ']'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.7s, verify 0.2s, in=1757, out=2174)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (whiskerLeft_iff ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) ((λ_ X).hom)).mp
simpa [whiskerLeft_comp] using (braiding_rightUnitor_aux₂ (X:=X))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 13.5s, verify 0.1s, in=1833, out=1429)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : 𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) := by
  rw [whiskerLeft_comp]
have h₂ : (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom := braiding_rightUnitor_aux₂ X
have h₃ : 𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = 𝟙_ C ◁ (λ_ X).hom := by
  rw [h₁]
  rw [h₂]
have h₄ : (β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom = (λ_ X).hom := by
  apply whiskerLeft_iff
  exact h₃
exact h₄
```

**lean_error:** tail step 1/10 ('have h₁ : 𝟙_ C ◁ ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) = (𝟙_ C ◁ (β_ (𝟙_ C) X).hom) ≫ (𝟙_ C ◁ (ρ_ X).hom) := by'): <stdin>:1:106: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.2s, in=1712, out=708)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← whiskerLeft_iff ((β_ (𝟙_ C) X).hom ≫ (ρ_ X).hom) ((λ_ X).hom)]
rw [whiskerLeft_comp (𝟙_ C) ((β_ (𝟙_ C) X).hom) ((ρ_ X).hom)]
exact braiding_rightUnitor_aux₂ X
```

**lean_error:** tail step 2/3 ('rw [whiskerLeft_comp (𝟙_ C) ((β_ (𝟙_ C) X).hom) ((ρ_ X).hom)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
