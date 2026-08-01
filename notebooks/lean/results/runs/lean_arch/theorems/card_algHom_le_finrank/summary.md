# card_algHom_le_finrank   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`  

**Ground-truth tail (from k):**
```lean
apply rank_lt_aleph0
```

**True premises at k:** `rank_lt_aleph0`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=335, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Module.Finite.rank_lt_aleph0 K M
```

**lean_error:** tail step 1/1 ('exact Module.Finite.rank_lt_aleph0 K M'): unknown constant 'Module.Finite.rank_lt_aleph0'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=305, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Cardinal.lift_lt, ← Cardinal.aleph0_lift]
exact Module.Finite.rank_lt_aleph0 K M
```

**lean_error:** tail step 1/2 ('rw [← Cardinal.lift_lt, ← Cardinal.aleph0_lift]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=324, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Module.rank_finite
```

**lean_error:** tail step 1/1 ('apply Module.rank_finite'): unknown constant 'Module.rank_finite'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=669, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact rank_lt_aleph0 K M
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=633, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact rank_lt_aleph0 K M
exact nontrivial_of_injective (algebraMap K L) (NoZeroSMulDivisors.algebraMap_injective K L)
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 3.4s, verify 0.1s, in=658, out=195)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply rank_lt_aleph0
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1478, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_lt_aleph0 K M
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1435, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
exact nontrivial_of_injective (Algebra.ofId K L).toLinearMap.toAddMonoidHom.injective
```

**lean_error:** tail step 1/2 ('exact rank_lt_aleph0'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=1467, out=176)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply rank_lt_aleph0
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.6s, in=1506, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rank_lt_aleph0 K M
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1563, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rank_lt_aleph0
exact nontrivial_of_injective (algebraMap K L) (IsScalarTower.injective K L L) this
```

**lean_error:** tail step 1/2 ('exact rank_lt_aleph0'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1495, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
assumption
```

**lean_error:** tail step 1/1 ('assumption'): tactic 'assumption' failed
