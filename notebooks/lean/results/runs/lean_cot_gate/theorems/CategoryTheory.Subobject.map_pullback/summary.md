# CategoryTheory.Subobject.map_pullback   (k=13, 14 tactics total)

file: `Mathlib/CategoryTheory/Subobject/Basic.lean`  

**Ground-truth tail (from k):**
```lean
apply PullbackCone.IsLimit.lift_snd
```

**True premises at k:** `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 193.0s, verify 0.2s, in=388, out=8009)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [PullbackCone.IsLimit.fac_snd]
```

**lean_error:** tail step 1/1 ('rw [PullbackCone.IsLimit.fac_snd]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 207.9s, verify 0.1s, in=388, out=8673)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [PullbackCone.IsLimit.fac2]
```

**lean_error:** tail step 1/1 ('simp_rw [PullbackCone.IsLimit.fac2]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 260.5s, verify 0.1s, in=388, out=11145)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw PullbackCone.IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('rw PullbackCone.IsLimit.lift_snd'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 775.9s, verify 0.0s, in=388, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.5s, verify 0.1s, in=388, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=388, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=388, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.1s, in=388, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=388, out=226)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.6s, verify 0.1s, in=388, out=244)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.7s, verify 0.2s, in=388, out=250)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.6s, verify 0.2s, in=388, out=275)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 115.4s, verify 0.6s, in=957, out=4508)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 116.0s, verify 0.1s, in=957, out=4516)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 116.4s, verify 0.1s, in=957, out=4596)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 136.7s, verify 0.1s, in=957, out=5442)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=957, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=957, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=957, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=957, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.5s, verify 0.1s, in=957, out=241)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('simp [IsLimit.lift_snd]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=957, out=272)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.6s, verify 0.1s, in=957, out=344)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ht := t]
```

**lean_error:** tail step 1/1 ('simp [ht := t]'): <stdin>:1:9: expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 18.3s, verify 0.2s, in=957, out=646)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsLimit.lift_snd t _ _ _]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd t _ _ _]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 151.2s, verify 0.2s, in=1185, out=1558)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 157.9s, verify 0.1s, in=1185, out=5876)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 213.3s, verify 0.1s, in=1185, out=4301)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 259.9s, verify 0.5s, in=1185, out=6579)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=1185, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1185, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=1185, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1185, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.1s, verify 0.7s, in=1185, out=253)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.3s, verify 0.2s, in=1185, out=298)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.7s, verify 0.2s, in=1185, out=259)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.9s, verify 0.1s, in=1185, out=285)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('simp [IsLimit.lift_snd]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 14.8s, verify 0.1s, in=1209, out=570)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 122.8s, verify 0.1s, in=1209, out=4879)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 131.6s, verify 0.1s, in=1209, out=5265)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 215.4s, verify 0.1s, in=1209, out=8993)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=1209, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.4s, verify 0.1s, in=1209, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=1209, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.6s, verify 0.1s, in=1209, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=1209, out=186)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.9s, verify 0.1s, in=1209, out=188)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsLimit.lift_snd
```

**lean_error:** tail step 1/1 ('apply IsLimit.lift_snd'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.4s, verify 0.1s, in=1209, out=239)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.4s, verify 0.2s, in=1209, out=340)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [IsLimit.lift_snd]'): tactic 'rewrite' failed, equality or iff proof expected
