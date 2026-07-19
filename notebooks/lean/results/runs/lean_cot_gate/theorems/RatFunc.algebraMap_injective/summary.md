# RatFunc.algebraMap_injective   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
exact ofFractionRing_injective.comp (IsFractionRing.injective _ _)
```

**True premises at k:** `IsFractionRing.injective`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 133.0s, verify 0.2s, in=236, out=5387)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp
apply algebraMap_fractionRing_injective
apply algebraMap_fractionRing_injective
```

**lean_error:** tail step 2/3 ('apply algebraMap_fractionRing_injective'): unknown identifier 'algebraMap_fractionRing_injective'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 133.1s, verify 0.6s, in=236, out=5385)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp
apply FractionRing.injective_algebraMap
apply AlgebraMap.injective
```

**lean_error:** tail step 2/3 ('apply FractionRing.injective_algebraMap'): unknown constant 'FractionRing.injective_algebraMap'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 133.8s, verify 0.1s, in=236, out=5416)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsFractionRing.algebraMap_injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.algebraMap_injective'): unknown constant 'IsFractionRing.algebraMap_injective'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 143.2s, verify 0.2s, in=236, out=5695)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp
apply injective_of_ring_hom_from_field
apply AlgebraMap_injective
```

**lean_error:** tail step 2/3 ('apply injective_of_ring_hom_from_field'): unknown identifier 'injective_of_ring_hom_from_field'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=236, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): type class instance expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.9s, in=236, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Function.Injective.comp ofFractionRing_injective (RingHom.injective _)
```

**lean_error:** tail step 1/1 ('exact Function.Injective.comp ofFractionRing_injective (RingHom.injective _)'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=236, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Function.Injective.comp (ofFractionRing_injective K[X]) (algebraMap_injective _)
```

**lean_error:** tail step 1/1 ('exact Function.Injective.comp (ofFractionRing_injective K[X]) (algebraMap_injective _)'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.5s, verify 0.3s, in=236, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Function.Injective.comp (IsFractionRing.injective K[X] _) (ofFractionRing_injective K)
```

**lean_error:** tail step 1/1 ('exact Function.Injective.comp (IsFractionRing.injective K[X] _) (ofFractionRing_injective K)'): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.2s, verify 0.1s, in=236, out=156)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp (IsFractionRing.injective_algebraMap K[X] (FractionRing K[X]))
```

**lean_error:** tail step 1/1 ('apply Function.Injective.comp (IsFractionRing.injective_algebraMap K[X] (FractionRing K[X]))'): unknown constant 'IsFractionRing.injective_algebraMap'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=236, out=182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Function.Injective.comp RingHom.injective_ofFractionRing RingHom.injective_algebraMap
```

**lean_error:** tail step 1/1 ('exact Function.Injective.comp RingHom.injective_ofFractionRing RingHom.injective_algebraMap'): unknown constant 'RingHom.injective_ofFractionRing'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.9s, verify 0.1s, in=236, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Function.Injective.comp ofFractionRing_injective (algebraMap_injective_of_isDomain _)
```

**lean_error:** tail step 1/1 ('exact Function.Injective.comp ofFractionRing_injective (algebraMap_injective_of_isDomain _)'): unknown identifier 'algebraMap_injective_of_isDomain'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.9s, verify 0.1s, in=236, out=461)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact injective_of_left_inverse (ofFractionRing_bijective.2 _)
```

**lean_error:** tail step 1/1 ('exact injective_of_left_inverse (ofFractionRing_bijective.2 _)'): unknown identifier 'injective_of_left_inverse'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 4.3s, verify 0.1s, in=410, out=219)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 23.2s, verify 0.9s, in=410, out=1099)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 29.5s, verify 1.3s, in=410, out=1378)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 35.6s, verify 0.1s, in=410, out=1623)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=410, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective _ _
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=410, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective _ _
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=410, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective K[X] (FractionRing K[X])
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective K[X] (FractionRing K[X])'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=410, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact RatFunc.injective_ofFractionRing.comp (IsFractionRing.injective K[X])
```

**lean_error:** tail step 1/1 ('exact RatFunc.injective_ofFractionRing.comp (IsFractionRing.injective K[X])'): unknown constant 'RatFunc.injective_ofFractionRing.comp'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 4.2s, verify 0.1s, in=410, out=125)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('apply RatFunc.algebraMap_injective'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.7s, verify 0.1s, in=410, out=172)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.algebraMap_injective'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=410, out=214)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.algebraMap_injective'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.6s, verify 0.1s, in=410, out=271)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('apply RatFunc.algebraMap_injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 21.0s, verify 0.1s, in=773, out=523)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 30.9s, verify 0.1s, in=773, out=774)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 35.2s, verify 0.1s, in=773, out=589)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 172.1s, verify 0.1s, in=773, out=3777)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.1s, in=773, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective _ _
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.8s, verify 0.2s, in=773, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective K[X] _
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective K[X] _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=773, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact RatFunc.injective_ofFractionRing.comp (IsFractionRing.injective K[X])
```

**lean_error:** tail step 1/1 ('exact RatFunc.injective_ofFractionRing.comp (IsFractionRing.injective K[X])'): unknown constant 'RatFunc.injective_ofFractionRing.comp'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.1s, verify 0.1s, in=773, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective K[X] (FractionRing K[X])
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective K[X] (FractionRing K[X])'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.3s, verify 0.1s, in=773, out=167)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.3s, verify 0.1s, in=773, out=173)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.1s, verify 0.1s, in=773, out=240)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.algebraMap_injective'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.6s, verify 0.1s, in=773, out=273)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=798, out=277)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 9.4s, verify 0.1s, in=798, out=490)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 26.2s, verify 0.1s, in=798, out=1228)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 92.4s, verify 0.1s, in=798, out=3838)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=798, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective _ _
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=798, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact RatFunc.injective_ofFractionRing.comp IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.injective_ofFractionRing.comp IsFractionRing.injective'): unknown constant 'RatFunc.injective_ofFractionRing.comp'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=798, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact RatFunc.injective_ofFractionRing.comp IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.injective_ofFractionRing.comp IsFractionRing.injective'): unknown constant 'RatFunc.injective_ofFractionRing.comp'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=798, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective K[X] (FractionRing K[X])
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective K[X] (FractionRing K[X])'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.1s, verify 0.1s, in=798, out=151)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=798, out=199)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← ofFractionRing_comp_algebraMap, IsFractionRing.injective]
```

**lean_error:** tail step 1/1 ('rw [← ofFractionRing_comp_algebraMap, IsFractionRing.injective]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.9s, verify 0.1s, in=798, out=210)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.3s, verify 0.1s, in=798, out=225)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact RatFunc.algebraMap_injective
```

**lean_error:** tail step 1/1 ('exact RatFunc.algebraMap_injective'): type mismatch
