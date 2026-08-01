# IsPerfectClosure.equiv_symm_apply   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [equiv_symm, equiv_apply j i p _ _ _ h]
```

**True premises at k:** `IsPerfectClosure.equiv_symm`, `IsPerfectClosure.equiv_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 23.7s, verify 0.2s, in=527, out=2966)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [h]
```

**lean_error:** tail step 1/1 ('simpa [h]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 271.6s, verify 0.8s, in=487, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (RingEquiv.symm (equiv i j p)) (j y) = i y := by sorry
have h₂ : (RingEquiv.symm (equiv i j p)) (x ^ (p^n)) = i y := by sorry
have h₃ : ((RingEquiv.symm (equiv i j p)) x) ^ (p^n) = i y := by sorry
have h₄ : (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y) = (RingEquiv.symm (equiv i j p)) x := by sorry
exact h₄
```

**lean_error:** tail step 5/5 ('exact h₄'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.2s, in=470, out=612)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← h]
simp [RingEquiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('rw [← h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.1s, in=906, out=1693)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [equiv_symm] using
  (equiv_apply (i:=j) (j:=i) (x:=x) (n:=n) (y:=y) (h:=h))
```

**lean_error:** tail step 1/2 ('simpa [equiv_symm] using'): <stdin>:1:24: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 51.6s, verify 0.2s, in=884, out=5374)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsPerfectClosure.equiv_symm]
exact IsPerfectClosure.equiv_apply j i p x n y h
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 15.3s, verify 0.4s, in=849, out=956)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsPerfectClosure.equiv_symm]
apply IsPerfectClosure.equiv_apply
exact h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=1644, out=1449)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (equiv_apply (i:=j) (j:=i) (x:=x) (n:=n) (y:=y) (h:=h))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 171.5s, verify 0.2s, in=1654, out=19043)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsPerfectClosure.equiv_symm]
apply IsPerfectClosure.equiv_apply with x n y h
```

**lean_error:** tail step 2/2 ('apply IsPerfectClosure.equiv_apply with x n y h'): <stdin>:1:35: expected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 14.2s, verify 0.4s, in=1595, out=903)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsPerfectClosure.equiv_symm]
apply IsPerfectClosure.equiv_apply
exact h
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=1582, out=1498)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [IsPerfectClosure.equiv_symm] using
    (IsPerfectClosure.equiv_apply (i:=j) (j:=i) (p:=p) (x:=x) (n:=n) (y:=y) (h:=h))
```

**lean_error:** tail step 1/2 ('simpa [IsPerfectClosure.equiv_symm] using'): <stdin>:1:41: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 107.2s, verify 0.1s, in=1762, out=11382)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem IsPerfectClosure.equiv_symm_apply {K L M N : Type*} [CommRing K] [CommRing L] [CommRing M] [CommRing N]
    {i : K →+* L} {j : K →+* M} {k : K →+* N} {f : L →+* M} {g : L →+* N} {p : ℕ}
    [ExpChar K p] [ExpChar L p] [ExpChar M p] [ExpChar N p]
    [PerfectRing L p] [IsPerfectClosure i p] [PerfectRing M p] [IsPerfectClosure j p]
    (x : M) (n : ℕ) (y : K) (h : j y = x ^ p ^ n) :
    (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y) := by
  set z : L := (iterateFrobeniusEquiv L p n).symm (i y) with hz_def
  have h_iz : (iterateFrobeniusEquiv L p n) z = i y := by
    rw [hz_def]
    <;> simp [Equiv.apply_symm_apply]
  
  have h_i_y_eq_z_pow : i y = z ^ p ^ n := by
    have h1 : (iterateFrobeniusEquiv L p n) z = z ^ p ^ n := by
      rw [iterateFrobeniusEquiv_apply]
      <;>
      (try infer_instance) <;>
      (try assumption) <;>
      (try exact PerfectRing.charP _) <;>
      (try exact inferInstance)
    have h2 : (iterateFrobeniusEquiv L p n) z = i y := h_iz
    rw [h2] at h1
    exact h1
  
  have h_equiv_apply : equiv i j p z = (iterateFrobeniusEquiv M p n).symm (j y) := by
    have h1 : i y = z ^ p ^ n := h_i_y_eq_z_pow
    have h2 : equiv i j p z = (iterateFrobeniusEquiv M p n).symm (j y) := by
      apply IsPerfectClosure.equiv_apply
      <;> assumption
      <;> (try assumption)
      <;> (try exact h1)
      <;> (try assumption)
    exact h2
  
  have h_symm_jy_eq_x : (iterateFrobeniusEquiv M p n).symm (j y) = x := by
    have h1 : (iterateFrobeniusEquiv M p n) x = x ^ p ^ n := by
      rw [iterateFrobeniusEquiv_apply]
      <;>
      (try infer_instance) <;>
      (try assumption) <;>
      (try exact PerfectRing.charP _) <;>
      (try exact inferInstance)
    have h2 : j y = x ^ p ^ n := h
    have h3 : (iterateFrobeniusEquiv M p n) x = j y := by
      rw [h1]
      <;> rw [h2]
    have h4 : (iterateFrobeniusEquiv M p n).symm (j y) = x := by
      apply Equiv.symm_apply_apply
    exact h4
  
  have h_equiv_apply_x : equiv i j p z = x := by
    rw [h_equiv_apply]
    rw [h_symm_jy_eq_x]
  
  have h_symm_x_eq_z : (equiv i j p).symm x = z := by
    have h1 : equiv i j p z = x := h_equiv_apply_x
    have h2 : (equiv i j p).symm x = z := by
      apply Equiv.symm_apply_apply
      <;> exact h1
    exact h2
  
  have h_symm_eq : (RingEquiv.symm (equiv i j p)) x = (equiv j i p) x := by
    rw [show (RingEquiv.symm (equiv i j p)) = (equiv i j p).symm by rfl]
    rw [IsPerfectClosure.equiv_symm]
    <;> simp [Equiv.apply_symm]
  
  have h_main : (equiv j i p) x = z := by
    have h1 : (equiv j i p) x = (equiv i j p).symm x := by
      rw [IsPerfectClosure.equiv_symm]
      <;> simp [Equiv.apply_symm]
    rw [h1]
    rw [h_symm_x_eq_z]
  
  have h_goal : (RingEquiv.symm (equiv i j p)) x = (iterateFrobeniusEquiv L p n).symm (i y) := by
    calc
      (RingEquiv.symm (equiv i j p)) x = (equiv j i p) x := by rw [h_symm_eq]
      _ = z := by rw [h_main]
      _ = (iterateFrobeniusEquiv L p n).symm (i y) := by
        rw [hz_def]
        <;> rfl
  
  exact h_goal
```

**lean_error:** tail step 1/72 ('theorem IsPerfectClosure.equiv_symm_apply {K L M N : Type*} [CommRing K] [CommRing L] [CommRing M] [CommRing N]'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.2s, verify 0.2s, in=1598, out=706)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsPerfectClosure.equiv_symm]
rw [IsPerfectClosure.equiv_apply j i p x n y h]
```
