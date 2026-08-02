# Polynomial.roots_X_pow_char_sub_C_pow   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
rwa [pow_one, iterateFrobeniusEquiv_one] at H
```

**True premises at k:** `pow_one`, `iterateFrobeniusEquiv_one`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✘ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.3s, verify 0.2s, in=414, out=500)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.6s, verify 0.1s, in=367, out=4483)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  roots ((X ^ p - C y) ^ m) = roots ((X ^ p ^ 1 - C y) ^ m) := by norm_num
  _ = (m * p ^ 1) • {(RingEquiv.symm (iterateFrobeniusEquiv R p 1)) y} := H
  _ = (m * p) • {(RingEquiv.symm (iterateFrobeniusEquiv R p 1)) y} := by norm_num
  _ = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y} := by
    rw [show iterateFrobeniusEquiv R p 1 = frobeniusEquiv R p by
      rw [iterateFrobeniusEquiv_one]]
```

**lean_error:** tail step 1/7 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.6s, verify 0.2s, in=361, out=517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_all [pow_one]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.8s, verify 0.3s, in=787, out=874)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.4s, verify 0.2s, in=755, out=7307)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [H]
<;> simp [pow_one, iterateFrobeniusEquiv_one]
<;> rfl
```

**lean_error:** tail step 1/3 ('rw [H]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.2s, in=743, out=412)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.6s, in=1569, out=714)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 25.6s, verify 0.3s, in=1570, out=2974)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pow_one] at H
rw [iterateFrobeniusEquiv_one] at H
exact H
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.3s, in=1534, out=472)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pow_one, iterateFrobeniusEquiv_one] at H
exact H
```

**lean_error:** tail step 2/2 ('exact H'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.0s, verify 0.2s, in=1495, out=489)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 33.2s, verify 0.1s, in=1678, out=3862)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem X_pow_char_sub_C_pow_roots {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] (f : R[X]) [PerfectRing R p] (y : R) (m : ℕ) :
    roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y} := by
  have H : roots ((X ^ p ^ 1 - C y) ^ m) = (m * p ^ 1) • {(RingEquiv.symm (iterateFrobeniusEquiv R p 1)) y} := by
    apply roots_X_pow_char_pow_sub_C_pow
  
  have H_main : roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y} := by
    have H₁ : (X ^ p ^ 1 - C y : R[X]) = (X ^ p - C y : R[X]) := by
      have h₂ : p ^ 1 = p := by norm_num
      rw [show X ^ p ^ 1 = X ^ p by
        rw [h₂]
        <;> simp [pow_one]
      ]
      <;> simp [sub_eq_add_neg]
      <;> ring_nf
    have H₂ : roots ((X ^ p ^ 1 - C y : R[X]) ^ m) = roots ((X ^ p - C y : R[X]) ^ m) := by
      rw [H₁]
    rw [H₂] at H
    have h₃ : (m * p ^ 1 : ℕ) = m * p := by
      have h₄ : p ^ 1 = p := by norm_num
      rw [h₄]
      <;> ring
    have h₄ : (iterateFrobeniusEquiv R p 1 : R →+* R) = frobeniusEquiv R p := by
      apply iterateFrobeniusEquiv_one
    have h₅ : RingEquiv.symm (iterateFrobeniusEquiv R p 1) = RingEquiv.symm (frobeniusEquiv R p) := by
      rw [h₄]
    rw [h₃] at H
    rw [h₅] at H
    exact H
  
  apply H_main
```

**lean_error:** tail step 1/28 ('theorem X_pow_char_sub_C_pow_roots {R : Type u_1} [CommRing R] [IsDomain R] {p n : ℕ} [ExpChar R p] (f : R[X]) [PerfectRing R p] (y : R) (m : ℕ) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.0s, verify 0.2s, in=1529, out=455)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [pow_one, iterateFrobeniusEquiv_one] using H
```
