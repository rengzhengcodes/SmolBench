# CategoryTheory.Limits.limitObjIsoLimitCompEvaluation_inv_limit_map   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`  

**Ground-truth tail (from k):**
```lean
rw [Iso.inv_comp_eq, ← Category.assoc, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**True premises at k:** `CategoryTheory.Iso.inv_comp_eq`, `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · ✘ · |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=379, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.3s, verify 0.1s, in=379, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [limitObjIsoLimitCompEvaluation]
```

**final state (truncated):**
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u'
inst✝³ : Category.{v', u'} D
J : Type u₁
inst✝² : Category.{v₁, u₁} J
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=379, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [limitObjIsoLimitCompEvaluation_inv, ← limit.w_apply, ← Functor.map_comp, limit.w]
```

**lean_error:** tail step 1/1 ('simp only [limitObjIsoLimitCompEvaluation_inv, ← limit.w_apply, ← Functor.map_comp, limit.w]'): unknown identifier 'limitObjIsoLimitCompEvaluation_inv'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.4s, verify 0.2s, in=379, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [limitObjIsoLimitCompEvaluation]
```

**final state (truncated):**
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u'
inst✝³ : Category.{v', u'} D
J : Type u₁
inst✝² : Category.{v₁, u₁} J
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1136, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1136, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq]
```

**lean_error:** tail step 1/1 ('simp [← Iso.inv_comp_eq]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1136, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=1136, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [limit_map_limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc]
```

**lean_error:** tail step 1/1 ('simp only [limit_map_limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=1739, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← Category.assoc, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/2 ('simp only [← Category.assoc, Iso.eq_comp_inv,'): <stdin>:1:45: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=1739, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Category.assoc, ← Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [← Iso.inv_comp_eq, ← Category.assoc, ← Iso.eq_comp_inv, limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=1739, out=43)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc,
  Category.comp_id, Iso.eq_comp_inv,
  limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/3 ('simp only [limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc,'): <stdin>:1:68: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 72.7s, verify 0.1s, in=1739, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1763, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1763, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [limit_map_limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc]
```

**lean_error:** tail step 1/1 ('simp only [limit_map_limitObjIsoLimitCompEvaluation_hom, Iso.inv_hom_id_assoc]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1763, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Category.assoc, limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [← Iso.inv_comp_eq, ← Category.assoc, limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1763, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Category.assoc, limit_map_limitObjIsoLimitCompEvaluation_hom]
```

**lean_error:** tail step 1/1 ('simp [← Iso.inv_comp_eq, ← Category.assoc, limit_map_limitObjIsoLimitCompEvaluation_hom]'): simp made no progress
