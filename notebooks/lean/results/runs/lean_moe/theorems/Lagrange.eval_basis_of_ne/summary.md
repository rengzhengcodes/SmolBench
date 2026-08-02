# Lagrange.eval_basis_of_ne   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨j, ⟨mem_erase.mpr ⟨hij.symm, hj⟩, eval_basisDivisor_right⟩⟩
```

**True premises at k:** `Lagrange.eval_basisDivisor_right`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.3s, in=361, out=1531)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
· simpa [Finset.mem_erase, hij, hj]
· simpa [basisDivisor]
```

**lean_error:** tail step 2/3 ('· simpa [Finset.mem_erase, hij, hj]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 55.7s, verify 0.2s, in=308, out=6962)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨j, _ , _⟩
· simp only [Finset.mem_erase, Finset.mem_singleton]
  exact ⟨hj, hij.symm⟩
· rw [Polynomial.eval_basisDivisor]
  <;> simp
```

**lean_error:** tail step 2/5 ('· simp only [Finset.mem_erase, Finset.mem_singleton]'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.3s, in=298, out=883)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use j
constructor
· exact Finset.mem_erase.mpr ⟨hij, hj⟩
· rw [eval_basisDivisor_self]
```

**lean_error:** tail step 3/4 ('· exact Finset.mem_erase.mpr ⟨hij, hj⟩'): application type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.5s, verify 0.4s, in=585, out=1250)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
· simpa [Finset.mem_erase, hij.symm, hj]
· simp
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.1s, in=554, out=1522)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨j, Finset.mem_erase.mp ⟨hj, hij⟩, _⟩
<;> apply eval_basisDivisor_right
```

**lean_error:** tail step 1/2 ("refine' ⟨j, Finset.mem_erase.mp ⟨hj, hij⟩, _⟩"): invalid constructor ⟨...⟩, expected type must be an inductive type 

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.3s, in=527, out=458)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
use j
constructor
· exact Finset.mem_erase.mpr ⟨hj, hij⟩
· simp [Lagrange.eval_basisDivisor_right]
```

**lean_error:** tail step 3/4 ('· exact Finset.mem_erase.mpr ⟨hj, hij⟩'): application type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.2s, in=743, out=1163)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
·
  have hji : j ≠ i := by
    intro h
    exact hij (h.symm)
  exact (Finset.mem_erase).2 ⟨hji, hj⟩
·
  simpa using (Lagrange.eval_basisDivisor_right (x := v i) (y := v j))
```

**lean_error:** tail step 2/8 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 16.0s, verify 0.2s, in=714, out=1818)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine' ⟨j, _ , _⟩
· -- Prove j ∈ Finset.erase s i
  simp [Finset.mem_erase, hj]
  <;> tauto
· -- Prove eval (v j) (basisDivisor (v i) (v j)) = 0
  apply eval_basisDivisor_right
```

**lean_error:** tail step 2/6 ('· -- Prove j ∈ Finset.erase s i'): <stdin>:1:31: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.3s, in=688, out=501)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use j
constructor
· exact Finset.mem_erase.mpr ⟨hj, hij.symm⟩
· simp [Lagrange.eval_basisDivisor_right]
```

**lean_error:** tail step 3/4 ('· exact Finset.mem_erase.mpr ⟨hj, hij.symm⟩'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.2s, in=751, out=1076)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
·
  have hji : j ≠ i := (ne_comm).mp hij
  exact Finset.mem_erase.mpr ⟨hji, hj⟩
·
  simpa using (Lagrange.eval_basisDivisor_right (x:=v i) (y:=v j))
```

**lean_error:** tail step 2/6 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 8.1s, verify 0.3s, in=766, out=911)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨j, _⟩
constructor
· simp only [Finset.mem_erase]
  exact ⟨hj, hij⟩
· apply Lagrange.eval_basisDivisor_right
```

**lean_error:** tail step 3/5 ('· simp only [Finset.mem_erase]'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.3s, in=708, out=621)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
use j
constructor
· exact Finset.mem_erase.mpr ⟨hij, hj⟩
· simp [Lagrange.eval_basisDivisor_right]
```

**lean_error:** tail step 3/4 ('· exact Finset.mem_erase.mpr ⟨hij, hj⟩'): application type mismatch
