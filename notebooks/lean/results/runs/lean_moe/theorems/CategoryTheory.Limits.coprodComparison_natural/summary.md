# CategoryTheory.Limits.coprodComparison_natural   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [coprodComparison, coprodComparison, coprod.map_desc, ← F.map_comp, ← F.map_comp,
  coprod.desc_comp, ← F.map_comp, coprod.inl_map, ← F.map_comp, coprod.inr_map]
```

**True premises at k:** `CategoryTheory.Limits.coprodComparison`, `CategoryTheory.Limits.coprodComparison`, `CategoryTheory.Limits.coprod.map_desc`, `CategoryTheory.Limits.coprod.desc_comp`, `CategoryTheory.Limits.coprod.inl_map`, `CategoryTheory.Limits.coprod.inr_map`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | · | ✘ | · |
| `hint:3` | · | ✘ | · |
| `noise:3` | · | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=456, out=553)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (coprodComparison_naturality (F:=F) (f:=f) (g:=g))
```

**lean_error:** tail step 1/1 ('simpa using (coprodComparison_naturality (F:=F) (f:=f) (g:=g))'): unknown identifier 'coprodComparison_naturality'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 213.5s, verify 0.1s, in=404, out=27936)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (F.map (coprod.map f g) ∘ coprodComparison F A B) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) = (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) := by
  calc
    (F.map (coprod.map f g) ∘ coprodComparison F A B) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B)
      = F.map (coprod.map f g) ∘ (coprodComparison F A B ∘ (inl : F.obj A → F.obj A ⊕ F.obj B)) := by rw [← Category.comp_assoc]
    _ = F.map (coprod.map f g) ∘ (F.map ((inl : A → A ⊕ B) : A → A ⊕ B)) := by
      rw [coprodComparison_inl]
    _ = F.map (coprod.map f g ∘ (inl : A → A ⊕ B)) := by rw [F.map_comp]
    _ = F.map ((inl' : A' → A' ⊕ B') ∘ (f : A → A')) := by
      rw [coprod.map_inl]
    _ = F.map (inl' : A' → A' ⊕ B') ∘ F.map (f : A → A') := by rw [F.map_comp]
    _ = (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) := by
      have h₂ : (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) = coprodComparison F A' B' ∘ (coprod.map (F.map f) (F.map g) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B)) := by rw [← Category.comp_assoc]
      rw [h₂]
      have h₃ : coprod.map (F.map f) (F.map g) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) = (inl' : F.obj A' → F.obj A' ⊕ F.obj B') ∘ (F.map f : F.obj A → F.obj A') := by
        rw [coprod.map_inl]
      rw [h₃]
      <;> simp [Category.comp_assoc]
have h₂ : (F.map (coprod.map f g) ∘ coprodComparison F A B) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B) = (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B) := by
  calc
    (F.map (coprod.map f g) ∘ coprodComparison F A B) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B)
      = F.map (coprod.map f g) ∘ (coprodComparison F A B ∘ (inr : F.obj B → F.obj A ⊕ F.obj B)) := by rw [← Category.comp_assoc]
    _ = F.map (coprod.map f g) ∘ (F.map ((inr : B → A ⊕ B) : B → A ⊕ B)) := by
      rw [coprodComparison_inr]
    _ = F.map (coprod.map f g ∘ (inr : B → A ⊕ B)) := by rw [F.map_comp]
    _ = F.map ((inr' : B' → A' ⊕ B') ∘ (g : B → B')) := by
      rw [coprod.map_inr]
    _ = F.map (inr' : B' → A' ⊕ B') ∘ F.map (g : B → B') := by rw [F.map_comp]
    _ = (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B) := by
      have h₃ : (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B) = coprodComparison F A' B' ∘ (coprod.map (F.map f) (F.map g) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B)) := by rw [← Category.comp_assoc]
      rw [h₃]
      have h₄ : coprod.map (F.map f) (F.map g) ∘ (inr : F.obj B → F.obj A ⊕ F.obj B) = (inr' : F.obj B' → F.obj A' ⊕ F.obj B') ∘ (F.map g : F.obj B → F.obj B') := by
        rw [coprod.map_inr]
      rw [h₄]
      <;> simp [Category.comp_assoc]
have h₃ : F.map (coprod.map f g) ∘ coprodComparison F A B = coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g) := by
  apply ext h₁ h₂
calc
  coprodComparison F A B ≫ F.map (coprod.map f g) = F.map (coprod.map f g) ∘ coprodComparison F A B := by rfl
  _ = coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g) := by rw [h₃]
  _ = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' := by rfl
```

**lean_error:** tail step 1/40 ("have h₁ : (F.map (coprod.map f g) ∘ coprodComparison F A B) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) = (coprodComparison F A' B' ∘ coprod.map (F.map f) (F.map g)) ∘ (inl : F.obj A → F.obj A ⊕ F.obj B) := by"): <stdin>:1:203: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.6s, verify 0.3s, in=406, out=462)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, coprod.map, CategoryStruct.comp]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 12.2s, verify 0.2s, in=2103, out=2366)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [coprodComparison, Category.assoc]
```

**final state (truncated):**
```
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
F : C ⥤ D
...
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 42.2s, verify 0.1s, in=2078, out=5090)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem CategoryTheory.Limits.coprodComparison_natural {C : Type u} {D : Type u₂} [Category.{v, u} C] [Category.{w, u₂} D] {F : C ⥤ D} {A A' B B' : C} [HasBinaryCoproduct A B] [HasBinaryCoproduct A' B'] [HasBinaryCoproduct (F.obj A) (F.obj B)] [HasBinaryCoproduct (F.obj A') (F.obj B')] (f : A ⟶ A') (g : B ⟶ B') :
    coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' := by
  have hLHS : coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
    have h1 : coprodComparison F A B = coprod.desc (F.map coprod.inl) (F.map coprod.inr) := rfl
    rw [h1]
    have h2 : coprod.desc (F.map coprod.inl) (F.map coprod.inr) ≫ F.map (coprod.map f g) = coprod.desc (F.map coprod.inl ≫ F.map (coprod.map f g)) (F.map coprod.inr ≫ F.map (coprod.map f g)) := by
      apply coprod.desc_comp
    rw [h2]
    have h3 : F.map coprod.inl ≫ F.map (coprod.map f g) = F.map (coprod.inl ≫ coprod.map f g) := by
      apply F.map_comp
    have h4 : F.map coprod.inr ≫ F.map (coprod.map f g) = F.map (coprod.inr ≫ coprod.map f g) := by
      apply F.map_comp
    rw [h3, h4]
    have h5 : coprod.inl ≫ coprod.map f g = f ≫ coprod.inl := by
      apply coprod.inl_map
    have h6 : coprod.inr ≫ coprod.map f g = g ≫ coprod.inr := by
      apply coprod.inr_map
    rw [h5, h6]
    have h7 : F.map (f ≫ coprod.inl) = F.map f ≫ F.map coprod.inl := by
      apply F.map_comp
    have h8 : F.map (g ≫ coprod.inr) = F.map g ≫ F.map coprod.inr := by
      apply F.map_comp
    rw [h7, h8]
    <;>
    simp_all [Function.comp_apply]
    <;>
    try aesop
  
  have hRHS : coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
    have h1 : coprodComparison F A' B' = coprod.desc (F.map coprod.inl) (F.map coprod.inr) := rfl
    rw [h1]
    have h2 : coprod.map (F.map f) (F.map g) ≫ coprod.desc (F.map coprod.inl) (F.map coprod.inr) = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
      apply coprod.map_desc
    rw [h2]
    <;>
    simp_all [Function.comp_apply]
    <;>
    try aesop
  
  have h_main : coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' := by
    rw [hLHS]
    rw [hRHS]
    <;>
    simp_all [Function.comp_apply]
    <;>
    try aesop
  
  exact h_main
```

**lean_error:** tail step 1/45 ("theorem CategoryTheory.Limits.coprodComparison_natural {C : Type u} {D : Type u₂} [Category.{v, u} C] [Category.{w, u₂} D] {F : C ⥤ D} {A A' B B' : C} [HasBinaryCoproduct A B] [HasBinaryCoproduct A' B'] [HasBinaryCoproduct (F.obj A) (F.obj B)] [HasBinaryCoproduct (F.obj A') (F.obj B

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 8.7s, verify 0.2s, in=2066, out=783)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, coprod.desc_comp, coprod.map_desc, coprod.inl_map, coprod.inr_map, Functor.map_comp]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 11.4s, verify 0.2s, in=2991, out=2168)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, Category.assoc]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.4s, verify 0.1s, in=2988, out=3856)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  coprodComparison F A B ≫ F.map (coprod.map f g)
    = (coprod.desc (F.map coprod.inl) (F.map coprod.inr)) ≫ F.map (coprod.map f g) := rfl
  _ = coprod.desc (F.map coprod.inl ≫ F.map (coprod.map f g)) (F.map coprod.inr ≫ F.map (coprod.map f g)) := by
    rw [coprod.desc_comp]
  _ = coprod.desc (F.map (coprod.inl ≫ coprod.map f g)) (F.map (coprod.inr ≫ coprod.map f g)) := by
    apply congr_arg2 coprod.desc
    · simp [F.map_comp]
    · simp [F.map_comp]
  _ = coprod.desc (F.map (f ≫ coprod.inl)) (F.map (g ≫ coprod.inr)) := by
    apply congr_arg2 coprod.desc
    · rw [coprod.inl_map]
    · rw [coprod.inr_map]
  _ = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
    apply congr_arg2 coprod.desc
    · simp [F.map_comp]
    · simp [F.map_comp]
  _ = coprod.map (F.map f) (F.map g) ≫ coprod.desc (F.map coprod.inl) (F.map coprod.inr) := by
    rw [← coprod.map_desc]
    <;> simp_all [Function.comp_def]
    <;> try simp_all
  _ = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' := by
    rw [coprodComparison]
