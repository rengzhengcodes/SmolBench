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

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=366, out=55)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : Fintype.card (β → R) ≤ Fintype.card (α → R) := Fintype.card_le_of_surjective (P.symm.trans (f.trans Q)),
simp [Fintype.card_fun] at h,
exact h
```

**lean_error:** tail step 1/3 ('have h : Fintype.card (β → R) ≤ Fintype.card (α → R) := Fintype.card_le_of_surjective (P.symm.trans (f.trans Q)),'): <stdin>:1:112: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=340, out=80)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Fintype.card_congr (P.trans f.range.toEquiv)]
apply LinearMap.range_le_ker_compl f
rw [LinearMap.ker_eq_bot_of_injective]
rw [← LinearEquiv.injective_iff_surjective]
exact i
rw [LinearEquiv.trans_apply, Q.apply_symm_apply, Finsupp.range_total]
exact le_top
```

**lean_error:** tail step 1/7 ('rw [← Fintype.card_congr (P.trans f.range.toEquiv)]'): application type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.4s, in=355, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Fintype.card_le_of_injective
apply (P ∘ f ∘ Q).Injective
```

**lean_error:** tail step 2/2 ('apply (P ∘ f ∘ Q).Injective'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1141, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact
  card_le_of_surjective ((P.symm.toLinearMap.comp f).comp Q.toLinearMap)
    (((LinearEquiv.symm P).surjective.comp i).comp (LinearEquiv.surjective Q))
```

**lean_error:** tail step 1/3 ('exact'): <stdin>:1:5: unexpected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=1102, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply card_le_of_surjective _ i
exact (P.symm.toLinearMap.comp f).comp Q.toLinearMap
```

**lean_error:** tail step 1/2 ('apply card_le_of_surjective _ i'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=1130, out=64)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact card_le_of_surjective (LinearMap.comp (LinearMap.comp Q.toLinearMap f) P.toLinearMap) (Function.Surjective.comp (Function.Surjective.comp (LinearEquiv.surjective Q.symm) i) (LinearEquiv.surjective P))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (LinearMap.comp (LinearMap.comp Q.toLinearMap f) P.toLinearMap) (Function.Surjective.comp (Function.Surjective.comp (LinearEquiv.surjective Q.symm) i) (LinearEquiv.surjective P))'): application type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=3521, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact
  le_of_fin_surjective R ((P.toLinearMap.comp f).comp Q.toLinearMap)
    (((LinearEquiv.surjective P).comp i).comp (LinearEquiv.surjective Q))
```

**lean_error:** tail step 1/3 ('exact'): <stdin>:1:5: unexpected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=3480, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply card_le_of_surjective (LinearMap.comp P.toLinearMap (f.comp Q.toLinearMap))
exact Function.Surjective.comp P.surjective (Function.Surjective.comp i Q.surjective)
```

**lean_error:** tail step 1/2 ('apply card_le_of_surjective (LinearMap.comp P.toLinearMap (f.comp Q.toLinearMap))'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=3510, out=62)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective (LinearMap.comp (LinearMap.comp Q.toLinearMap f) P.toLinearMap) (Function.Surjective.comp (Function.Surjective.comp (LinearEquiv.surjective Q) i) (LinearEquiv.surjective P))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (LinearMap.comp (LinearMap.comp Q.toLinearMap f) P.toLinearMap) (Function.Surjective.comp (Function.Surjective.comp (LinearEquiv.surjective Q) i) (LinearEquiv.surjective P))'): application type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=3554, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact card_le_of_surjective ((P.toLinearMap.comp f).comp Q.toLinearMap)
  ((Function.Surjective.comp P.surjective i).comp Q.surjective)
```

**lean_error:** tail step 1/2 ('exact card_le_of_surjective ((P.toLinearMap.comp f).comp Q.toLinearMap)'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=3790, out=48)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply card_le_of_surjective _ (P.symm.toLinearMap.comp f).comp Q.toLinearMap
exact (LinearEquiv.symm P).surjective.comp (i.comp (LinearEquiv.surjective Q))
```

**lean_error:** tail step 1/2 ('apply card_le_of_surjective _ (P.symm.toLinearMap.comp f).comp Q.toLinearMap'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=3543, out=61)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact card_le_of_surjective (LinearMap.comp (LinearMap.comp P.toLinearMap f) Q.toLinearMap) (Function.Surjective.comp (LinearEquiv.surjective P) (Function.Surjective.comp i (LinearEquiv.surjective Q)))
```

**lean_error:** tail step 1/1 ('exact card_le_of_surjective (LinearMap.comp (LinearMap.comp P.toLinearMap f) Q.toLinearMap) (Function.Surjective.comp (LinearEquiv.surjective P) (Function.Surjective.comp i (LinearEquiv.surjective Q)))'): application type mismatch
