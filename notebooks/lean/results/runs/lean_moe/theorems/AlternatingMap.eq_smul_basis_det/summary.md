# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 9.5s, verify 0.4s, in=450, out=1773)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, smul_comm]
```

**final state (truncated):**
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 194.4s, verify 0.1s, in=410, out=24628)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : f (⇑e ∘ ⇑σ) = (Equiv.sign σ : R) • f ⇑e := by
  have h₁₁ : (⇑e ∘ ⇑σ : ι → M) = (⇑e : ι → M) ∘ ⇑σ := by
    ext i
    <;> simp [Function.comp_apply]
  rw [h₁₁]
  apply AlternatingMultilinearMap.map_perm
have h₂ : (Basis.det e : M [⋀^ι]→ₗ[R] R) (⇑e ∘ ⇑σ) = (Equiv.sign σ : R) • (Basis.det e : M [⋀^ι]→ₗ[R] R) ⇑e := by
  have h₂₁ : (⇑e ∘ ⇑σ : ι → M) = (⇑e : ι → M) ∘ ⇑σ := by
    ext i
    <;> simp [Function.comp_apply]
  rw [h₂₁]
  apply AlternatingMultilinearMap.map_perm
have h₃ : (Basis.det e : M [⋀^ι]→ₗ[R] R) ⇑e = (1 : R) := by
  apply Basis.det_apply
have h₄ : (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ) = (f ⇑e : R) * ((Basis.det e : M [⋀^ι]→ₗ[R] R) (⇑e ∘ ⇑σ)) := by
  simp [Pi.smul_apply, smul_eq_mul]
  <;> ring_nf
  <;> simp_all
have h₅ : (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ) = (Equiv.sign σ : R) • f ⇑e := by
  calc
    (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ) = (f ⇑e : R) * ((Basis.det e : M [⋀^ι]→ₗ[R] R) (⇑e ∘ ⇑σ)) := h₄
    _ = (f ⇑e : R) * ((Equiv.sign σ : R) • (Basis.det e : M [⋀^ι]→ₗ[R] R) ⇑e) := by rw [h₂]
    _ = (f ⇑e : R) * ((Equiv.sign σ : R) * (1 : R)) := by rw [h₃]
    _ = (Equiv.sign σ : R) * (f ⇑e : R) := by ring
    _ = (Equiv.sign σ : R) • f ⇑e := by simp [smul_eq_mul]
have h₆ : f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ) := by
  rw [h₁]
  <;> rw [h₅]
exact h₆
```

**lean_error:** tail step 1/29 ('have h₁ : f (⇑e ∘ ⇑σ) = (Equiv.sign σ : R) • f ⇑e := by'): <stdin>:1:55: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=395, out=516)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Basis.det_smul]
<;> simp [Function.comp]
```

**lean_error:** tail step 1/2 ('rw [Basis.det_smul]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.2s, in=954, out=3305)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hdet := (AlternatingMap.map_perm (g:=e.det) (v:=e) σ)
  simpa [AlternatingMap.smul_apply, Basis.det_self, Units.smul_def, mul_comm, hdet] using
    (AlternatingMap.map_perm (g:=f) (v:=e) σ)
```

**lean_error:** tail step 2/3 ('simpa [AlternatingMap.smul_apply, Basis.det_self, Units.smul_def, mul_comm, hdet] using'): <stdin>:1:87: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 213.4s, verify 0.1s, in=926, out=26811)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : f (e ∘ σ) = Equiv.Perm.sign σ • f e := by
  apply AlternatingMap.map_perm
have h₂ : det e = 1 := Basis.det e
-- We will now show that the right-hand side simplifies to the same expression.
-- Note that (f e • e.det) is a scalar, and we interpret (e ∘ σ) as 1 in this context.
-- However, to match the structure, we use the properties of the determinant and alternating maps.
-- We know that f (e ∘ σ) = Equiv.Perm.sign σ • f e.
-- We also know that det e = 1.
-- The right-hand side (f e • e.det) (e ∘ σ) is interpreted as (f e • e.det) * 1 = f e * e.det.
-- Since det e = 1, this becomes f e * 1 = f e.
-- But we need to relate this to Equiv.Perm.sign σ • f e.
-- However, in the context of the problem, the correct interpretation likely involves the determinant of the permuted basis.
-- Given the constraints, we use the given premises to adjust the proof.
-- We use the fact that the sign of the permutation can be incorporated via the determinant.
-- Specifically, we use that det (e ∘ σ) = Equiv.Perm.sign σ • det e and det e = 1.
-- Thus, (f e • e.det) * det (e ∘ σ) = (f e * e.det) * (Equiv.Perm.sign σ * det e) = f e * 1 * Equiv.Perm.sign σ = Equiv.Perm.sign σ * f e.
-- Since multiplication in R is commutative, this equals Equiv.Perm.sign σ • f e.
-- Therefore, f (e ∘ σ) = (f e • e.det) * det (e ∘ σ).
-- Assuming the right-hand side in the goal is a shorthand for this expression, we conclude.
-- For the purpose of this proof, we directly use the given premises to simplify the goal to rfl.
-- We do this by noting that both sides are equal to Equiv.Perm.sign σ • f e after applying the premises.
rfl
```

**lean_error:** tail step 1/22 ('have h₁ : f (e ∘ σ) = Equiv.Perm.sign σ • f e := by'): <stdin>:1:51: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.0s, verify 0.2s, in=897, out=1224)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm]
simp [Basis.det_comp_perm, smul_smul]
```

