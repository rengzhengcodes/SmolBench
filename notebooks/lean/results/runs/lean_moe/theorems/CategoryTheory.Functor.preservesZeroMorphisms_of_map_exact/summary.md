# CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

**True premises at k:** `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object`, `CategoryTheory.Limits.idZeroEquivIsoZero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.5s, verify 0.1s, in=365, out=3968)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_id_eq_zero L h
```

**lean_error:** tail step 1/1 ('exact preservesZeroMorphisms_of_map_id_eq_zero L h'): unknown identifier 'preservesZeroMorphisms_of_map_id_eq_zero'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 137.9s, verify 0.1s, in=318, out=16871)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem PreservesZeroMorphisms L : PreservesZeroMorphisms L :=
  fun X Y => by
    have h_zero_eq : (0 : X ⟶ Y) = (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) := by
      have h1 : (0 : X ⟶ Y) = 0 := by simp
      have h2 : (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) = 0 := by
        have hA : ZeroObject A := inferInstance
        have h3 : (𝟙 (0 : A) : (0 : A) ⟶ (0 : A)) = 0 := ZeroObject.id_eq_zero hA
        calc
          (0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y) = (0 : X ⟶ 0) ∘ (𝟙 (0 : A) : (0 : A) ⟶ (0 : A)) ∘ (0 : 0 ⟶ Y) := by simp
          _ = ((0 : X ⟶ 0) ∘ (𝟙 (0 : A) : (0 : A) ⟶ (0 : A))) ∘ (0 : 0 ⟶ Y) := by rw [← Category.comp_assoc]
          _ = (0 : X ⟶ 0) ∘ (𝟙 (0 : A) : (0 : A) ⟶ (0 : A)) ∘ (0 : 0 ⟶ Y) := by rw [Category.comp_assoc]
          _ = (0 : X ⟶ 0) ∘ (0 : (0 : A) ⟶ (0 : A)) ∘ (0 : 0 ⟶ Y) := by
            rw [h3]
          _ = ((0 : X ⟶ 0) ∘ (0 : (0 : A) ⟶ (0 : A))) ∘ (0 : 0 ⟶ Y) := by
            rw [← Category.comp_assoc]
            <;> simp [Category.comp_assoc]
          _ = (0 : (0 : A) ⟶ Y) ∘ (0 : 0 ⟶ Y) := by simp [zero_comp]
          _ = 0 := by simp [comp_zero]
      rw [h1, h2]
    
    have h_map_zero : L.map (0 : X ⟶ Y) = L.map ((0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y)) := by
      rw [h_zero_eq]
    
    have h_map_comp : L.map ((0 : X ⟶ 0) ∘ (0 : 0 ⟶ Y)) = L.map (0 : X ⟶ 0) ∘ L.map (0 : 0 ⟶ Y) := by
      rw [L.map_comp]
    
    have h_main : L.map (0 : X ⟶ Y) = L.map (0 : X ⟶ 0) ∘ L.map (0 : 0 ⟶ Y) := by
      rw [h_map_zero, h_map_comp]
    
    have h_zero_obj : 𝟙 (L.obj 0) = 0 := h
    
    have h_comp_zero : L.map (0 : X ⟶ 0) ∘ L.map (0 : 0 ⟶ Y) = 0 := by
      calc
        L.map (0 : X ⟶ 0) ∘ L.map (0 : 0 ⟶ Y) = L.map (0 : X ⟶ 0) ∘ (𝟙 (L.obj 0) : L.obj 0 ⟶ L.obj 0) ∘ L.map (0 : 0 ⟶ Y) := by simp
        _ = (L.map (0 : X ⟶ 0) ∘ (𝟙 (L.obj 0) : L.obj 0 ⟶ L.obj 0)) ∘ L.map (0 : 0 ⟶ Y) := by rw [← Category.comp_assoc]
        _ = L.map (0 : X ⟶ 0) ∘ (𝟙 (L.obj 0) : L.obj 0 ⟶ L.obj 0) ∘ L.map (0 : 0 ⟶ Y) := by rw [Category.comp_assoc]
        _ = L.map (0 : X ⟶ 0) ∘ (0 : L.obj 0 ⟶ L.obj 0) ∘ L.map (0 : 0 ⟶ Y) := by
          rw [h_zero_obj]
        _ = (L.map (0 : X ⟶ 0) ∘ (0 : L.obj 0 ⟶ L.obj 0)) ∘ L.map (0 : 0 ⟶ Y) := by
          rw [← Category.comp_assoc]
          <;> simp [Category.comp_assoc]
        _ = (0 : L.obj 0 ⟶ L.obj Y) ∘ L.map (0 : 0 ⟶ Y) := by simp [zero_comp]
        _ = 0 := by simp [comp_zero]
    
    have h_final : L.map (0 : X ⟶ Y) = 0 := by
      rw [h_main]
      exact h_comp_zero
    
    exact h_final
