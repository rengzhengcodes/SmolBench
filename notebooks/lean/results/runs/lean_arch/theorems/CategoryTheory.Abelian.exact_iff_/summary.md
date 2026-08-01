# CategoryTheory.Abelian.exact_iff'   (k=7, 8 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
simp [h.2]
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=449, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [kernel.ι_assoc],
rw [cokernel.π_assoc],
rw [←h.2],
rw [Fork.ι_assoc],
rw [kernel.condition_assoc],
rw [zero_comp],
rw [comp_zero]
```

**lean_error:** tail step 1/7 ('rw [kernel.ι_assoc],'): <stdin>:1:19: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 1.4s, in=420, out=71)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Category.assoc, IsColimit.coconePointUniqueUpToIso_hom_comp, CokernelCofork.π, colimit.isColimit, IsColimit.comp_coconePoint, parallelPair_pi]
rw [← Category.assoc, ← Iso.hom_inv_id, Category.assoc, comp_zero]
```

**lean_error:** tail step 1/2 ('simp only [Category.assoc, IsColimit.coconePointUniqueUpToIso_hom_comp, CokernelCofork.π, colimit.isColimit, IsColimit.comp_coconePoint, parallelPair_pi]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 519.7s, verify 0.2s, in=438, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)
apply (CategoryTheory.Iso.hom_inv_id (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf) _)
simp only [CategoryTheory.Iso.inv_hom_id]
rw [← CategoryTheory.Category.assoc]
apply (CategoryTheory.I
```

**lean_error:** tail step 1/1457 ('apply (CategoryTheory.Iso.hom_inv_id (IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))) _)'): function expected at
