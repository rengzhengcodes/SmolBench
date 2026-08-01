# CategoryTheory.Limits.limitObjIsoLimitCompEvaluation_inv_limit_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`  

**Ground-truth tail (from k):**
```lean
rw [Iso.inv_comp_eq, ← Category.assoc, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**True premises at k:** `CategoryTheory.Iso.inv_comp_eq`, `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=406, out=207)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iso.inv_comp_eq],
  erw [limit.map_eq (limit F) f],
  erw [limit.map_eq (limit (whiskerLeft F ((evaluation K C).map f))) (𝟙 _)],
  erw [limMap_eq_limit_map],
  erw [category.id_comp],
  erw [(limitObjIsoLimitCompEvaluation F j).hom_inv_id],
  erw [(limitObjIsoLimitCompEvaluation F i).hom_inv_id],
  erw [limit.map_id],
  erw [category.id_comp],
  erw [category.id_comp],
  erw [limMap_eq_limit_map],
  erw [(limitObjIsoLimitCompEvaluation F i).inv_hom_id],
  erw [(limitObjIsoLimitCompEvaluation F j).inv_hom_id],
  erw [category.id_comp],
  erw [category.id_comp],
  erw [category.id_comp],
  erw [category.id_comp],
  erw [category.id_comp],
  apply category.comp_id,
  apply category.id_comp,
  refl
```

**lean_error:** tail step 1/21 ('rw [Iso.inv_comp_eq],'): <stdin>:1:20: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=379, out=77)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [limitObjIsoLimitCompEvaluation_inv, limitObjIsoLimitCompEvaluation_inv, limit.map_comp, limMap_comp, ←assoc, ←assoc]
simp only [Functor.map_id, Category.id_comp]
rw [←Functor.map_comp, ←Functor.map_comp]
simp only [whiskerLeft_id, Functor.map_id, Category.comp_id, Category.id_comp]
```

**lean_error:** tail step 1/4 ('rw [limitObjIsoLimitCompEvaluation_inv, limitObjIsoLimitCompEvaluation_inv, limit.map_comp, limMap_comp, ←assoc, ←assoc]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=395, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply limit_obj_iso_limit_comp_evaluation_naturality
```

**lean_error:** tail step 1/1 ('apply limit_obj_iso_limit_comp_evaluation_naturality'): unknown identifier 'limit_obj_iso_limit_comp_evaluation_naturality'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=1159, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Iso.inv_comp_eq, Category.assoc, Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('rw [Iso.inv_comp_eq, Category.assoc, Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1138, out=48)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.inv_comp_eq]
simp only [CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]
rw [← CategoryTheory.Category.assoc, CategoryTheory.Iso.eq_comp_inv]
rfl
```

**lean_error:** tail step 2/4 ('simp only [CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 60.1s, verify 0.1s, in=1148, out=3684)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cancel_epi (limitObjIsoLimitCompEvaluation F i).hom],
simp [limit_map_limitObjIsoLimitCompEvaluation_hom],
rw [Iso.inv_comp_eq],
```

**lean_error:** tail step 1/3 ('rw [← cancel_epi (limitObjIsoLimitCompEvaluation F i).hom],'): <stdin>:1:58: expected end of input

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1751, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Iso.inv_comp_eq, Category.assoc, Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('rw [Iso.inv_comp_eq, Category.assoc, Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1738, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc, ←CategoryTheory.Iso.inv_comp_eq, CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Category.assoc, ←CategoryTheory.Iso.inv_comp_eq, CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1740, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cancel_epi (limitObjIsoLimitCompEvaluation F i).hom],
apply CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom,
```

**lean_error:** tail step 1/2 ('rw [← cancel_epi (limitObjIsoLimitCompEvaluation F i).hom],'): <stdin>:1:58: expected end of input

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.3s, in=1783, out=51)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Iso.inv_comp_eq (limitObjIsoLimitCompEvaluation F i)]
rw [Category.assoc]
rw [Iso.eq_comp_inv (limitObjIsoLimitCompEvaluation F j)]
rw [limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 2/4 ('rw [Category.assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=1830, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc, ← CategoryTheory.Iso.inv_comp_eq, CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]
rw [CategoryTheory.Iso.eq_comp_inv, CategoryTheory.Category.assoc]
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Category.assoc, ← CategoryTheory.Iso.inv_comp_eq, CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.5s, in=1772, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cancel_epi (limitObjIsoLimitCompEvaluation F i).hom]
apply CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom
```

**lean_error:** tail step 2/2 ('apply CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom'): tactic 'apply' failed, failed to unify
