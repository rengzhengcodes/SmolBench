# Basis.coe_toDual_self   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply toDual_apply_right
```

**True premises at k:** `Basis.toDual_apply_right`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=325, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply]
rw [coord_apply]
```

**lean_error:** tail step 1/2 ('rw [toDual_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=325, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, Basis.coord_apply, Basis.repr_self_apply] 
exact rfl
```

**lean_error:** tail step 1/2 ('rw [toDual_apply, Basis.coord_apply, Basis.repr_self_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.4s, verify 1.2s, in=325, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, coord_apply] 
congr 
exact Basis.total_apply b x✝
```

**lean_error:** tail step 1/3 ('rw [toDual_apply, coord_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=325, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, coord_apply]
congr
rw [toDual_def, coord_def]
rfl
```

**lean_error:** tail step 1/4 ('rw [toDual_apply, coord_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=325, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact toDual_apply _ _
```

**lean_error:** tail step 1/1 ('exact toDual_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=325, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact toDual_apply _ _
```

**lean_error:** tail step 1/1 ('exact toDual_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.2s, in=325, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (toDual_apply _ _ _).trans (coord_apply _ _ _).symm
```

**lean_error:** tail step 1/1 ('exact (toDual_apply _ _ _).trans (coord_apply _ _ _).symm'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=325, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, Basis.sum_repr x✝, Finsupp.sum, Finsupp.sum, coord_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply, Basis.sum_repr x✝, Finsupp.sum, Finsupp.sum, coord_apply]'): <stdin>:1:34: expected token

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 0.6s, verify 0.1s, in=525, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right, Basis.coord_apply]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=525, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
rfl
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.0s, verify 0.2s, in=525, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right]
rw [coord_apply]
rw [repr_apply]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 2.7s, verify 0.2s, in=525, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
rw [Basis.coord_apply]
rw [Basis.repr_self]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=525, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right, repr_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply_right, repr_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=525, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right, ← Basis.coord_apply]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=525, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right, Basis.coord_apply]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=525, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right, repr_apply, Finsupp.single_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply_right, repr_apply, Finsupp.single_apply]'): tactic 'rewrite' failed, equality or iff proof expected