```

**lean_error:** tail step 1/23 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 8.4s, verify 0.3s, in=2967, out=754)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, coprod.desc_comp, coprod.inl_map, coprod.inr_map, CategoryTheory.Functor.map_comp]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 9.2s, verify 0.3s, in=2911, out=1559)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, Category.assoc]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 103.9s, verify 0.1s, in=3132, out=12924)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
  calc
    coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.desc (F.map coprod.inl) (F.map coprod.inr) ≫ F.map (coprod.map f g) := by
      rw [coprodComparison]
    _ = coprod.desc (F.map coprod.inl ≫ F.map (coprod.map f g)) (F.map coprod.inr ≫ F.map (coprod.map f g)) := by
      rw [coprod.desc_comp]
    _ = coprod.desc (F.map (coprod.inl ≫ coprod.map f g)) (F.map (coprod.inr ≫ coprod.map f g)) := by
      have h₂ : F.map coprod.inl ≫ F.map (coprod.map f g) = F.map (coprod.inl ≫ coprod.map f g) := by
        rw [← F.map_comp]
        <;> simp [≫]
        <;> rfl
      have h₃ : F.map coprod.inr ≫ F.map (coprod.map f g) = F.map (coprod.inr ≫ coprod.map f g) := by
        rw [← F.map_comp]
        <;> simp [≫]
        <;> rfl
      rw [h₂, h₃]
    _ = coprod.desc (F.map (f ≫ coprod.inl)) (F.map (g ≫ coprod.inr)) := by
      have h₄ : coprod.inl ≫ coprod.map f g = f ≫ coprod.inl := by
        rw [coprod.inl_map]
      have h₅ : coprod.inr ≫ coprod.map f g = g ≫ coprod.inr := by
        rw [coprod.inr_map]
      rw [h₄, h₅]
    _ = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
      have h₆ : F.map (f ≫ coprod.inl) = F.map f ≫ F.map coprod.inl := by
        rw [← F.map_comp]
        <;> simp [≫]
        <;> rfl
      have h₇ : F.map (g ≫ coprod.inr) = F.map g ≫ F.map coprod.inr := by
        rw [← F.map_comp]
        <;> simp [≫]
        <;> rfl
      rw [h₆, h₇]
  
have h₂ : coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
  calc
    coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B' = coprod.map (F.map f) (F.map g) ≫ coprod.desc (F.map coprod.inl) (F.map coprod.inr) := by
      rw [coprodComparison]
    _ = coprod.desc ((F.map f) ≫ (F.map coprod.inl)) ((F.map g) ≫ (F.map coprod.inr)) := by
      rw [coprod.map_desc]
    _ = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by
      simp [≫]
      <;> rfl
  
rw [h₁]
rw [h₂]
<;> rfl
```

**lean_error:** tail step 1/44 ('have h₁ : coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.desc (F.map f ≫ F.map coprod.inl) (F.map g ≫ F.map coprod.inr) := by'): <stdin>:1:135: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 7.9s, verify 0.2s, in=2966, out=702)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [coprodComparison, coprod.desc_comp, coprod.inl_map, coprod.inr_map, Functor.map_comp]
```

**final state (truncated):**
```
case h₁
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
...
```
