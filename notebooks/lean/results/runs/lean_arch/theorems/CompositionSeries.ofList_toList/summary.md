# CompositionSeries.ofList_toList   (k=3, 4 tactics total)

file: `Mathlib/Order/JordanHolder.lean`  

**Ground-truth tail (from k):**
```lean
simp [ofList, toList, -List.ofFn_succ]
```

**True premises at k:** `CompositionSeries.ofList`, `CompositionSeries.toList`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=343, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ofList_series]
rw [Fin.cast_eq_castLE]
rw [Fin.castLE_of_lt]
```

**lean_error:** tail step 1/3 ('rw [ofList_series]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=310, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Fin.cast_to_nat, Fin.cast_mk]
simp only [CompositionSeries.ofList_series, List.get_toList]
rfl
```

**lean_error:** tail step 1/3 ('rw [← Fin.cast_to_nat, Fin.cast_mk]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 61.9s, verify 0.1s, in=332, out=3954)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw CompositionSeries.ofList_toList_eq
rfl
```

**lean_error:** tail step 1/2 ('rw CompositionSeries.ofList_toList_eq'): <stdin>:1:3: expected '['

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=753, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [series_ofList, nthLe_toList, Fin.cast_mk]
congr
exact Fin.eq_of_veq _
```

**lean_error:** tail step 1/3 ('rw [series_ofList, nthLe_toList, Fin.cast_mk]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=727, out=40)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [ofList, toList, List.nthLe_ofFn, List.length_ofFn, Fin.eta, Fin.cast_mk]
simp only [List.nthLe_ofFn']
```

**lean_error:** tail step 1/2 ('simp_rw [ofList, toList, List.nthLe_ofFn, List.length_ofFn, Fin.eta, Fin.cast_mk]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=742, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ofList_series, toList_ofFn]
congr
exact i.2
```

**lean_error:** tail step 1/3 ('rw [ofList_series, toList_ofFn]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1671, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Fin.castSucc, Fin.cast, ofList_series, toList_series]
```

**lean_error:** tail step 1/1 ('rw [Fin.castSucc, Fin.cast, ofList_series, toList_series]'): failed to rewrite using equation theorems for 'Fin.castSucc'

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1644, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [ofList, toList, List.nthLe_ofFn, List.length_ofFn]
simp only [Fin.eta]
rfl
```

**lean_error:** tail step 1/3 ('simp_rw [ofList, toList, List.nthLe_ofFn, List.length_ofFn]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1660, out=38)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1695, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [series_ofList, List.nthLe_ofFn]
simp only [Fin.cast_mk, Fin.val_mk]
```

**lean_error:** tail step 1/2 ('rw [series_ofList, List.nthLe_ofFn]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1776, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [ofList_series, toList, List.nthLe_ofFn, Fin.eta, Fin.cast_mk]
simp only [List.length_ofFn]
```

**lean_error:** tail step 1/2 ('simp_rw [ofList_series, toList, List.nthLe_ofFn, Fin.eta, Fin.cast_mk]'): unknown identifier 'ofList_series'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1684, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ofList_series, toList_to_ofList, List.nthLe_ofFn']
simp
```

**lean_error:** tail step 1/2 ("rw [ofList_series, toList_to_ofList, List.nthLe_ofFn']"): tactic 'rewrite' failed, equality or iff proof expected