**lean_error:** tail step 2/2 ('simp [Basis.det_comp_perm, smul_smul]'): unknown constant 'Basis.det_comp_perm'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.3s, verify 0.7s, in=2123, out=2242)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, Basis.det_self, mul_comm, mul_left_comm, mul_assoc]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 106.1s, verify 0.1s, in=2128, out=13495)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : f (e ∘ σ) = Equiv.Perm.sign σ • f e := by
  apply AlternatingMap.map_perm
have h2 : e.det (e ∘ σ) = Equiv.Perm.sign σ • e.det e := by
  apply AlternatingMap.map_perm
have h3 : e.det e = 1 := by
  apply Basis.det_self
have h4 : e.det (e ∘ σ) = (Equiv.Perm.sign σ : R) := by
  calc
    e.det (e ∘ σ) = Equiv.Perm.sign σ • e.det e := h2
    _ = Equiv.Perm.sign σ • 1 := by rw [h3]
    _ = (Equiv.Perm.sign σ : R) := by
      simp [zsmul_eq_mul]
      <;> simp [one_mul]
have h5 : f (e ∘ σ) = (f e • e.det) (e ∘ σ) := by
  calc
    f (e ∘ σ) = Equiv.Perm.sign σ • f e := h1
    _ = (Equiv.Perm.sign σ : R) * f e := by simp [zsmul_eq_mul]
    _ = f e * (Equiv.Perm.sign σ : R) := by rw [mul_comm]
    _ = f e * e.det (e ∘ σ) := by rw [h4]
    _ = (f e • e.det) (e ∘ σ) := by rfl
exact h5
```

**lean_error:** tail step 1/21 ('have h1 : f (e ∘ σ) = Equiv.Perm.sign σ • f e := by'): <stdin>:1:51: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.6s, verify 0.3s, in=2074, out=921)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm]
rw [Basis.det_self]
simp
```

**lean_error:** tail step 2/3 ('rw [Basis.det_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.0s, verify 0.5s, in=2005, out=2124)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, Basis.det_self, smul_smul, mul_comm, mul_left_comm, mul_assoc]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.5s, verify 0.1s, in=2300, out=17407)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' Basis.ext_alternating e fun i h => _
have h₁ : f (e ∘ σ) = Equiv.Perm.sign σ • f e := by
  apply AlternatingMap.map_perm
have h₂ : e.det (e ∘ σ) = Equiv.Perm.sign σ • e.det e := by
  apply AlternatingMap.map_perm
have h₃ : e.det e = 1 := by
  apply Basis.det_self
have h₄ : (f e • e.det) (e ∘ σ) = (f e) * (e.det (e ∘ σ)) := by
  simp [smul_eq_mul]
have h₅ : (f e • e.det) (e ∘ σ) = (f e) * (Equiv.Perm.sign σ : R) := by
  calc
    (f e • e.det) (e ∘ σ) = (f e) * (e.det (e ∘ σ)) := by rw [h₄]
    _ = (f e) * (Equiv.Perm.sign σ • e.det e) := by rw [h₂]
    _ = (f e) * (Equiv.Perm.sign σ * 1 : R) := by
      simp [h₃, smul_eq_mul]
    _ = (f e) * Equiv.Perm.sign σ := by ring
have h₆ : f (e ∘ σ) = (Equiv.Perm.sign σ : R) * f e := by
  rw [h₁]
  <;> simp [smul_eq_mul]
have h₇ : (Equiv.Perm.sign σ : R) * f e = (f e) * (Equiv.Perm.sign σ : R) := by
  ring
have h₈ : (f e • e.det) (e ∘ σ) = (f e) * (Equiv.Perm.sign σ : R) := h₅
calc
  f (e ∘ σ) = (Equiv.Perm.sign σ : R) * f e := by rw [h₆]
  _ = (f e) * (Equiv.Perm.sign σ : R) := by rw [h₇]
  _ = (f e • e.det) (e ∘ σ) := by
    rw [h₈]
    <;> simp [smul_eq_mul]
```

**lean_error:** tail step 1/28 ("refine' Basis.ext_alternating e fun i h => _"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.3s, in=2066, out=698)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlternatingMap.map_perm]
rw [smul_eq_mul, AlternatingMap.map_perm, Basis.det_self, one_smul]
simp [smul_eq_mul]
```

**lean_error:** tail step 2/3 ('rw [smul_eq_mul, AlternatingMap.map_perm, Basis.det_self, one_smul]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
