# card_le_of_surjective'   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`  

**Ground-truth tail (from k):**
```lean
exact
  card_le_of_surjective R ((P.toLinearMap.comp f).comp Q.toLinearMap)
    ((P.surjective.comp i).comp Q.surjective)
```

**True premises at k:** `card_le_of_surjective`, `LinearMap.comp`, `Function.Surjective.comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 92.1s, verify 0.1s, in=338, out=4846)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [rank_finsupp R β, rank_finsupp R α]
exact rankCondition.le_of_surjective f i
```

**lean_error:** tail step 1/2 ('rw [rank_finsupp R β, rank_finsupp R α]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=338, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact i.liftCard_le (P.trans f.toLinearMap.comp Q)
```

**lean_error:** tail step 1/1 ('exact i.liftCard_le (P.trans f.toLinearMap.comp Q)'): invalid field 'liftCard_le', the environment does not contain 'Function.Surjective.liftCard_le'

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=338, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact i.liftCardLE
```

**lean_error:** tail step 1/1 ('exact i.liftCardLE'): invalid field 'liftCardLE', the environment does not contain 'Function.Surjective.liftCardLE'

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=338, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact i.liftCard_le
```

**lean_error:** tail step 1/1 ('exact i.liftCard_le'): invalid field 'liftCard_le', the environment does not contain 'Function.Surjective.liftCard_le'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 128.6s, verify 0.1s, in=1114, out=6957)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (LinearEquiv.surjective P).comp (i.comp (LinearEquiv.surjective Q))
```

**lean_error:** tail step 1/1 ('apply card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (LinearEquiv.surjective P).comp (i.comp (LinearEquiv.surjective Q))'): application type mismatch

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1114, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=1114, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `hint:2` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=1114, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 111.0s, verify 0.2s, in=3501, out=5923)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q)) (Function.Surjective.comp (LinearEquiv.surjective P) (i.comp (LinearEquiv.surjective Q)))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q)) (Function.Surjective.comp (LinearEquiv.surjective P) (i.comp (LinearEquiv.surjective Q)))'): application type mismatch

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 2.3s, verify 2.0s, in=3501, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=3501, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `hint:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 9.2s, verify 0.2s, in=3501, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 118.7s, verify 0.1s, in=3530, out=6372)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply card_le_of_surjective (P.toLinearMap ∘ f ∘ Q.toLinearMap)
apply P.surjective.comp (i.comp Q.surjective)
```

**lean_error:** tail step 1/2 ('apply card_le_of_surjective (P.toLinearMap ∘ f ∘ Q.toLinearMap)'): application type mismatch

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 4.3s, verify 0.6s, in=3530, out=47)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (Function.Surjective.comp P.surjective (Function.Surjective.comp i Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (Function.Surjective.comp P.surjective (Function.Surjective.comp i Q.surjective))'): application type mismatch

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=3530, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 9.4s, verify 0.2s, in=3530, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (P.toLinearMap.comp (f.comp Q.toLinearMap)) (P.surjective.comp (i.comp Q.surjective))'): application type mismatch
