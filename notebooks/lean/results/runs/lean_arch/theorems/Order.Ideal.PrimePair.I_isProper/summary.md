# Order.Ideal.PrimePair.I_isProper   (k=2, 3 tactics total)

file: `Mathlib/Order/PrimeIdeal.lean`  

**Ground-truth tail (from k):**
```lean
rwa [← IF.compl_I_eq_F] at h
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=237, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.disjoint h
```

**lean_error:** tail step 1/1 ('exact IF.disjoint h'): invalid field 'disjoint', the environment does not contain 'Order.Ideal.PrimePair.disjoint'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=211, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [PrimePair.mem_F_iff] at h
exact h.2.1.symm.not_mem_of_not_isMin h.1.isMin_I.some_isMin
```

**lean_error:** tail step 1/2 ('rw [PrimePair.mem_F_iff] at h'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=226, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.not_mem_I_of_mem_F h
```

**lean_error:** tail step 1/1 ('exact IF.not_mem_I_of_mem_F h'): invalid field 'not_mem_I_of_mem_F', the environment does not contain 'Order.Ideal.PrimePair.not_mem_I_of_mem_F'
