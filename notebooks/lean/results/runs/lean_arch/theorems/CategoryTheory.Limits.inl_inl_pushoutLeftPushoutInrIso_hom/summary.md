# CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Category.assoc, ← Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.2s, in=364, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pushoutLeftPushoutInrIso_hom]
rw [pushout.inl_desc]
rw [pushout.inl_desc]
```

**lean_error:** tail step 1/3 ('rw [pushoutLeftPushoutInrIso_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=337, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Category.assoc, ← Iso.eq_comp_inv]
simp
rw [pushoutLeftPushoutInrIso_hom_inl, Category.comp_id]
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=353, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pushoutLeftPushoutInrIso_hom_inl
```

**lean_error:** tail step 1/1 ('apply pushoutLeftPushoutInrIso_hom_inl'): unknown identifier 'pushoutLeftPushoutInrIso_hom_inl'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=912, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc],
rw [CategoryTheory.Iso.eq_comp_inv],
rw [CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/3 ('rw [CategoryTheory.Category.assoc],'): <stdin>:1:34: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=884, out=52)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, pushoutLeftPushoutInrIso_hom]
rw [inl_pushoutLeftPushoutInrIso_inv, CategoryTheory.Iso.eq_comp_inv]
simp only [CategoryTheory.Category.id_comp]
```

**lean_error:** tail step 1/3 ('simp only [CategoryTheory.Category.assoc, pushoutLeftPushoutInrIso_hom]'): unknown identifier 'pushoutLeftPushoutInrIso_hom'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=901, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.eq_comp_inv],
apply CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv,
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Iso.eq_comp_inv],'): <stdin>:1:35: expected end of input

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.2s, in=1940, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv, Iso.eq_comp_inv]
```

**lean_error:** tail step 1/1 ('rw [Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv, Iso.eq_comp_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.8s, in=1927, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, inl_pushoutLeftPushoutInrIso_inv, ← Category.assoc]
rw [pushoutLeftPushoutInrIso_hom, Category.comp_id]
```

**lean_error:** tail step 1/2 ('simp only [Category.assoc, inl_pushoutLeftPushoutInrIso_inv, ← Category.assoc]'): failed to synthesize

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.9s, in=1929, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Category.assoc]
rw [← inl_pushoutLeftPushoutInrIso_inv]
rw [Iso.eq_comp_inv]
```

**lean_error:** tail step 1/3 ('rw [Category.assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=1972, out=37)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Category.assoc],
rw [CategoryTheory.Iso.eq_comp_inv],
rw [CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/3 ('rw [CategoryTheory.Category.assoc],'): <stdin>:1:34: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2065, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Category.assoc]
rw [inl_pushoutLeftPushoutInrIso_inv]
simp
```

**lean_error:** tail step 1/3 ('simp only [Category.assoc]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=1961, out=55)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←CategoryTheory.Category.assoc],
rw [←CategoryTheory.Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g')],
rw [CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv],
```

**lean_error:** tail step 1/3 ('rw [←CategoryTheory.Category.assoc],'): <stdin>:1:35: expected end of input
