# OrderHom.coe_iSup   (k=1, 2 tactics total)

file: `Mathlib/Order/Hom/Order.lean`  

**Ground-truth tail (from k):**
```lean
simp [iSup_apply]
```

**True premises at k:** `OrderHom.iSup_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ · ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.4s, in=297, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup]
congr
funext
rw [OrderHom.coe_iSup]
```

**lean_error:** tail step 4/4 ('rw [OrderHom.coe_iSup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.4s, in=297, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_apply]
congr
funext
rw [OrderHom.coe_iSup]
```

**lean_error:** tail step 4/4 ('rw [OrderHom.coe_iSup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.8s, verify 0.3s, in=297, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup_apply]
congr
ext i
rw [OrderHom.coe_coe]
```

**lean_error:** tail step 3/4 ('ext i'): no applicable extensionality theorem found for

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.1s, verify 0.2s, in=297, out=56)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' le_antisymm _ _
rw [le_iSup_iff]
intro i
rw [OrderHom.le_iff]
apply le_iSup
rw [iSup_le_iff]
intro i
rw [OrderHom.le_iff]
apply le_iSup_of_le i
```

**lean_error:** tail step 2/9 ('rw [le_iSup_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=297, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_apply (fun i => f i) _ x
```

**lean_error:** tail step 1/1 ('exact iSup_apply (fun i => f i) _ x'): function expected at

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=297, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (OrderIso.fun_iSup_apply (fun i => f i) x).symm
```

**lean_error:** tail step 1/1 ('exact (OrderIso.fun_iSup_apply (fun i => f i) x).symm'): unknown constant 'OrderIso.fun_iSup_apply'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=297, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (OrderIso.fun_iSup_apply (α →o β) ι x).symm
```

**lean_error:** tail step 1/1 ('exact (OrderIso.fun_iSup_apply (α →o β) ι x).symm'): unknown constant 'OrderIso.fun_iSup_apply'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=297, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (OrderIso.fun_iSup_apply (OrderIso.fun β α) _ _).symm
```

**lean_error:** tail step 1/1 ('exact (OrderIso.fun_iSup_apply (OrderIso.fun β α) _ _).symm'): unknown constant 'OrderIso.fun_iSup_apply'

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.5s, verify 0.1s, in=536, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact OrderHom.iSup_apply _ _
```

**lean_error:** tail step 1/1 ('exact OrderHom.iSup_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 2 → **incomplete**  (gen 0.5s, verify 0.1s, in=536, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.6s, verify 0.2s, in=536, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=536, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [OrderHom.iSup_apply] 
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=536, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply _ _
```

**lean_error:** tail step 1/1 ('exact iSup_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=536, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply _ _
```

**lean_error:** tail step 1/1 ('exact iSup_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=536, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply _ _
```

**lean_error:** tail step 1/1 ('exact iSup_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=536, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_apply _ _
```

**lean_error:** tail step 1/1 ('exact iSup_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables
