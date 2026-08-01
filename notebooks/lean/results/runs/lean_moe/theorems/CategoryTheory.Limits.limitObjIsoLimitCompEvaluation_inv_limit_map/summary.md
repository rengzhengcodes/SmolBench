# CategoryTheory.Limits.limitObjIsoLimitCompEvaluation_inv_limit_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`  

**Ground-truth tail (from k):**
```lean
rw [Iso.inv_comp_eq, ← Category.assoc, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**True premises at k:** `CategoryTheory.Iso.inv_comp_eq`, `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=450, out=1071)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using limitObjIsoLimitCompEvaluation_naturality (F:=F) (f:=f)
```

**lean_error:** tail step 1/1 ('simpa using limitObjIsoLimitCompEvaluation_naturality (F:=F) (f:=f)'): unknown identifier 'limitObjIsoLimitCompEvaluation_naturality'

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
