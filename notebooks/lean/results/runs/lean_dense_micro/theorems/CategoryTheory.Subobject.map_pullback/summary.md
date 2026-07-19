# CategoryTheory.Subobject.map_pullback   (k=13, 14 tactics total)

file: `Mathlib/CategoryTheory/Subobject/Basic.lean`  

**Ground-truth tail (from k):**
```lean
apply PullbackCone.IsLimit.lift_snd
```

**True premises at k:** `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=420, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [assoc, pullback.lift_snd]
```

**lean_error:** tail step 1/1 ('rw [assoc, pullback.lift_snd]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.9s, verify 0.2s, in=420, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [assoc, lift_fst, assoc, lift_snd, comp_id]
exact id_comp _
```

**lean_error:** tail step 1/2 ('rw [assoc, lift_fst, assoc, lift_snd, comp_id]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.1s, verify 0.2s, in=420, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [assoc, lift_mk, assoc, IsLimit.fac t WalkingCospan.right, pullback.condition]
rw [←cancel_mono g]
exact IsLimit.fac t WalkingCospan.left
```

**lean_error:** tail step 1/3 ('rw [assoc, lift_mk, assoc, IsLimit.fac t WalkingCospan.right, pullback.condition]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.4s, verify 0.2s, in=420, out=41)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [assoc, t.fac _ walking_cospan.right, pullback.condition_assoc]
rw [pullback.lift_fst_assoc, assoc, pullback.condition]
erw [pullback.lift_snd]
```

**lean_error:** tail step 1/3 ('rw [assoc, t.fac _ walking_cospan.right, pullback.condition_assoc]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=420, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact pullback.lift_snd _ _ _
```

**lean_error:** tail step 1/1 ('exact pullback.lift_snd _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=420, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact pullback.lift_snd _ _ _
```

**lean_error:** tail step 1/1 ('exact pullback.lift_snd _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=420, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact pullback.lift_snd _ _ _
```

**lean_error:** tail step 1/1 ('exact pullback.lift_snd _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.5s, in=420, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact t.fac _ WalkingSpan.right
```

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.9s, verify 0.2s, in=988, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [assoc, PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [assoc, PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=988, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.3s, in=988, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.7s, verify 0.3s, in=988, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]
rfl
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.5s, in=988, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact PullbackCone.IsLimit.lift_snd _ _ _ _
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 2.1s, verify 0.5s, in=988, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact PullbackCone.IsLimit.lift_snd _ _ _ _
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.5s, in=988, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact PullbackCone.IsLimit.lift_snd _ _ _ _
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 3.1s, verify 0.5s, in=988, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact PullbackCone.IsLimit.lift_snd _ _ _ _
```
