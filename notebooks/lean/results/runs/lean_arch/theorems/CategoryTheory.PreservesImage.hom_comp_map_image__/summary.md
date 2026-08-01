# CategoryTheory.PreservesImage.hom_comp_map_image_ι   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Images.lean`  

**Ground-truth tail (from k):**
```lean
rw [iso_hom, image.lift_fac]
```

**True premises at k:** `CategoryTheory.PreservesImage.iso_hom`, `CategoryTheory.Limits.image.lift_fac`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 1.6s, in=429, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [iso.hom_inv_id_assoc, L.map_comp, image.lift_fac]
rw [image.lift_fac_assoc, image.fac, Category.assoc]
erw [image.lift_fac, image.fac]
```

**lean_error:** tail step 1/3 ('erw [iso.hom_inv_id_assoc, L.map_comp, image.lift_fac]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=402, out=87)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Category.assoc, ← L.map_comp]
apply image.iso_hom_comp_image_ι
infer_instance
rw [← Category.assoc, iso_hom_comp_eq_id_assoc (imageIsoImage f)]
simp only [Category.id_comp, Category.comp_id, image.factorThruImage_comp_image_ι]
rw [← L.map_comp]
simp only [image.factorThruImage_comp_image_ι]
```

**lean_error:** tail step 1/7 ('rw [← Category.assoc, ← L.map_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=418, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply image.fac_iso_hom
```

**lean_error:** tail step 1/1 ('apply image.fac_iso_hom'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.3s, in=705, out=179)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [image.lift_fac (MonoFactorisation.mk (L.map (image.ι f)) (L.map (image.ι f)))]
rw [(iso L f).hom]
rw [(iso L f).inv_comp_eq]
rw [image.lift_fac (image.monoFactorisation f)]
rw [(image.isImage f).lift_fac (image.monoFactorisation f)]
rw [Category.assoc]
rw [(image.isImage f).fac]
rw [image.lift_fac (MonoFactorisation.mk (L.map (image.ι f)) (L.map (image.ι f)))]
rw [(image.isImage (L.map f)).lift_fac (image.monoFactorisation (L.map f))]
rw [Category.assoc]
rw [(image.isImage (L.map f)).fac]
rw [(iso L f).comp_inv_eq]
rw [Category.id_comp]
```

**lean_error:** tail step 1/13 ('rw [image.lift_fac (MonoFactorisation.mk (L.map (image.ι f)) (L.map (image.ι f)))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=684, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Category.assoc, ← L.map_comp, image.lift_fac]
rw [image.lift_fac, CategoryTheory.PreservesImage.iso_hom]
rfl
```

**lean_error:** tail step 1/3 ('rw [← Category.assoc, ← L.map_comp, image.lift_fac]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 43.9s, verify 0.1s, in=694, out=2515)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
erw [image.lift_fac]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.3s, in=956, out=121)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [←image.lift_fac (MonoFactorisation.mk (L.obj X) (L.map f) (image.m (L.map f)) (image.e (L.map f)) (image.fac (L.map f)))],
rw [←image.lift_fac (MonoFactorisation.mk (L.obj X) (L.map f) (L.map (image.m f)) ((iso L f).inv ≫ L.map (image.e f)) (by rw [iso.inv_hom_id_assoc, ←L.map_comp, image.fac]))],
rw [(iso L f).hom_inv_id_assoc]
```

**lean_error:** tail step 1/3 ('rw [←image.lift_fac (MonoFactorisation.mk (L.obj X) (L.map f) (image.m (L.map f)) (image.e (L.map f)) (image.fac (L.map f)))],'): <stdin>:1:125: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=936, out=38)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Category.assoc, ← L.map_comp, image.lift_fac]
erw [CategoryTheory.PreservesImage.iso_hom]
simp only [image.lift_fac]
```

**lean_error:** tail step 1/3 ('rw [← Category.assoc, ← L.map_comp, image.lift_fac]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 54.1s, verify 0.1s, in=945, out=3145)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply image.lift_fac
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=980, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [PreservesImage.iso_hom L f],
rw [image.lift_fac (MonoFactorisation.ofIsoImage f)]
```

**lean_error:** tail step 1/2 ('rw [PreservesImage.iso_hom L f],'): <stdin>:1:31: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=990, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, ← L.map_comp, image.lift_fac]
erw [CategoryTheory.PreservesImage.iso_hom]
simp only [Category.assoc, image.lift_fac]
```

**lean_error:** tail step 1/3 ('rw [← Category.assoc, ← L.map_comp, image.lift_fac]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 111.3s, verify 0.1s, in=969, out=6592)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply image.lift_fac
```
