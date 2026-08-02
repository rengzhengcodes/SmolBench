# LinearMap.trace_eq_contract_apply   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Trace.lean`  

**Ground-truth tail (from k):**
```lean
rw [← comp_apply, trace_eq_contract]
```

**True premises at k:** `LinearMap.comp_apply`, `LinearMap.trace_eq_contract`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 1.1s, in=466, out=1646)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine TensorProduct.induction_on x ?hz ?ht ?ha
  · simp
  · intro φ m
    simp
  · intro x y hx hy
    simpa [map_add, hx, hy]
```

**lean_error:** tail step 3/6 ('· intro φ m'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 182.7s, verify 0.1s, in=428, out=24435)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hFD : FiniteDimensional R M := ⟨hFin⟩
obtain ⟨B, hB⟩ := FiniteDimensional.exists_basis_finite hFD
have hιFintype : Fintype ι := Fintype.ofFinite hB
have h_main : ∀ (f : Module.Dual R M) (v : M), (trace R M) ((dualTensorHom R M M) (f ⊗ v)) = (contractLeft R M) (f ⊗ v) := by
  intro f v
  have h₁ : (trace R M) ((dualTensorHom R M M) (f ⊗ v)) = ∑ i : ι, (B.dual i) ((dualTensorHom R M M) (f ⊗ v) (B i)) := by
    have h₂ : trace R M ((dualTensorHom R M M) (f ⊗ v)) = ∑ i : ι, B.dual i ((dualTensorHom R M M) (f ⊗ v) (B i)) := by
      rw [trace_eq_sum_dual]
      <;>
      (try infer_instance) <;>
      (try exact hιFintype) <;>
      (try exact B)
    exact h₂
  rw [h₁]
  have h₂ : ∀ (i : ι), (dualTensorHom R M M) (f ⊗ v) (B i) = f (B i) • v := by
    intro i
    have h₃ : (dualTensorHom R M M) (f ⊗ v) (B i) = f (B i) • v := by
      have h₄ : (dualTensorHom R M M) (f ⊗ v) (B i) = f (B i) • v := by
        rw [dualTensorHom_apply]
        <;>
        (try simp_all) <;>
        (try aesop)
      exact h₄
    exact h₃
  calc
    (∑ i : ι, (B.dual i) ((dualTensorHom R M M) (f ⊗ v) (B i))) = ∑ i : ι, (B.dual i) (f (B i) • v) := by
      apply Finset.sum_congr rfl
      intro i _
      rw [h₂ i]
    _ = ∑ i : ι, f (B i) * (B.dual i v) := by
      apply Finset.sum_congr rfl
      intro i _
      have h₃ : (B.dual i) (f (B i) • v) = f (B i) * (B.dual i v) := by
        rw [B.dual i.map_smul]
        <;> simp [smul_smul]
        <;>
        (try ring_nf)
        <;>
        (try simp_all [Module.Dual.smul_apply])
        <;>
        (try aesop)
      rw [h₃]
    _ = ∑ i : ι, (B.dual i v) * f (B i) := by
      apply Finset.sum_congr rfl
      intro i _
      ring
    _ = f v := by
      have h₃ : v = ∑ i : ι, (B.dual i v) • B i := by
        apply B.sum_dual
      rw [h₃]
      calc
        f (∑ i : ι, (B.dual i v) • B i) = ∑ i : ι, f ((B.dual i v) • B i) := by
          rw [f.map_sum]
          <;>
          simp [Finset.sum_smul]
          <;>
          (try simp_all [smul_smul])
          <;>
          (try ring_nf)
          <;>
          (try aesop)
        _ = ∑ i : ι, (B.dual i v) * f (B i) := by
          apply Finset.sum_congr rfl
          intro i _
          have h₄ : f ((B.dual i v) • B i) = (B.dual i v) * f (B i) := by
            rw [f.map_smul]
            <;> simp [smul_smul]
            <;>
            (try ring_nf)
            <;>
            (try simp_all [Module.Dual.smul_apply])
            <;>
            (try aesop)
          rw [h₄]
          <;>
          (try ring_nf)
have h₂ : (trace R M) ((dualTensorHom R M M) x) = (contractLeft R M) x := by
  have h₃ : ((trace R M).comp (dualTensorHom R M M)) = (contractLeft R M : (Module.Dual R M ⊗[R] M) →ₗ[R] R) := by
    apply TensorProduct.ext
    intro f v
    have h₄ : ((trace R M).comp (dualTensorHom R M M)) (f ⊗ v) = (trace R M) ((dualTensorHom R M M) (f ⊗ v)) := by
      simp [LinearMap.comp_apply]
    rw [h₄]
    have h₅ : (contractLeft R M : (Module.Dual R M ⊗[R] M) →ₗ[R] R) (f ⊗ v) = (contractLeft R M) (f ⊗ v) := by
      simp
    rw [h₅]
    exact h_main f v
  calc
    (trace R M) ((dualTensorHom R M M) x) = ((trace R M).comp (dualTensorHom R M M)) x := by
      simp [LinearMap.comp_apply]
    _ = (contractLeft R M : (Module.Dual R M ⊗[R] M) →ₗ[R] R) x := by rw [h₃]
    _ = (contractLeft R M) x := by simp
exact h₂
```

