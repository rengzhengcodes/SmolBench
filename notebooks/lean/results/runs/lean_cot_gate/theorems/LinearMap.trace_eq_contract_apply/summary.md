# LinearMap.trace_eq_contract_apply   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Trace.lean`  

**Ground-truth tail (from k):**
```lean
rw [← comp_apply, trace_eq_contract]
```

**True premises at k:** `LinearMap.comp_apply`, `LinearMap.trace_eq_contract`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · · · | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✓ | ✘ ✓ ✘ ✘ | ✓ ✘ ✘ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 64.9s, verify 0.1s, in=392, out=2751)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply TensorProduct.induction_on x
{ simp [contractLeft_zero] }
{ intros ξ m; simp [dualTensorHom_tmul, trace_dual_tensor] }
{ intros a b ha hb; simp [ha, hb] }
```

**lean_error:** tail step 1/4 ('apply TensorProduct.induction_on x'): failed to elaborate eliminator, expected type is not available

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 77.1s, verify 0.1s, in=392, out=3278)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (contractLeft_eq_trace_dualTensorHom x).symm
```

**lean_error:** tail step 1/1 ('exact (contractLeft_eq_trace_dualTensorHom x).symm'): unknown identifier 'contractLeft_eq_trace_dualTensorHom'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 142.3s, verify 0.1s, in=392, out=6656)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply TensorProduct.induction_on x,
{ rintro f m,
  simp only [dualTensorHom_apply, contractLeft_ofTensor] },
{ simp only [contractLeft_zero, trace_zero] },
{ intros y z hy hz,
  simp only [contractLeft_add, trace_add, hy, hz] },
{ intros a y,
  simp only [contractLeft_smul, trace_smul] }
```

**lean_error:** tail step 1/8 ('apply TensorProduct.induction_on x,'): <stdin>:1:34: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 173.4s, verify 0.1s, in=392, out=8556)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply TensorProduct.induction_on x,
{ rintro f m, simp [trace_tensor_dual_left, contractLeftOfTau] },
{ rintro a x y, simp },
{ rintro x y hx hy, simp [hx, hy] }
```

**lean_error:** tail step 1/4 ('apply TensorProduct.induction_on x,'): <stdin>:1:34: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=392, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.3s, verify 0.2s, in=392, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [trace, dualTensorHom]
```

**final state (truncated):**
```
R : Type u_1
inst✝¹² : CommRing R
M : Type u_2
inst✝¹¹ : AddCommGroup M
inst✝¹⁰ : Module R M
N : Type u_3
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.5s, verify 0.2s, in=392, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [trace, contractLeft, contractRight]
```

**final state (truncated):**
```
R : Type u_1
inst✝¹² : CommRing R
M : Type u_2
inst✝¹¹ : AddCommGroup M
inst✝¹⁰ : Module R M
N : Type u_3
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.2s, in=392, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [trace, contractLeft, dualTensorHom, TensorProduct.map]
```

**final state (truncated):**
```
R : Type u_1
inst✝¹² : CommRing R
M : Type u_2
inst✝¹¹ : AddCommGroup M
inst✝¹⁰ : Module R M
N : Type u_3
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=392, out=275)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.2s, verify 0.2s, in=392, out=278)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ext <;> apply span_dualTensorHom_eq_top R M <;> rfl
```

**lean_error:** tail step 1/1 ('apply LinearMap.ext <;> apply span_dualTensorHom_eq_top R M <;> rfl'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.3s, verify 0.1s, in=392, out=288)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [dualTensorHom_apply', trace_apply, contractLeft_apply]
```

**lean_error:** tail step 1/1 ("simp only [dualTensorHom_apply', trace_apply, contractLeft_apply]"): unknown identifier 'dualTensorHom_apply''

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.8s, verify 0.1s, in=392, out=302)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← (tensorHomDual R M M).symm_apply_apply x, trace_tensorHomDual]
```

**lean_error:** tail step 1/1 ('rw [← (tensorHomDual R M M).symm_apply_apply x, trace_tensorHomDual]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 41.0s, verify 0.2s, in=728, out=1689)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 79.3s, verify 0.2s, in=728, out=3394)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 85.0s, verify 0.2s, in=728, out=3648)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 105.7s, verify 0.2s, in=728, out=4647)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply (trace R M) (dualTensorHom R M M) x]
rw [LinearMap.trace_eq_contract R M]
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=728, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=728, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← comp_apply, LinearMap.trace_eq_contract]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.2s, in=728, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.1s, in=728, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('simp [trace_eq_contract, LinearMap.comp_apply]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.4s, verify 0.1s, in=728, out=210)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← comp_apply, trace_eq_contract]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.5s, verify 0.1s, in=728, out=212)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.9s, verify 0.1s, in=728, out=245)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.comp_apply, trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.comp_apply, trace_eq_contract]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.0s, verify 0.1s, in=728, out=344)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 76.4s, verify 0.1s, in=1812, out=1109)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.trace_eq_contract]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 84.8s, verify 0.2s, in=1812, out=1952)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 91.6s, verify 0.2s, in=1812, out=2615)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [trace_eq_contract]
rfl
```

**lean_error:** tail step 1/2 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 123.8s, verify 0.2s, in=1812, out=3617)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1812, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.trace_eq_contract]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1812, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.trace_eq_contract]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=1812, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.trace_eq_contract]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.4s, in=1812, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('simp [trace_eq_contract, LinearMap.comp_apply]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.1s, verify 0.1s, in=1812, out=182)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa only [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simpa only [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 14.7s, verify 0.1s, in=1812, out=226)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.1s, verify 0.1s, in=1812, out=242)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 18.9s, verify 0.1s, in=1812, out=387)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← comp_apply, LinearMap.trace_eq_contract]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 33.1s, verify 0.2s, in=1837, out=1371)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 47.5s, verify 0.2s, in=1837, out=1982)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 50.9s, verify 0.2s, in=1837, out=2140)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 113.6s, verify 0.1s, in=1837, out=5015)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply], rw [trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [← LinearMap.comp_apply], rw [trace_eq_contract]'): <stdin>:1:27: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=1837, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Function.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp [Function.comp_apply, LinearMap.trace_eq_contract]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=1837, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.0s, verify 0.2s, in=1837, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.2s, verify 0.2s, in=1837, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.trace_eq_contract, LinearMap.comp_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.4s, verify 0.2s, in=1837, out=230)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.6s, verify 0.1s, in=1837, out=231)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.comp_apply, LinearMap.trace_eq_contract]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.0s, verify 0.1s, in=1837, out=248)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [comp_apply, trace_eq_contract]
```

**lean_error:** tail step 1/1 ('simp only [comp_apply, trace_eq_contract]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.9s, verify 0.1s, in=1837, out=308)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply, LinearMap.trace_eq_contract]
```
