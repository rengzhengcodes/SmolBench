# Basis.coe_toDual_self   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply toDual_apply_right
```

**True premises at k:** `Basis.toDual_apply_right`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | · | · |
| `hint:2` | · | · | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 115.4s, verify 0.1s, in=295, out=6193)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.total_coord b x✝]
simp only [LinearMap.map_sum, LinearMap.map_smul]
rw [Finset.sum_eq_single i]
simp
intros j _ hj
rw [Basis.toDual_apply_self, if_neg hj, MulZeroClass.mul_zero]
simp
```

**lean_error:** tail step 1/7 ('rw [Basis.total_coord b x✝]'): <stdin>:1:25: expected token

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 3.6s, verify 0.1s, in=295, out=6)

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

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 2.0s, verify 0.1s, in=295, out=6)

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

### `stepk:1` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 2.3s, verify 0.1s, in=295, out=6)

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

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 7.6s, verify 0.1s, in=497, out=494)

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

### `hint:2` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 3.7s, verify 0.1s, in=497, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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

### `hint:2` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 1.8s, verify 0.1s, in=497, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 2.2s, verify 0.1s, in=497, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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
