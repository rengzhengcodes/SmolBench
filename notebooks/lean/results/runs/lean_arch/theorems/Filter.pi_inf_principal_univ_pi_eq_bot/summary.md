# Filter.pi_inf_principal_univ_pi_eq_bot   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
filter_upwards [mem_pi_of_mem i hi] with x using mt fun h => h i trivial
```

**True premises at k:** `Filter.mem_pi_of_mem`, `mt`, `trivial`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=301, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.pi_univ],
rw [Set.compl_pi],
apply Filter.pi_of_compl_mem hi,
```

**lean_error:** tail step 1/3 ('rw [Set.pi_univ],'): <stdin>:1:16: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 1.7s, in=274, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [compl_pi]
simp only [mem_univ, pi_empty', compl_compl]
exact hi
```

**lean_error:** tail step 1/3 ('rw [compl_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=290, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pi_mem_compl
intro i
apply Set.mem_compl_compl
exact hi
```

**lean_error:** tail step 1/4 ('apply pi_mem_compl'): unknown identifier 'pi_mem_compl'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=826, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Filter.mem_pi_of_mem i ((mt (Set.preimage_mono (eval i)) hi).mpr trivial)
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi_of_mem i ((mt (Set.preimage_mono (eval i)) hi).mpr trivial)'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=794, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Filter.mem_pi_of_mem i hi
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi_of_mem i hi'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=815, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply mem_pi_of_mem i
exact hi
```

**lean_error:** tail step 1/2 ('apply mem_pi_of_mem i'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=993, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Filter.mem_pi_of_mem i ((mt (fun ht => Filter.pi_inf_principal_univ_pi_eq_bot f s ht trivial) hi).mpr hi)
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi_of_mem i ((mt (fun ht => Filter.pi_inf_principal_univ_pi_eq_bot f s ht trivial) hi).mpr hi)'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=962, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Filter.mem_pi_of_mem i hi
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi_of_mem i hi'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=982, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply mem_pi_of_mem i
exact hi
```

**lean_error:** tail step 1/2 ('apply mem_pi_of_mem i'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1019, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact mt (mem_pi_of_mem i) hi
trivial
```

**lean_error:** tail step 1/2 ('exact mt (mem_pi_of_mem i) hi'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=1008, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Filter.mem_pi_of_mem i hi
```
```

**lean_error:** tail step 1/2 ('exact Filter.mem_pi_of_mem i hi'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 80.9s, verify 0.1s, in=1008, out=5106)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply mem_pi_of_mem i
exact hi
```

**lean_error:** tail step 1/2 ('apply mem_pi_of_mem i'): tactic 'apply' failed, failed to unify
