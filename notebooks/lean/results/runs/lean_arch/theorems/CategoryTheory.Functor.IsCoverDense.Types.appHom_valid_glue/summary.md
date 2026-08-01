# CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`  

**Ground-truth tail (from k):**
```lean
apply appHom_restrict
```

**True premises at k:** `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=500, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Functor.map_comp, NatTrans.naturality],
simp only [appHom, NatTrans.comp_app, Functor.op_map]
```

**lean_error:** tail step 1/2 ('rw [Functor.map_comp, NatTrans.naturality],'): <stdin>:1:42: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=466, out=90)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← FunctorToTypes.naturality, ← FunctorToTypes.naturality]
simp only [Functor.comp_map, Functor.op_map, op_comp, assoc, IsCoverDense.appHom_app]
rw [← ℱ'.val.map_comp, ← op_comp]
simp only [CategoryTheory.Functor.map_id, CategoryTheory.Functor.id_map, op_id, ℱ'.val.map_id]
rfl
```

**lean_error:** tail step 1/5 ('rw [← FunctorToTypes.naturality, ← FunctorToTypes.naturality]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 174.6s, verify 0.2s, in=489, out=10865)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply α.naturality
```

**lean_error:** tail step 1/1 ('apply α.naturality'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=842, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Functor.map_comp, appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [Functor.map_comp, appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=806, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=831, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [appHom_restrict α f a✝]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict α f a✝]'): <stdin>:1:25: expected token

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=2084, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 2.2s, verify 0.1s, in=2040, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=2073, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2109, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Functor.map_comp, appHom_restrict]
```

**lean_error:** tail step 1/1 ('rw [Functor.map_comp, appHom_restrict]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=2216, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [appHom_restrict]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2098, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [appHom_restrict α f a✝]
```

**lean_error:** tail step 1/1 ('rw [appHom_restrict α f a✝]'): <stdin>:1:25: expected token
