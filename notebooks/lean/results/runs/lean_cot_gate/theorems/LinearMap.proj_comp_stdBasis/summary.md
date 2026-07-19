# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ · · | ✘ ✘ ✘ ✘ ✘ ✘ X X ✘ |
| `hint:2` | ✘ ✘ ✓ ✘ | · ✓ ✓ ✓ | ✓ ✘ ✓ ✓ ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✘ ✘ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ ✓ ✓ ✓ X |
| `noise:3` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✘ ✓ ✘ ✓ ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 133.0s, verify 0.3s, in=285, out=6096)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
rw [LinearMap.comp_apply, LinearMap.stdBasis_apply, LinearMap.proj_apply]
split_ifs <;> rfl
```

**lean_error:** tail step 3/3 ('split_ifs <;> rfl'): tactic 'split_ifs' failed, no if-then-else conditions to split

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 185.9s, verify 0.3s, in=285, out=5010)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
rw [LinearMap.comp_apply, LinearMap.stdBasis_apply, LinearMap.proj_apply]
split_ifs <;> simp
```

**lean_error:** tail step 3/3 ('split_ifs <;> simp'): tactic 'split_ifs' failed, no if-then-else conditions to split

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 226.6s, verify 0.4s, in=285, out=6881)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp [stdBasis_apply, proj_apply]
congr
rw [if_congr_eq]
```

**lean_error:** tail step 4/4 ('rw [if_congr_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 243.2s, verify 0.3s, in=285, out=11038)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext r
simp [stdBasis_apply]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.7s, verify 0.1s, in=285, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
```

**final state (truncated):**
```
case h
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=285, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.0s, verify 0.1s, in=285, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Function.comp, diag]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.6s, verify 0.1s, in=285, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Function.comp, LinearMap.stdBasis, LinearMap.proj]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.7s, verify 0.1s, in=285, out=178)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact proj_comp_stdBasis_eq_diag R φ i j
```

**lean_error:** tail step 1/1 ('exact proj_comp_stdBasis_eq_diag R φ i j'): unknown identifier 'proj_comp_stdBasis_eq_diag'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 8.1s, verify 0.1s, in=285, out=253)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.8s, verify 0.1s, in=285, out=276)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [LinearMap.ext_iff, Function.comp_apply, proj_apply, stdBasis_apply, diag_apply]
```

**lean_error:** tail step 1/1 ('simp_rw [LinearMap.ext_iff, Function.comp_apply, proj_apply, stdBasis_apply, diag_apply]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.9s, verify 0.1s, in=285, out=316)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.comp_apply, LinearMap.stdBasis_apply, Pi.single_apply, LinearMap.proj_apply,
  LinearMap.diagonal]
```

**lean_error:** tail step 1/2 ('simp [LinearMap.comp_apply, LinearMap.stdBasis_apply, Pi.single_apply, LinearMap.proj_apply,'): <stdin>:1:92: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 11.8s, verify 0.1s, in=285, out=379)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.ext, LinearMap.stdBasis_apply, LinearMap.diag_apply, LinearMap.comp_apply,
  Pi.single_apply]
```

**lean_error:** tail step 1/2 ('simp [LinearMap.ext, LinearMap.stdBasis_apply, LinearMap.diag_apply, LinearMap.comp_apply,'): <stdin>:1:90: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 15.6s, verify 0.1s, in=285, out=512)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split_ifs <;> simp [stdBasis_comp_proj, stdBasis_eq_zero, *]
```

**lean_error:** tail step 1/1 ('split_ifs <;> simp [stdBasis_comp_proj, stdBasis_eq_zero, *]'): tactic 'split_ifs' failed, no if-then-else conditions to split

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **exception**  (gen 80.4s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance i-077d8082814a9172d is running). If the instance is running, your public IP probably changed and the security group is blocking you: re-run provision_spot_instance() to re-authorize your current IP.

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **exception**  (gen 80.4s, verify 0.0s, in=0, out=0)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance i-077d8082814a9172d is running). If the instance is running, your public IP probably changed and the security group is blocking you: re-run provision_spot_instance() to re-authorize your current IP.

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.2s, verify 0.1s, in=285, out=410)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [coeFn, LinearMap.coe_comp, LinearMap.coe_stdBasis, Pi.single_eq_pi_single,
  LinearMap.coe_proj]
