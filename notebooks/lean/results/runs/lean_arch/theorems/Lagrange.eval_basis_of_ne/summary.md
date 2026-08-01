# Lagrange.eval_basis_of_ne   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨j, ⟨mem_erase.mpr ⟨hij.symm, hj⟩, eval_basisDivisor_right⟩⟩
```

**True premises at k:** `Lagrange.eval_basisDivisor_right`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.6s, in=316, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use j
simp [basisDivisor, hij]
constructor
exact hj
rfl
```

**lean_error:** tail step 4/5 ('exact hj'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=286, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use hj
simp only [mem_erase, Ne, hij, not_false_eq_true, true_and]
intro a ha
simp only [basisDivisor, eval_sub, eval_C, eval_X, sub_self]
use a
simp [*]
```

**lean_error:** tail step 1/6 ('use hj'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 56.6s, verify 1.1s, in=305, out=3594)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply exists_mem_erase_iff.2
refine ⟨j, hj, _⟩
simp [basisDivisor]
```

**lean_error:** tail step 1/3 ('apply exists_mem_erase_iff.2'): unknown identifier 'exists_mem_erase_iff'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=535, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
use hj,
exact ⟨j, Finset.mem_erase_of_ne_of_mem hij hj, Lagrange.eval_basisDivisor_right⟩
```

**lean_error:** tail step 1/2 ('use hj,'): <stdin>:1:7: unexpected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=492, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Lagrange.eval_basisDivisor_right]
exact ⟨j, Finset.mem_erase_of_ne_of_mem hij hj, rfl⟩
```

**lean_error:** tail step 1/2 ('rw [Lagrange.eval_basisDivisor_right]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 20.5s, verify 0.2s, in=524, out=1265)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Exists.intro j
simp [hij, hj, Finset.mem_erase, Lagrange.eval_basisDivisor_right]
```

**final state (truncated):**
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s : Finset ι
v : ι → F
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=688, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use j,
simp_rw [Lagrange.eval_basisDivisor_right],
exact hj
```

**lean_error:** tail step 1/3 ('use j,'): <stdin>:1:6: unexpected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=639, out=57)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Lagrange.basisDivisor, eval_mul, eval_C, eval_sub, eval_X, sub_self, mul_zero]
refine' ⟨j, Finset.mem_erase.mpr ⟨hij, hj⟩, _⟩
simp
```

**lean_error:** tail step 2/3 ("refine' ⟨j, Finset.mem_erase.mpr ⟨hij, hj⟩, _⟩"): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 22.2s, verify 0.2s, in=677, out=1373)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use j
simp [hj, hij, Finset.mem_erase, eval_basisDivisor_right]
```

**final state (truncated):**
```
case h
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s : Finset ι
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=712, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨j, Finset.mem_erase.mpr ⟨hj, hij⟩, _⟩
simp_rw [Lagrange.eval_basisDivisor_right]
```

**lean_error:** tail step 1/2 ("refine' ⟨j, Finset.mem_erase.mpr ⟨hj, hij⟩, _⟩"): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=688, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨j, Finset.mem_erase_of_ne_of_mem hij hj, by simp⟩
```

**lean_error:** tail step 1/1 ('exact ⟨j, Finset.mem_erase_of_ne_of_mem hij hj, by simp⟩'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.3s, in=701, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Exists.intro i
simp [hij, Finset.mem_erase]
```

**final state (truncated):**
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s : Finset ι
v : ι → F
...
```