**lean_error:** tail step 1/93 ('have hFD : FiniteDimensional R M := ⟨hFin⟩'): failed to synthesize instance

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.2s, in=412, out=635)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [trace_dualTensorHom_eq_contractLeft]
```

**lean_error:** tail step 1/1 ('rw [trace_dualTensorHom_eq_contractLeft]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=814, out=636)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [LinearMap.comp_apply] using
  congrArg (fun f : Module.Dual R M ⊗[R] M →ₗ[R] R => f x)
    (LinearMap.trace_eq_contract (R:=R) (M:=M))
```

**lean_error:** tail step 1/3 ('simpa [LinearMap.comp_apply] using'): <stdin>:1:34: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=791, out=725)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  (trace R M) ((dualTensorHom R M M) x) = (LinearMap.trace R M ∘ₗ dualTensorHom R M M) x := by
    rw [LinearMap.comp_apply]
  _ = (contractLeft R M) x := by
    rw [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=762, out=463)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.trace_eq_contract, LinearMap.comp_apply]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.trace_eq_contract, LinearMap.comp_apply]'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=1924, out=1032)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [LinearMap.comp_apply] using
  congrArg (fun f : (Module.Dual R M ⊗[R] M) →ₗ[R] R => f x)
    (LinearMap.trace_eq_contract (R:=R) (M:=M))
```

**lean_error:** tail step 1/3 ('simpa [LinearMap.comp_apply] using'): <stdin>:1:34: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 12.9s, verify 0.2s, in=1955, out=1715)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.comp_apply]
rw [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.comp_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.9s, verify 0.1s, in=1884, out=560)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply, LinearMap.trace_eq_contract]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=1822, out=981)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [LinearMap.comp_apply] using
  congrArg (fun f : (Module.Dual R M ⊗[R] M) →ₗ[R] R => f x)
    (LinearMap.trace_eq_contract (R:=R) (M:=M))
```

**lean_error:** tail step 1/3 ('simpa [LinearMap.comp_apply] using'): <stdin>:1:34: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.1s, in=2102, out=1198)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  (trace R M) ((dualTensorHom R M M) x) = (LinearMap.trace R M ∘ₗ dualTensorHom R M M) x := by
    simp [LinearMap.comp_apply]
  _ = (contractLeft R M) x := by
    rw [LinearMap.trace_eq_contract]
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.6s, verify 0.1s, in=1882, out=433)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.comp_apply, LinearMap.trace_eq_contract]
```
