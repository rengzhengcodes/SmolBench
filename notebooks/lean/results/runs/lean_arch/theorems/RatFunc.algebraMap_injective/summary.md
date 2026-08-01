# RatFunc.algebraMap_injective   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
exact ofFractionRing_injective.comp (IsFractionRing.injective _ _)
```

**True premises at k:** `IsFractionRing.injective`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=262, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' Function.Injective.comp _ _,
  exact ofFractionRing_injective,
exact algebraMap_injective K[X] (FractionRing K[X])
```

**lean_error:** tail step 1/3 ("refine' Function.Injective.comp _ _,"): <stdin>:1:35: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 1.2s, in=232, out=58)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Function.comp]
rw [← IsLocalization.coe_algebraMap _ (nonZeroDivisors K[X])]
apply IsFractionRing.injective K[X] (FractionRing K[X])
exact IsDomain.noZeroSMulDivisors K[X] (FractionRing K[X])
```

**lean_error:** tail step 2/4 ('rw [← IsLocalization.coe_algebraMap _ (nonZeroDivisors K[X])]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=251, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp
apply ofFractionRing_injective
apply Algebra.algebraMap_injective
apply Polynomial.aeval_injective
apply RingHom.injective_of_isDomain
```

**lean_error:** tail step 3/5 ('apply Algebra.algebraMap_injective'): unknown constant 'Algebra.algebraMap_injective'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=436, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=400, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=425, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=797, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=756, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=786, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=821, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=828, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective.comp Polynomial.algebraMap_injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective.comp Polynomial.algebraMap_injective'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=810, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify
