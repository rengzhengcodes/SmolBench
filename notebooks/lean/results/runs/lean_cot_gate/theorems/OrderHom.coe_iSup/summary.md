# OrderHom.coe_iSup   (k=1, 2 tactics total)

file: `Mathlib/Order/Hom/Order.lean`  

**Ground-truth tail (from k):**
```lean
simp [iSup_apply]
```

**True premises at k:** `OrderHom.iSup_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✓ ✓ |
| `hint:2` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | · ✘ ✓ ✘ |
| `noise:3` | · ✘ · ✘ | · ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 10.2s, verify 0.1s, in=270, out=452)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 27.5s, verify 0.1s, in=270, out=1276)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 78.8s, verify 0.1s, in=270, out=4149)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coe_supr]
```

**lean_error:** tail step 1/1 ('rw [coe_supr]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 126.7s, verify 0.1s, in=270, out=6517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [supr_apply]
```

**lean_error:** tail step 1/1 ('rw [supr_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=270, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=270, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=270, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=270, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 7.6s, verify 0.1s, in=509, out=339)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=509, out=451)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact OrderHom.iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact OrderHom.iSup_apply f x'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 12.8s, verify 0.1s, in=509, out=570)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 17.8s, verify 0.1s, in=509, out=787)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=509, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=509, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 18.0s, verify 0.1s, in=1072, out=330)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 20.2s, verify 0.1s, in=1072, out=578)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact OrderHom.iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact OrderHom.iSup_apply f x'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 23.1s, verify 0.1s, in=1072, out=692)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact OrderHom.iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact OrderHom.iSup_apply f x'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 29.7s, verify 0.1s, in=1072, out=1037)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.7s, verify 0.3s, in=1072, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.1s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=1072, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 7.3s, verify 0.1s, in=1099, out=327)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 8.0s, verify 0.1s, in=1099, out=357)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 10.3s, verify 0.1s, in=1099, out=456)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 44.5s, verify 0.1s, in=1099, out=2080)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply OrderHom.iSup_apply
```

**lean_error:** tail step 1/1 ('apply OrderHom.iSup_apply'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=1099, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_apply f x
```

**lean_error:** tail step 1/1 ('exact iSup_apply f x'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [iSup_apply]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=1099, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [iSup_apply]
```
