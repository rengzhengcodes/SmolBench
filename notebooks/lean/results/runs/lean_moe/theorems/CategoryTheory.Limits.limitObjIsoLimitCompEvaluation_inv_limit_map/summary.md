# CategoryTheory.Limits.limitObjIsoLimitCompEvaluation_inv_limit_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`  

**Ground-truth tail (from k):**
```lean
rw [Iso.inv_comp_eq, ← Category.assoc, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**True premises at k:** `CategoryTheory.Iso.inv_comp_eq`, `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=450, out=1071)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using limitObjIsoLimitCompEvaluation_naturality (F:=F) (f:=f)
```

**lean_error:** tail step 1/1 ('simpa using limitObjIsoLimitCompEvaluation_naturality (F:=F) (f:=f)'): unknown identifier 'limitObjIsoLimitCompEvaluation_naturality'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 262.3s, verify 0.1s, in=405, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
def evaluation {C D : Type*} [Category C] [Category D] : (C ⥤ D) ⥤ C ⥤ D :=
  ⟨fun F => fun c => F c, fun α => fun c => α c⟩
```

**lean_error:** tail step 1/2 ('def evaluation {C D : Type*} [Category C] [Category D] : (C ⥤ D) ⥤ C ⥤ D :='): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=394, out=485)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext k
simp [limitObjIsoLimitCompEvaluation, limMap, whiskerLeft, Category.assoc]
<;> rfl
```

**lean_error:** tail step 1/3 ('ext k'): no applicable extensionality theorem found for

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 39.3s, verify 0.6s, in=1246, out=10349)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)).mpr
  apply (Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)).mpr
  simpa [Category.assoc] using
    (limit_map_limitObjIsoLimitCompEvaluation_hom (F:=F) (f:=f)).symm
```

**lean_error:** tail step 2/4 ('apply (Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)).mpr'): tactic 'apply' failed, failed to unify

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.8s, verify 0.1s, in=1237, out=9310)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom = (limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) := by
  apply limit_map_limitObjIsoLimitCompEvaluation_hom
have h₂ : (limit F).map f = ((limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f))) ≫ (limitObjIsoLimitCompEvaluation F j).inv := by
  calc
    (limit F).map f = (limit F).map f ≫ 1 := by simp
    _ = (limit F).map f ≫ ((limitObjIsoLimitCompEvaluation F j).hom ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
      simp [CategoryTheory.hom_inv_id]
    _ = ((limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom) ≫ (limitObjIsoLimitCompEvaluation F j).inv := by
      rw [← CategoryTheory.assoc]
    _ = ((limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f))) ≫ (limitObjIsoLimitCompEvaluation F j).inv := by
      rw [h₁]
have h₃ : (limit F).map f = (limitObjIsoLimitCompEvaluation F i).hom ≫ (limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
  calc
    (limit F).map f = ((limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f))) ≫ (limitObjIsoLimitCompEvaluation F j).inv := h₂
    _ = (limitObjIsoLimitCompEvaluation F i).hom ≫ (limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
      rw [CategoryTheory.assoc]
have h₄ : (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f = limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv := by
  apply CategoryTheory.Iso.inv_comp_eq
  exact h₃
exact h₄
```

**lean_error:** tail step 1/20 ('have h₁ : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom = (limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) := by'): <stdin>:1:167: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.3s, verify 0.2s, in=1174, out=1417)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)]
rw [CategoryTheory.Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)]
exact limit_map_limitObjIsoLimitCompEvaluation_hom F f
```

**lean_error:** tail step 1/3 ('rw [← CategoryTheory.Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 24.0s, verify 0.4s, in=1866, out=6118)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)).mp
  have h := (limit_map_limitObjIsoLimitCompEvaluation_hom (F:=F) (f:=f))
  simpa [Category.assoc] using
    (by
      simpa [Category.assoc] using
        (congrArg (fun k => k ≫ (limitObjIsoLimitCompEvaluation F j).inv) h))
```

**lean_error:** tail step 1/6 ('apply (Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)).mp'): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 150.5s, verify 0.1s, in=1881, out=14308)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom = (limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) := by
  apply limit_map_limitObjIsoLimitCompEvaluation_hom
calc
  (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f = (limitObjIsoLimitCompEvaluation F i).inv ≫ ((limit F).map f ≫ 1) := by simp
  _ = (limitObjIsoLimitCompEvaluation F i).inv ≫ ((limit F).map f ≫ ((limitObjIsoLimitCompEvaluation F j).hom ≫ (limitObjIsoLimitCompEvaluation F j).inv)) := by
    simp [CategoryTheory.inv_hom]
  _ = (limitObjIsoLimitCompEvaluation F i).inv ≫ (((limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
    simp [CategoryTheory.assoc]
  _ = (limitObjIsoLimitCompEvaluation F i).inv ≫ (((limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f))) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
    rw [h]
  _ = ((limitObjIsoLimitCompEvaluation F i).inv ≫ (limitObjIsoLimitCompEvaluation F i).hom) ≫ (limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
    simp [CategoryTheory.assoc]
  _ = 1 ≫ (limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv) := by
    simp [CategoryTheory.inv_hom]
  _ = limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv := by
    simp

<;> simp_all [CategoryTheory.assoc]
<;> try simp_all [CategoryTheory.inv_hom]
<;> try simp_all [CategoryTheory.assoc]
```

**lean_error:** tail step 1/19 ('have h : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation F j).hom = (limitObjIsoLimitCompEvaluation F i).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) := by'): <stdin>:1:166: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.2s, in=1803, out=738)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)]
rw [CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom F f]
simp [CategoryTheory.Category.assoc]
```

**lean_error:** tail step 1/3 ('rw [← CategoryTheory.Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.1s, verify 0.2s, in=1817, out=3780)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)).mpr
  simpa [Category.assoc] using
    (congrArg (fun k => k ≫ (limitObjIsoLimitCompEvaluation F j).inv)
      (limit_map_limitObjIsoLimitCompEvaluation_hom (F:=F) (f:=f))).symm
```

**lean_error:** tail step 2/4 ('simpa [Category.assoc] using'): <stdin>:1:28: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 262.4s, verify 0.1s, in=1976, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (limit F).map f = (limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by
  have h₂ : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation F i).hom = (limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) := ...
  -- right-compose both sides with (limitObjIsoLimitCompEvaluation F i).inv
  have h₃ : (limit F).map f = (limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by
    calc
      (limit F).map f = (limit F).map f ≫ id := by simp
      _ = (limit F).map f ≫ ((limitObjIsoLimitCompEvaluation F i).hom ≫ (limitObjIsoLimitCompEvaluation F i).inv) := by
        simp [limitObjIsoLimitCompEvaluation F i].hom_inv_id
      _ = ((limit F).map f ≫ (limitObjIsoLimitCompEvaluation F i).hom) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by
        simp [assoc]
      _ = ((limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f))) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by rw [h₂]
      _ = (limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by simp [assoc]
  exact h₃
```

**lean_error:** tail step 1/13 ('have h₁ : (limit F).map f = (limitObjIsoLimitCompEvaluation F j).hom ≫ limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F i).inv := by'): <stdin>:1:167: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 32.8s, verify 0.2s, in=1807, out=3377)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)]
rw [CategoryTheory.Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)]
exact limit_map_limitObjIsoLimitCompEvaluation_hom F f
```

**lean_error:** tail step 1/3 ('rw [← CategoryTheory.Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