```

**lean_error:** tail step 1/2 ('simp only [coeFn, LinearMap.coe_comp, LinearMap.coe_stdBasis, Pi.single_eq_pi_single,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 19.9s, verify 0.1s, in=671, out=909)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j]
rw [proj_pi (diag j) i]
```

**lean_error:** tail step 1/2 ('rw [stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 47.0s, verify 0.1s, in=671, out=2347)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 85.1s, verify 0.2s, in=671, out=3984)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 117.7s, verify 0.1s, in=671, out=5417)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag], exact proj_pi (diag j) i
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag], exact proj_pi (diag j) i'): <stdin>:1:24: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.9s, verify 0.1s, in=671, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.1s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.3s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.5s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 5.6s, verify 0.1s, in=671, out=180)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=671, out=196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [← stdBasis_eq_pi_diag, proj_pi]
```

**lean_error:** tail step 1/1 ('simpa only [← stdBasis_eq_pi_diag, proj_pi]'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.0s, verify 0.1s, in=671, out=224)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.1s, verify 0.1s, in=671, out=226)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 11.9s, verify 0.1s, in=671, out=202)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 12.0s, verify 0.1s, in=671, out=205)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 12.6s, verify 0.1s, in=671, out=196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **success**  (gen 13.9s, verify 0.1s, in=671, out=222)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 65.9s, verify 0.1s, in=1089, out=2134)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 66.9s, verify 0.2s, in=1089, out=901)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 136.7s, verify 0.1s, in=1089, out=3181)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 143.0s, verify 0.1s, in=1089, out=2333)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw stdBasis_eq_pi_diag
exact proj_pi (diag j) i
```

**lean_error:** tail step 1/2 ('rw stdBasis_eq_pi_diag'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.7s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.8s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.9s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 20.4s, verify 0.1s, in=1089, out=189)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 21.3s, verify 0.1s, in=1089, out=252)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 21.4s, verify 0.1s, in=1089, out=227)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 21.8s, verify 0.1s, in=1089, out=232)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 21.9s, verify 0.1s, in=1089, out=218)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 22.2s, verify 0.1s, in=1089, out=234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 24.6s, verify 0.1s, in=1089, out=249)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **exception**  (gen 99.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance i-077d8082814a9172d is running). If the instance is running, your public IP probably changed and the security group is blocking you: re-run provision_spot_instance() to re-authorize your current IP.

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 22.8s, verify 0.2s, in=1113, out=1064)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 62.1s, verify 0.1s, in=1113, out=3082)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 71.1s, verify 0.1s, in=1113, out=3426)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j]
rw [proj_pi]
trivial
```

**lean_error:** tail step 1/3 ('rw [stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 90.5s, verify 0.2s, in=1113, out=843)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag R φ j]
rw [proj_pi (diag j)]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.1s, verify 0.1s, in=1113, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=1113, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=1113, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.4s, verify 0.1s, in=1113, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 14.6s, verify 0.1s, in=1113, out=244)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← stdBasis_eq_pi_diag, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [← stdBasis_eq_pi_diag, proj_pi]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 14.8s, verify 0.1s, in=1113, out=227)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.0s, verify 0.1s, in=1113, out=211)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.5s, verify 0.1s, in=1113, out=187)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 18.1s, verify 0.1s, in=1113, out=201)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 18.9s, verify 0.1s, in=1113, out=238)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 21.0s, verify 0.1s, in=1113, out=290)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi (diag j) i]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi (diag j) i]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 88.7s, verify 0.1s, in=1113, out=218)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [stdBasis_eq_pi_diag, proj_pi]
```