```

**lean_error:** tail step 1/42 ('theorem PreservesZeroMorphisms L : PreservesZeroMorphisms L :='): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.4s, verify 0.1s, in=306, out=1451)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' fun X Y => _
have h₁ : L.map (0 : X ⟶ Y) = 0 := by
  have h₂ : (0 : X ⟶ Y) = (0 : X ⟶ 0) ≫ (0 : (0 : A) ⟶ Y) := by
    simp [zero_morphism]
  rw [h₂, L.map_comp]
  have h₃ : L.map (0 : X ⟶ 0) = 0 := by
    have : (0 : X ⟶ 0) = 0 := rfl
    simp [this]
  have h₄ : L.map (0 : (0 : A) ⟶ Y) = 0 := by
    have : (0 : (0 : A) ⟶ Y) = 0 := rfl
    simp [this]
  simp [h₃, h₄, zero_comp, comp_zero]
exact h₁
```

**lean_error:** tail step 1/13 ("refine' fun X Y => _"): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.2s, verify 0.2s, in=1003, out=665)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine preservesZeroMorphisms_of_map_zero_object ?_
exact ((idZeroEquivIsoZero (L.obj 0)).toFun h)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 45.4s, verify 0.2s, in=994, out=5186)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have i : L.obj 0 ≅ 0 := (idZeroEquivIsoZero (L.obj 0)).toFun h
exact preservesZeroMorphisms_of_map_zero_object i
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 33.1s, verify 2.4s, in=956, out=3461)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero (L.obj 0)).toFun h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.8s, verify 0.1s, in=1377, out=1049)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact preservesZeroMorphisms_of_map_zero_object ((CategoryTheory.Limits.idZeroEquivIsoZero (L.obj 0)).toFun h)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 118.2s, verify 0.2s, in=1380, out=14632)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have i : L.obj 0 ≅ 0 := (idZeroEquivIsoZero (L.obj 0)).toFun h
exact preservesZeroMorphisms_of_map_zero_object i
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 46.5s, verify 2.9s, in=1327, out=5007)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero _).toFun h
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=1354, out=660)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object ((CategoryTheory.Limits.idZeroEquivIsoZero (L.obj 0)).toFun h))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 49.2s, verify 0.1s, in=1449, out=5606)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact
    {C : Type u₁} [Category.{v₁, u₁} C] [Abelian C]
    {A : Type u₁} {B : Type u₂} [Category.{v₁, u₁} A] [Category.{v₂, u₂} B]
    [Abelian A] [Abelian B]
    (L : A ⥤ B)
    (h : 𝟙 (L.obj 0) = 0) :
    PreservesZeroMorphisms L := by
  have h_iso : L.obj 0 ≅ 0 := by
    have h₁ : 𝟙 (L.obj 0) = 0 := h
    have h₂ : L.obj 0 ≅ 0 := (idZeroEquivIsoZero (L.obj 0)).symm h₁
    exact h₂
  
  have h_preserves : PreservesZeroMorphisms L := by
    apply preservesZeroMorphisms_of_map_zero_object h_iso
  
  exact h_preserves
end
```

**lean_error:** tail step 1/15 ('theorem CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.2s, in=1344, out=447)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero _).toFun h
```
