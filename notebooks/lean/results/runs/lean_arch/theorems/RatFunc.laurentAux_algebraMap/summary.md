# RatFunc.laurentAux_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Laurent.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, ← mk_one, mk_eq_div, laurentAux_div, mk_eq_div, taylor_one, map_one, map_one]
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one`, `RatFunc.mk_eq_div`, `RatFunc.laurentAux_div`, `RatFunc.mk_eq_div`, `Polynomial.taylor_one`, `map_one`, `map_one`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=313, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [laurentAux_algebraMap]
rw [taylor_algebraMap]
rw [algebraMap_comp]
rw [algebraMap_id]
rfl
```

**lean_error:** tail step 1/5 ('rw [laurentAux_algebraMap]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=279, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [laurentAux, taylor, algebraMap_apply]
simp only [Polynomial.map_taylor]
rfl
```

**lean_error:** tail step 1/3 ('simp only [laurentAux, taylor, algebraMap_apply]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=302, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LaurentAux.taylor_eq
```

**lean_error:** tail step 1/1 ('apply LaurentAux.taylor_eq'): unknown identifier 'LaurentAux.taylor_eq'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.3s, in=1441, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one, RatFunc.mk_one, RatFunc.mk_eq_div, RatFunc.laurentAux_div, RatFunc.mk_eq_div, Polynomial.taylor_one, map_one, map_one]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.mk_one, RatFunc.mk_one, RatFunc.mk_eq_div, RatFunc.laurentAux_div, RatFunc.mk_eq_div, Polynomial.taylor_one, map_one, map_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1382, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← RatFunc.mk_one p, RatFunc.laurentAux_div, RatFunc.mk_one (taylor r p), Polynomial.taylor_one, map_one]
```

**lean_error:** tail step 1/1 ('rw [← RatFunc.mk_one p, RatFunc.laurentAux_div, RatFunc.mk_one (taylor r p), Polynomial.taylor_one, map_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=1430, out=232)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div, laurentAux_div, mk_eq_div, map_taylor, map_taylor, map_one, taylor_one, C_1]
```

**lean_error:** tail step 1/1 ('rw [mk_eq_div, laurentAux_div, mk_eq_div, map_taylor, map_taylor, map_one, taylor_one, C_1]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=3159, out=69)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div p 1]
rw [RatFunc.mk_eq_div (taylor r p) 1]
rw [RatFunc.laurentAux_div]
rw [Polynomial.taylor_one]
rw [map_one]
rw [map_one]
rw [div_one]
rw [div_one]
```

**lean_error:** tail step 1/8 ('rw [RatFunc.mk_eq_div p 1]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=3072, out=46)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [laurentAux, RatFunc.mapRingHom_apply, RatFunc.mk_one, RatFunc.laurentAux_div, map_one, div_one]
simp only [Polynomial.taylor_one, RatFunc.mk_one]
```

**lean_error:** tail step 1/2 ('rw [laurentAux, RatFunc.mapRingHom_apply, RatFunc.mk_one, RatFunc.laurentAux_div, map_one, div_one]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=3148, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
done
```

**lean_error:** tail step 1/1 ('done'): internal exception #7

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=3184, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one, RatFunc.mk_one, RatFunc.mk_eq_div, RatFunc.laurentAux_div, RatFunc.mk_eq_div, Polynomial.taylor_one, map_one, map_one]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.mk_one, RatFunc.mk_one, RatFunc.mk_eq_div, RatFunc.laurentAux_div, RatFunc.mk_eq_div, Polynomial.taylor_one, map_one, map_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=3323, out=44)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one p, RatFunc.laurentAux_div, RatFunc.mk_eq_div, RatFunc.mk_eq_div]
simp only [Polynomial.taylor_one, map_one, div_one]
```

**lean_error:** tail step 1/2 ('rw [← RatFunc.mk_one p, RatFunc.laurentAux_div, RatFunc.mk_eq_div, RatFunc.mk_eq_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=3173, out=41)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div p 1, mk_eq_div (taylor r p) 1, laurentAux_div r p 1, map_one, map_one]
```

**lean_error:** tail step 1/1 ('rw [mk_eq_div p 1, mk_eq_div (taylor r p) 1, laurentAux_div r p 1, map_one, map_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
