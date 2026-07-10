# Basis.coe_toDual_self   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply toDual_apply_right
```

**True premises at k:** `Basis.toDual_apply_right`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:2` | ✓ | ✓ | ✘ | ✓ | · | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=325, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, Basis.coord_apply, Basis.repr_self_apply] 
exact rfl
```

**lean_error:** tail step 1/2 ('rw [toDual_apply, Basis.coord_apply, Basis.repr_self_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=325, out=80)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, Basis.sum_repr, Finsupp.sum, Finsupp.sum, Finset.sum_eq_single_of_mem i
  (Finset.mem_univ _), Finset.sum_eq_single_of_mem i (Finset.mem_univ _), coord_apply, ←
  Finsupp.smul_single_one (b i), smul_eq_mul, mul_one]
```

**lean_error:** tail step 1/3 ('rw [toDual_apply, Basis.sum_repr, Finsupp.sum, Finsupp.sum, Finset.sum_eq_single_of_mem i'): <stdin>:1:89: unexpected end of input; expected ']'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=314, out=367)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply toDual_apply
apply coord_apply
```

**lean_error:** tail step 1/2 ('apply toDual_apply'): tactic 'apply' failed, failed to unify

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=305, out=151)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [toDual_apply, LinearMap.comp_apply, LinearMap.id_apply]
rw [coord_apply, Basis.repr_self_apply, Finsupp.single_eq_same]
```

**lean_error:** tail step 1/2 ('rw [toDual_apply, LinearMap.comp_apply, LinearMap.id_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 92.2s, verify 0.1s, in=295, out=6445)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.4s, verify 0.6s, in=295, out=6)

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

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.5s, verify 0.2s, in=525, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
rfl
```

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=525, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right, Basis.coord_apply]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=514, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right]
refl
```

**lean_error:** tail step 2/2 ('refl'): <stdin>:1:1: unknown tactic

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 0.5s, verify 0.2s, in=505, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [toDual_apply_right]
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 6.6s, verify 0.1s, in=497, out=406)

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

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.3s, verify 0.1s, in=497, out=6)

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
