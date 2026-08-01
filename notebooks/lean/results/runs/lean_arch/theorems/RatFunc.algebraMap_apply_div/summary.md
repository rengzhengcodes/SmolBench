# RatFunc.algebraMap_apply_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
convert coe_div (algebraMap F[X] (RatFunc F) p) (algebraMap F[X] (RatFunc F) q) <;>
  rw [← mk_one, coe_def, coeAlgHom, mk_eq_div, liftAlgHom_apply_div, map_one, div_one,
    Algebra.ofId_apply]
```

**True premises at k:** `RatFunc.coe_div`, `algebraMap`, `RatFunc`, `algebraMap`, `RatFunc`, `RatFunc.mk_one`, `RatFunc.coe_def`, `RatFunc.coeAlgHom`, `RatFunc.mk_eq_div`, `RatFunc.liftAlgHom_apply_div`, `map_one`, `div_one`, `Algebra.ofId_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.2s, in=374, out=112)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_div₀ (algebraMap (RatFunc F) (LaurentSeries F))]
rw [(algebraMap (RatFunc F) (LaurentSeries F)).comp (algebraMap F[X] (RatFunc F))]
rw [(algebraMap F[X] (LaurentSeries F)).comp (algebraMap F[X] (RatFunc F)) (algebraMap F[X] (RatFunc F))]
rw [map_div₀ (algebraMap F[X] (LaurentSeries F))]
```

**lean_error:** tail step 1/4 ('rw [map_div₀ (algebraMap (RatFunc F) (LaurentSeries F))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=326, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← RatFunc.algebraMap_apply, ← RatFunc.algebraMap_apply, RatFunc.laurentSeries_algebraMap_div]
simp only [RingHom.map_div, RingHom.comp_apply]
```

**lean_error:** tail step 1/2 ('rw [← RatFunc.algebraMap_apply, ← RatFunc.algebraMap_apply, RatFunc.laurentSeries_algebraMap_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=363, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [algebra_map_rat_func, algebra_map_laurent_series]
```

**lean_error:** tail step 1/1 ('simp only [algebra_map_rat_func, algebra_map_laurent_series]'): unknown identifier 'algebra_map_rat_func'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=2321, out=53)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div p q, RatFunc.liftAlgHom_apply_div, RatFunc.mk_one p, RatFunc.mk_one q]
rw [Algebra.ofId_apply, Algebra.ofId_apply]
rw [map_one, div_one]
```

**lean_error:** tail step 1/3 ('rw [RatFunc.mk_eq_div p q, RatFunc.liftAlgHom_apply_div, RatFunc.mk_one p, RatFunc.mk_one q]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2213, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div]
simp [RatFunc.coeAlgHom]
```

**lean_error:** tail step 1/2 ('simp_rw [← RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=2310, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.coe_div, RatFunc.coeAlgHom, RatFunc.coe_def, Algebra.ofId_apply]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.coe_div, RatFunc.coeAlgHom, RatFunc.coe_def, Algebra.ofId_apply]'): simp made no progress

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=5048, out=77)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div p q, RatFunc.coe_div (algebraMap F[X] (RatFunc F) p) (algebraMap F[X] (RatFunc F) q)]
rw [RatFunc.coe_def, RatFunc.coe_def]
rw [RatFunc.mk_one p, RatFunc.mk_one q]
```

**lean_error:** tail step 1/3 ('rw [RatFunc.mk_eq_div p q, RatFunc.coe_div (algebraMap F[X] (RatFunc F) p) (algebraMap F[X] (RatFunc F) q)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.9s, in=4893, out=123)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [← RatFunc.liftAlgHom_apply_div (algebraMap F[X] (RatFunc F)) (nonZeroDivisors_le_comap_nonZeroDivisors_of_injective _ (Polynomial.algebraMap_hahnSeries_injective _)) p q, RatFunc.coeAlgHom, RatFunc.coe_def]
simp_rw [RatFunc.liftAlgHom_apply_div (algebraMap F[X] (LaurentSeries F)) (nonZeroDivisors_le_comap_nonZeroDivisors_of_injective _ (Polynomial.algebraMap_hahnSeries_injective _)) p q]
rfl
```

**lean_error:** tail step 1/3 ('simp_rw [← RatFunc.liftAlgHom_apply_div (algebraMap F[X] (RatFunc F)) (nonZeroDivisors_le_comap_nonZeroDivisors_of_injective _ (Polynomial.algebraMap_hahnSeries_injective _)) p q, RatFunc.coeAlgHom, RatFunc.coe_def]'): failed to synthesize instance

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=5037, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [coe_div, coe_def, mk_eq_div]
```

**lean_error:** tail step 1/1 ('simp only [coe_div, coe_def, mk_eq_div]'): simp made no progress

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=5073, out=86)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div p q, RatFunc.coe_div]
rw [RatFunc.coe_def, RatFunc.coe_def]
rw [RatFunc.coeAlgHom_apply, RatFunc.coeAlgHom_apply]
rw [RatFunc.liftAlgHom_apply_div p q]
rw [Algebra.ofId_apply, Algebra.ofId_apply]
rw [map_one, div_one]
```

**lean_error:** tail step 1/6 ('rw [RatFunc.mk_eq_div p q, RatFunc.coe_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=5277, out=38)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← RatFunc.coe_def, coe_div, RatFunc.liftAlgHom_apply_div, RatFunc.coeAlgHom]
simp only [Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('simp only [← RatFunc.coe_def, coe_div, RatFunc.liftAlgHom_apply_div, RatFunc.coeAlgHom]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=5062, out=76)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.coe_div]
simp only [RatFunc.coeAlgHom_apply, Algebra.ofId_apply, Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('rw [RatFunc.coe_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
