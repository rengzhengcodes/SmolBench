# Basis.coe_toDual_self   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply toDual_apply_right
```

**True premises at k:** `Basis.toDual_apply_right`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | X ✘ ✘ ✘ ✘ | · · · · | ✘ ✘ ✘ · ✘ · ✘ ✘ |
| `hint:2` | · ✘ · ✘ | ✓ ✓ ✓ ✓ | ✓ · · · ✘ ✘ ✘ · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **exception**  (gen 80.3s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance i-00c5fbc8f31798b2f is running). If the instance is running, your public IP probably changed and the security group is blocking you: re-run provision_spot_instance() to re-authorize your current IP.

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 160.8s, verify 0.2s, in=295, out=7302)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Basis.coord_apply b i x
```

**lean_error:** tail step 1/1 ('exact Basis.coord_apply b i x'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 161.6s, verify 0.1s, in=295, out=7626)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.sum_coords_self b x]
simp only [linearMap.map_sum, linearMap.map_smul]
rw dual_basis_eval
simp only [if_true, if_false, finset.sum_ite_eq, mul_one, mul_zero]
ring
```

**lean_error:** tail step 1/5 ('rw [Basis.sum_coords_self b x]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 178.3s, verify 0.2s, in=295, out=8001)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 62.9s, verify 0.1s, in=295, out=3488)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [to_dual_apply]
```

**lean_error:** tail step 1/1 ('rw [to_dual_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.2s, verify 0.1s, in=295, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.3s, verify 0.1s, in=295, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.5s, verify 0.1s, in=295, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [toDual_apply]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.6s, verify 0.2s, in=295, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.toDual]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.0s, verify 0.1s, in=295, out=131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 4.3s, verify 0.1s, in=295, out=140)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 4.4s, verify 0.1s, in=295, out=145)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, rfl]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply, rfl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 4.8s, verify 0.1s, in=295, out=155)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [toDual_apply]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 5.2s, verify 0.1s, in=295, out=170)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dualBasis_toDual, dualBasis_apply]
```

**lean_error:** tail step 1/1 ('rw [dualBasis_toDual, dualBasis_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 5.9s, verify 0.1s, in=295, out=196)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 7.9s, verify 0.1s, in=295, out=265)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, Basis.coord_apply]
```

**lean_error:** tail step 1/1 ('rw [toDual_apply, Basis.coord_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 77.0s, verify 0.1s, in=295, out=283)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coord, toDual_repr_apply]
```

**lean_error:** tail step 1/1 ('rw [coord, toDual_repr_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 11.8s, verify 0.1s, in=497, out=356)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 19.4s, verify 0.2s, in=497, out=1047)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right]
refl
```

**lean_error:** tail step 2/2 ('refl'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 19.8s, verify 0.1s, in=497, out=792)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 53.0s, verify 0.1s, in=497, out=2690)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact b.toDual_apply_right i x✝
```

**lean_error:** tail step 1/1 ('exact b.toDual_apply_right i x✝'): <stdin>:1:30: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=497, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toDual_apply_right]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=497, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toDual_apply_right, coord]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=497, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toDual_apply_right, coord]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=497, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Basis.coord, toDual_apply_right]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.4s, verify 0.1s, in=497, out=177)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply b.toDual_apply_right
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 5.8s, verify 0.1s, in=497, out=190)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **incomplete**  (gen 8.7s, verify 0.8s, in=497, out=159)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **incomplete**  (gen 9.5s, verify 0.1s, in=497, out=183)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 10.1s, verify 0.1s, in=497, out=191)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact b.toDual_apply_right i x✝
```

**lean_error:** tail step 1/1 ('exact b.toDual_apply_right i x✝'): <stdin>:1:30: expected end of input

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 11.2s, verify 0.1s, in=497, out=253)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact b.toDual_apply_right i x✝
```

**lean_error:** tail step 1/1 ('exact b.toDual_apply_right i x✝'): <stdin>:1:30: expected end of input

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 75.1s, verify 0.1s, in=497, out=201)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [toDual_apply_right, b.repr_apply]
```

**lean_error:** tail step 1/1 ('simp [toDual_apply_right, b.repr_apply]'): invalid field 'repr_apply', the environment does not contain 'Basis.repr_apply'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 75.5s, verify 0.1s, in=497, out=213)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```
