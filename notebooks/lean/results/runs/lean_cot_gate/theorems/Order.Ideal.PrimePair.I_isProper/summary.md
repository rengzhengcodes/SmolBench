# Order.Ideal.PrimePair.I_isProper   (k=2, 3 tactics total)

file: `Mathlib/Order/PrimeIdeal.lean`  

**Ground-truth tail (from k):**
```lean
rwa [← IF.compl_I_eq_F] at h
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 57.5s, verify 0.1s, in=212, out=2752)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (set.disjoint_left.mp IF.disjoint) h
```

**lean_error:** tail step 1/1 ('exact (set.disjoint_left.mp IF.disjoint) h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 60.5s, verify 0.1s, in=212, out=2902)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← PrimePair.F_eq_compl_I] at h
exact h
```

**lean_error:** tail step 1/2 ('rw [← PrimePair.F_eq_compl_I] at h'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 68.1s, verify 0.1s, in=212, out=3257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IF.F.I_disjoint h
```

**lean_error:** tail step 1/1 ('apply IF.F.I_disjoint h'): invalid field 'I_disjoint', the environment does not contain 'Order.PFilter.I_disjoint'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 79.7s, verify 0.2s, in=212, out=4006)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h1
exact IF.disjoint w h1 h
```

**lean_error:** tail step 2/2 ('exact IF.disjoint w h1 h'): invalid field 'disjoint', the environment does not contain 'Order.Ideal.PrimePair.disjoint'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.3s, verify 0.1s, in=212, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.1 h
```

**lean_error:** tail step 1/1 ('exact IF.1 h'): function expected at

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.4s, verify 0.1s, in=212, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.NFw h
```

**lean_error:** tail step 1/1 ('exact IF.NFw h'): invalid field 'NFw', the environment does not contain 'Order.Ideal.PrimePair.NFw'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.4s, verify 0.1s, in=212, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.F.disjoint_I.left h
```

**lean_error:** tail step 1/1 ('exact IF.F.disjoint_I.left h'): invalid field 'disjoint_I', the environment does not contain 'Order.PFilter.disjoint_I'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=212, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.f_disjoint.2 h
```

**lean_error:** tail step 1/1 ('exact IF.f_disjoint.2 h'): invalid field 'f_disjoint', the environment does not contain 'Order.Ideal.PrimePair.f_disjoint'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.7s, verify 0.1s, in=212, out=170)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.I_disjoint h
```

**lean_error:** tail step 1/1 ('exact IF.I_disjoint h'): invalid field 'I_disjoint', the environment does not contain 'Order.Ideal.PrimePair.I_disjoint'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.2s, verify 0.2s, in=212, out=191)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.not_mem_I_of_mem_F h
```

**lean_error:** tail step 1/1 ('exact IF.not_mem_I_of_mem_F h'): invalid field 'not_mem_I_of_mem_F', the environment does not contain 'Order.Ideal.PrimePair.not_mem_I_of_mem_F'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.4s, verify 0.1s, in=212, out=199)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IF.disjoint.not_mem h
```

**lean_error:** tail step 1/1 ('exact IF.disjoint.not_mem h'): invalid field 'disjoint', the environment does not contain 'Order.Ideal.PrimePair.disjoint'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.6s, verify 0.1s, in=212, out=261)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using Disjoint.left_of_le h
```

**lean_error:** tail step 1/1 ('simpa using Disjoint.left_of_le h'): invalid field notation, type is not of the form (C ...) where C is a constant
