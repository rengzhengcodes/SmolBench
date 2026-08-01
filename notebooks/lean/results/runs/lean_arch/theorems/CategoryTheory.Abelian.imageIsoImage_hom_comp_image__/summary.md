# CategoryTheory.Abelian.imageIsoImage_hom_comp_image_ι   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsImage.isoExt_hom, IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

**True premises at k:** `CategoryTheory.Limits.IsImage.isoExt_hom`, `CategoryTheory.Limits.IsImage.lift_ι`, `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=282, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [imageIsoImage_hom, Limits.image.ι_image_subobject_assoc]
rw [kernel_ι_cokernel_π]
```

**lean_error:** tail step 1/2 ('erw [imageIsoImage_hom, Limits.image.ι_image_subobject_assoc]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=256, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Category.assoc, ← image_ι]
rw [imageIsoImage_hom_comp_image_ι, ← kernel.lift_ι]
rw [← Category.assoc, kernel.lift_ι]
rw [Abelian.image_ι_eq_kernel_cokernel_π]
```

**lean_error:** tail step 1/4 ('rw [← Category.assoc, ← image_ι]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=271, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply imageIsoImage_hom_comp_image_ι_eq_kernel_ι_cokernel_π
```

**lean_error:** tail step 1/1 ('apply imageIsoImage_hom_comp_image_ι_eq_kernel_ι_cokernel_π'): unknown identifier 'imageIsoImage_hom_comp_image_ι_eq_kernel_ι_cokernel_π'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=656, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imageIsoImage_hom],
exact IsImage.lift_ι (imageStrongEpiMonoFactorisation f) (imageStrongEpiMonoFactorisationIsImage f)
```

**lean_error:** tail step 1/2 ('rw [imageIsoImage_hom],'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.4s, in=641, out=41)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Category.assoc, ← IsImage.lift_ι (Image.isImage f), IsImage.isoExt_hom]
simp [Abelian.imageStrongEpiMonoFactorisation_m]
```

**lean_error:** tail step 1/2 ('rw [← Category.assoc, ← IsImage.lift_ι (Image.isImage f), IsImage.isoExt_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=645, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.Limits.IsImage.isoExt_hom
apply CategoryTheory.Limits.IsImage.lift_ι
exact CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m
```

**lean_error:** tail step 1/3 ('apply CategoryTheory.Limits.IsImage.isoExt_hom'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=907, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imageIsoImage_hom],
exact IsImage.lift_ι (imageStrongEpiMonoFactorisation f)
```

**lean_error:** tail step 1/2 ('rw [imageIsoImage_hom],'): <stdin>:1:22: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=893, out=71)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <| Limits.IsImage.isoExt_hom (Limits.imageIsImage f) (Abelian.imageIsImage f)
simp [← Category.assoc, IsImage.lift_ι]
rw [Abelian.imageStrongEpiMonoFactorisation_m, ← Category.assoc, kernel.lift_ι]
simp [← Category.assoc]
```

**lean_error:** tail step 1/4 ('ext <| Limits.IsImage.isoExt_hom (Limits.imageIsImage f) (Abelian.imageIsImage f)'): <stdin>:1:4: expected end of input

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=896, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.Limits.IsImage.isoExt_hom
apply CategoryTheory.Limits.IsImage.lift_ι
exact CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m
```

**lean_error:** tail step 1/3 ('apply CategoryTheory.Limits.IsImage.isoExt_hom'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=931, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [imageIsoImage_hom],
exact IsImage.lift_ι (imageStrongEpiMonoFactorisation f) (isImageImageStrongEpiMonoFactorisation f)
```

**lean_error:** tail step 1/2 ('rw [imageIsoImage_hom],'): <stdin>:1:22: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=947, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, ← IsImage.lift_ι (Image.isImage f), IsImage.isoExt_hom]
simp [imageStrongEpiMonoFactorisation_m]
```

**lean_error:** tail step 1/2 ('rw [← Category.assoc, ← IsImage.lift_ι (Image.isImage f), IsImage.isoExt_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=920, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.Limits.IsImage.isoExt_hom
apply CategoryTheory.Limits.IsImage.lift_ι
exact CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m
```

**lean_error:** tail step 1/3 ('apply CategoryTheory.Limits.IsImage.isoExt_hom'): tactic 'apply' failed, failed to unify
