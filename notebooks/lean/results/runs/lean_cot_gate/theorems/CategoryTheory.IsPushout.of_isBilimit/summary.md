# CategoryTheory.IsPushout.of_isBilimit   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`  

**Ground-truth tail (from k):**
```lean
convert IsPushout.of_is_coproduct' h.isColimit HasZeroObject.zeroIsInitial
```

**True premises at k:** `CategoryTheory.IsPushout.of_is_coproduct'`, `CategoryTheory.Limits.HasZeroObject.zeroIsInitial`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=291, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsPushout.of_isColimit_zero _ _ _ h.colimit
```

**lean_error:** tail step 1/1 ('exact IsPushout.of_isColimit_zero _ _ _ h.colimit'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=291, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isPushout_of_isColimit_of_isColimit_coconeAtZero b.isColimit
```

**lean_error:** tail step 1/1 ('exact isPushout_of_isColimit_of_isColimit_coconeAtZero b.isColimit'): unknown identifier 'isPushout_of_isColimit_of_isColimit_coconeAtZero'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=291, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isPushout_of_isZero_left_of_isZero_right _ _ zeroIsZero zeroIsZero
```

**lean_error:** tail step 1/1 ('exact h.isPushout_of_isZero_left_of_isZero_right _ _ zeroIsZero zeroIsZero'): invalid field 'isPushout_of_isZero_left_of_isZero_right', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isPushout_of_isZero_left_of_isZero_right'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.9s, verify 0.1s, in=291, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsPushout.of_ι_inr_eq_zero _ _ (h.eq_of_w _ (b.fac _ WalkingBiconePoint.left)
  (b.fac _ WalkingBiconePoint.right).trans (zero_comp _).symm)
```

**lean_error:** tail step 1/2 ('exact IsPushout.of_ι_inr_eq_zero _ _ (h.eq_of_w _ (b.fac _ WalkingBiconePoint.left)'): <stdin>:1:83: unexpected end of input; expected ')', ',' or ':'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=692, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=692, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isCoproduct HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isCoproduct HasZeroObject.zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=692, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=692, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1011, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=1011, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=1011, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.2s, in=1011, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.2s, in=1036, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.colimitCocone.isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.colimitCocone.isColimit (zeroIsInitial C)"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1036, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' (Limits.IsColimit.of_isBilimit h) (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' (Limits.IsColimit.of_isBilimit h) (zeroIsInitial C)"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.1s, verify 0.1s, in=1036, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 71.2s, verify 0.1s, in=1036, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} _)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} _)"): type mismatch
