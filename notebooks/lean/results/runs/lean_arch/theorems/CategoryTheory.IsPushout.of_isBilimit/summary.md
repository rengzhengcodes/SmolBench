# CategoryTheory.IsPushout.of_isBilimit   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`  

**Ground-truth tail (from k):**
```lean
convert IsPushout.of_is_coproduct' h.isColimit HasZeroObject.zeroIsInitial
```

**True premises at k:** `CategoryTheory.IsPushout.of_is_coproduct'`, `CategoryTheory.Limits.HasZeroObject.zeroIsInitial`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=318, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h' := h.is_bilimit_of_is_zero X Y 0 0,
exact h'.is_colimit.is_pushout
```

**lean_error:** tail step 1/2 ("have h' := h.is_bilimit_of_is_zero X Y 0 0,"): <stdin>:1:42: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=290, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← h.isPushout]
apply PushoutCocone.isPushoutOfIsPushoutOfIsInitial _ (isInitialZero _ _)
infer_instance
```

**lean_error:** tail step 1/3 ('rw [← h.isPushout]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=307, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply BinaryBicone.IsBilimit.isPushout
simp [h]
```

**lean_error:** tail step 1/2 ('apply BinaryBicone.IsBilimit.isPushout'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.3s, in=719, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (CategoryTheory.Limits.HasZeroObject.zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (CategoryTheory.Limits.HasZeroObject.zeroIsInitial C)"): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=685, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← b.cofunctor.obj_zero]
apply IsPushout.of_is_coproduct' h.isCoproduct
infer_instance
```

**lean_error:** tail step 1/3 ('rw [← b.cofunctor.obj_zero]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=708, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct'
exact h
exact CategoryTheory.Limits.HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply CategoryTheory.IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1036, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (CategoryTheory.Limits.HasZeroObject.zeroIsInitial)
```

**lean_error:** tail step 1/1 ("exact CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (CategoryTheory.Limits.HasZeroObject.zeroIsInitial)"): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=1005, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.isCoproduct
exact HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/2 ("apply IsPushout.of_is_coproduct' h.isCoproduct"): invalid field 'isCoproduct', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isCoproduct'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1025, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct'
exact h
exact CategoryTheory.Limits.HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply CategoryTheory.IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.9s, in=1060, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact of_is_coproduct' h.to_isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact of_is_coproduct' h.to_isColimit (zeroIsInitial C)"): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1063, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.isCoproduct
apply Limits.HasZeroObject.zeroIsInitial
```
```

**lean_error:** tail step 1/3 ("apply IsPushout.of_is_coproduct' h.isCoproduct"): invalid field 'isCoproduct', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isCoproduct'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1049, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply of_is_coproduct'
exact h
exact zeroIsInitial
```

**lean_error:** tail step 1/3 ("apply of_is_coproduct'"): tactic 'apply' failed, failed to unify
