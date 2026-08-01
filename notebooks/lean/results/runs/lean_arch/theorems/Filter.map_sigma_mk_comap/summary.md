# Filter.map_sigma_mk_comap   (k=2, 3 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
apply image_sigmaMk_preimage_sigmaMap hf
```

**True premises at k:** `Set.image_sigmaMk_preimage_sigmaMap`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=386, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Sigma.map_eq, preimage_preimage, preimage_id],
congr,
ext1,
rw [mem_preimage, mem_preimage, Sigma.mk.inj_iff],
constructor,
rw [Function.Injective.eq_iff hf]
```

**lean_error:** tail step 1/6 ('rw [Sigma.map_eq, preimage_preimage, preimage_id],'): <stdin>:1:49: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=360, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [Sigma.map, Sigma.mk.injEq, ← preimage_comp, ← image_comp, comp]
simp only [Function.comp_apply, id_eq, preimage_id', image_id']
rw [← hf.eq_iff, preimage_image_eq]
```

**lean_error:** tail step 1/3 ('simp_rw [Sigma.map, Sigma.mk.injEq, ← preimage_comp, ← image_comp, comp]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=375, out=597)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Sigma.ext
simp only [Sigma.map, Function.comp, Sigma.eta]
```

**lean_error:** tail step 1/2 ('apply Sigma.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=848, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=813, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Set.image_sigmaMk_preimage_sigmaMap hf g a, id.def]
```

**lean_error:** tail step 1/1 ('simp_rw [Set.image_sigmaMk_preimage_sigmaMap hf g a, id.def]'): no goals to be solved

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=837, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1581, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1545, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [id.def, Set.image_id]
rw [Set.image_sigmaMk_preimage_sigmaMap hf g]
```

**lean_error:** tail step 1/2 ('simp_rw [id.def, Set.image_id]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1570, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf
exacts [g, a, x✝]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1610, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1661, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [id.def, image_id]
simp_rw [Set.image_sigmaMk_preimage_sigmaMap hf g a x✝]
```

**lean_error:** tail step 1/2 ('simp_rw [id.def, image_id]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1599, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf
exacts [g, a, x✝]
```
