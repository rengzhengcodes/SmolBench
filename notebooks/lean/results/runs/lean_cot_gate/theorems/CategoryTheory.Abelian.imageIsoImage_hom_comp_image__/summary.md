# CategoryTheory.Abelian.imageIsoImage_hom_comp_image_ι   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [IsImage.isoExt_hom, IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

**True premises at k:** `CategoryTheory.Limits.IsImage.isoExt_hom`, `CategoryTheory.Limits.IsImage.lift_ι`, `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✘ |
| `hint:2` | ✘ ✓ ✘ ✘ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✓ |
| `noise:3` | ✘ ✘ ✘ ✓ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 138.6s, verify 0.1s, in=256, out=5769)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 161.3s, verify 0.1s, in=256, out=6600)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 191.0s, verify 0.1s, in=256, out=7761)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 205.7s, verify 0.1s, in=256, out=8322)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [image_ι_eq_kernel_ι_cokernel_π]
```

**lean_error:** tail step 1/1 ('simp [image_ι_eq_kernel_ι_cokernel_π]'): unknown identifier 'image_ι_eq_kernel_ι_cokernel_π'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=256, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=256, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=256, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=256, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [imageIsoImage, imageToKernelCokernel]
```

**lean_error:** tail step 1/1 ('simp [imageIsoImage, imageToKernelCokernel]'): unknown identifier 'imageToKernelCokernel'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.6s, verify 0.1s, in=256, out=182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.1s, verify 0.1s, in=256, out=200)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.2s, verify 0.1s, in=256, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.1s, verify 0.1s, in=256, out=424)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← cancel_mono ((imageIsoImage f).hom), Iso.inv_hom_id_assoc, imageIsoImage]
```

**lean_error:** tail step 1/1 ('rw [← cancel_mono ((imageIsoImage f).hom), Iso.inv_hom_id_assoc, imageIsoImage]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 80.4s, verify 0.1s, in=630, out=3474)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsImage.lift_ι (Abelian.imageStrongEpiMonoFactorisation_m f).IsImage
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι (Abelian.imageStrongEpiMonoFactorisation_m f).IsImage'): invalid field 'IsImage', the environment does not contain 'Eq.IsImage'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 104.6s, verify 0.1s, in=630, out=4447)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsImage.lift_ι, Abelian.imageStrongEpiMonoFactorisation_m]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 126.1s, verify 0.2s, in=630, out=5292)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsImage.lift_ι
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 184.4s, verify 0.1s, in=630, out=7348)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsImage.lift_ι (image.isImage (kernel.ι (cokernel.π f)))
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι (image.isImage (kernel.ι (cokernel.π f)))'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=630, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=630, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=630, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=630, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imageIsoImage, imageIsoImageMk]
```

**lean_error:** tail step 1/1 ('simp [imageIsoImage, imageIsoImageMk]'): unknown identifier 'imageIsoImageMk'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.6s, verify 0.1s, in=630, out=253)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsImage.isoExt_hom, IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.8s, verify 0.1s, in=630, out=293)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.1s, verify 0.1s, in=630, out=308)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CategoryTheory.Limits.IsImage.lift_ι, CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 10.0s, verify 0.1s, in=630, out=320)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsImage.lift_ι]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 184.0s, verify 0.2s, in=884, out=4638)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsImage.lift_ι
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 213.2s, verify 0.2s, in=884, out=4161)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsImage.lift_ι
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 217.1s, verify 0.1s, in=884, out=5312)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← IsImage.lift_ι (imageStrongEpiMonoFactorisation_m f).isImage]
```

**lean_error:** tail step 1/1 ('rw [← IsImage.lift_ι (imageStrongEpiMonoFactorisation_m f).isImage]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 226.1s, verify 0.1s, in=884, out=8250)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

**lean_error:** tail step 1/1 ('simp only [IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=884, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=884, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=884, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=884, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imageIsoImage, imageStrongEpiMonoFactorisation, IsImage.lift_ι]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.6s, verify 0.1s, in=884, out=255)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imageIsoImage_hom, IsImage.lift_ι (kernelIsKernel f), imageStrongEpiMonoFactorisation_m f]
```

**lean_error:** tail step 1/1 ('simp [imageIsoImage_hom, IsImage.lift_ι (kernelIsKernel f), imageStrongEpiMonoFactorisation_m f]'): unknown identifier 'imageIsoImage_hom'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 15.6s, verify 0.1s, in=884, out=304)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 16.3s, verify 0.1s, in=884, out=318)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 16.9s, verify 0.1s, in=884, out=335)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 21.5s, verify 0.2s, in=908, out=925)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsImage.lift_ι
simp [imageStrongEpiMonoFactorisation_m]
```

**lean_error:** tail step 1/2 ('apply IsImage.lift_ι'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 61.1s, verify 0.2s, in=908, out=2759)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsImage.lift_ι
```

**lean_error:** tail step 1/1 ('apply IsImage.lift_ι'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 115.6s, verify 0.1s, in=908, out=4884)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsImage.lift_ι,
  exact (Abelian.imageStrongEpiMonoFactorisation f).2.mono,
```

**lean_error:** tail step 1/2 ('apply IsImage.lift_ι,'): <stdin>:1:20: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 137.8s, verify 0.1s, in=908, out=5738)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=908, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=908, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=908, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [imageIsoImage]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=908, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [imageIsoImage, imageIsoImageAux, ← cancel_epi (imageStrongEpiMonoFactorisation f).e]
```

**lean_error:** tail step 1/1 ('simp [imageIsoImage, imageIsoImageAux, ← cancel_epi (imageStrongEpiMonoFactorisation f).e]'): unknown identifier 'imageIsoImageAux'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 6.3s, verify 0.1s, in=908, out=210)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.0s, verify 0.1s, in=908, out=305)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.5s, verify 0.1s, in=908, out=312)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [IsImage.lift_ι]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.2s, verify 0.1s, in=908, out=358)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Limits.IsImage.isoExt_hom, Limits.IsImage.lift_ι, imageStrongEpiMonoFactorisation_m]
```
