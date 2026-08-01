# CategoryTheory.Subobject.map_pullback   (k=13, 14 tactics total)

file: `Mathlib/CategoryTheory/Subobject/Basic.lean`  

**Ground-truth tail (from k):**
```lean
apply PullbackCone.IsLimit.lift_snd
```

**True premises at k:** `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.3s, in=420, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [assoc, pullback.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [assoc, pullback.lift_snd]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=390, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsLimit.fac]
simp
rw [← Category.assoc, ← MonoOver.w]
simp
rw [Category.assoc]
simp
rw [IsLimit.fac]
aesop_cat
```

**lean_error:** tail step 1/8 ('rw [IsLimit.fac]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.3s, in=409, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pullback.lift_fst
apply pullback.lift_snd
```

**lean_error:** tail step 1/2 ('apply pullback.lift_fst'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.4s, in=988, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.6s, in=969, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]
rfl
```

**lean_error:** tail step 1/2 ('rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=977, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.8s, in=1213, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=1197, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]
rfl
```

**lean_error:** tail step 1/2 ('rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.3s, in=1202, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1237, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [assoc, PullbackCone.IsLimit.lift_snd]
rfl
rfl
```

**lean_error:** tail step 1/3 ('rw [assoc, PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=1244, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]
rfl
```

**lean_error:** tail step 1/2 ('rw [PullbackCone.IsLimit.lift_snd t _ _ ⋯]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=1226, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
