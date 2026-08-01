# RatFunc.mk_eq_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**True premises at k:** `RatFunc.mk_eq_div'`, `RatFunc.ofFractionRing_div`, `RatFunc.ofFractionRing_algebraMap`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=292, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div]
rw [RatFunc.algebraMap_eq_ofFrac]
```

**lean_error:** tail step 1/2 ('rw [RatFunc.mk_eq_div]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=258, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.mk_eq, RatFunc.algebraMap_eq]
simp only [RingHom.coe_comp, Function.comp_apply, RatFunc.map_apply]
simp only [div_eq_mul_inv]
rw [← RatFunc.map_mul, ← RatFunc.map_inv₀]
simp only [Polynomial.map_one, Polynomial.map_mul, inv_one, mul_one]
```

**lean_error:** tail step 1/5 ('rw [RatFunc.mk_eq, RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=281, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [algebraMap_apply, algebraMap_apply]
exact RatFunc.mk_eq_div (algebraMap K[X] (RatFunc K) p) (algebraMap K[X] (RatFunc K) q)
```

**lean_error:** tail step 1/2 ('rw [algebraMap_apply, algebraMap_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 2.0s, verify 0.5s, in=808, out=44)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
rw [RatFunc.ofFractionRing_algebraMap]
rw [RatFunc.ofFractionRing_algebraMap]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=756, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.3s, in=797, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div]
simp [ofFractionRing_algebraMap]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.4s, in=1408, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
congr <;> exact RatFunc.ofFractionRing_algebraMap _
```

**lean_error:** tail step 3/3 ('congr <;> exact RatFunc.ofFractionRing_algebraMap _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1335, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1397, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.5s, in=1432, out=47)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
congr
rw [RatFunc.ofFractionRing_algebraMap]
rw [RatFunc.ofFractionRing_algebraMap]
```

**lean_error:** tail step 4/5 ('rw [RatFunc.ofFractionRing_algebraMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1448, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap p, RatFunc.ofFractionRing_algebraMap q]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1421, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```
