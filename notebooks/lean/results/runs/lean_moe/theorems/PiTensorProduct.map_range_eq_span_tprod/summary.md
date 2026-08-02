# PiTensorProduct.map_range_eq_span_tprod   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Set.mem_range, comp_apply, map_tprod, Set.mem_setOf_eq]
```

**True premises at k:** `Set.mem_range`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `Set.mem_setOf_eq`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.1s, verify 0.6s, in=699, out=1981)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · rintro ⟨m, hm⟩
    refine ⟨m, ?_⟩
    simpa [Function.comp, TensorProduct.map_tprod] using hm
  · rintro ⟨m, hm⟩
    refine ⟨m, ?_⟩
    simpa [Function.comp, TensorProduct.map_tprod] using hm
```

**lean_error:** tail step 2/7 ('· rintro ⟨m, hm⟩'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 103.9s, verify 0.1s, in=652, out=13039)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, tprod_apply, map_apply_tprod] <;> aesop
```

**lean_error:** tail step 1/1 ('simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, tprod_apply, map_apply_tprod] <;> aesop'): unknown identifier 'tprod_apply'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.8s, in=634, out=521)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply]
constructor
· intro ⟨m, hm⟩
  refine' ⟨m, _⟩
  simpa using hm
· intro ⟨m, hm⟩
  refine' ⟨m, _⟩
  simpa using hm
```

**lean_error:** tail step 3/8 ('· intro ⟨m, hm⟩'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.1s, verify 0.1s, in=1346, out=1485)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, PiTensorProduct.map_tprod]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 67.4s, verify 0.2s, in=1318, out=8135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range]
<;> simp [Function.comp_apply, PiTensorProduct.map_tprod]
<;> rw [Set.mem_setOf_eq]
<;> tauto
```

**lean_error:** tail step 2/4 ('<;> simp [Function.comp_apply, PiTensorProduct.map_tprod]'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=1286, out=449)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, Set.mem_setOf_eq, PiTensorProduct.map_tprod]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.8s, verify 0.1s, in=1566, out=1894)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Set.mem_range, Set.mem_setOf_eq, PiTensorProduct.map_tprod]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 72.5s, verify 0.6s, in=1533, out=8858)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  rcases h with ⟨y, hy, hxy⟩
  rcases hy with ⟨z, hz⟩
  have h₁ : (⇑(map f)) (⇑(tprod R) z) = x := by simpa [hz] using hxy
  have h₂ : (⇑(map f)) (⇑(tprod R) z) = tprod R (fun i ↦ f i (z i)) := by
    rw [PiTensorProduct.map_tprod]
  rw [h₂] at h₁
  exact ⟨z, h₁⟩
· intro h
  rcases h with ⟨m, hm⟩
  have h₁ : (⇑(tprod R) m) ∈ Set.range (⇑(tprod R)) := Set.mem_range_self m
  have h₂ : (⇑(map f)) (⇑(tprod R) m) = x := by
    calc
      (⇑(map f)) (⇑(tprod R) m) = tprod R (fun i ↦ f i (m i)) := by rw [PiTensorProduct.map_tprod]
      _ = (⨂ₜ[R] (i : ι), (f i) (m i)) := rfl
      _ = x := hm
  exact ⟨⇑(tprod R) m, h₁, h₂⟩
```

**lean_error:** tail step 2/18 ('· intro h'): unsolved goals

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=1507, out=571)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.5s, verify 0.2s, in=1565, out=873)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 76.4s, verify 0.1s, in=1597, out=9408)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_lhs : x ∈ Set.range (⇑(map f) ∘ ⇑(tprod R)) ↔ (∃ (y : Π i, s i), ⇑(tprod R) (fun i ↦ f i (y i)) = x) := by
  constructor
  · -- Prove the forward direction: if x is in the range, then there exists y such that ...
    intro h
    rcases h with ⟨y, hy⟩
    have h₁ : (⇑(map f) ∘ ⇑(tprod R)) y = x := hy
    have h₂ : (⇑(map f) ∘ ⇑(tprod R)) y = ⇑(map f) (⇑(tprod R) y) := by
      simp [Function.comp_apply]
    rw [h₂] at h₁
    have h₃ : ⇑(map f) (⇑(tprod R) y) = x := h₁
    have h₄ : ⇑(map f) (⇑(tprod R) y) = ⇑(tprod R) (fun i ↦ f i (y i)) := by
      rw [PiTensorProduct.map_tprod]
    rw [h₄] at h₃
    exact ⟨y, h₃⟩
  · -- Prove the backward direction: if there exists y such that ..., then x is in the range
    rintro ⟨y, hy⟩
    have h₁ : ⇑(tprod R) (fun i ↦ f i (y i)) = x := hy
    have h₂ : ⇑(map f) (⇑(tprod R) y) = ⇑(tprod R) (fun i ↦ f i (y i)) := by
      rw [PiTensorProduct.map_tprod]
    have h₃ : (⇑(map f) ∘ ⇑(tprod R)) y = ⇑(map f) (⇑(tprod R) y) := by
      simp [Function.comp_apply]
    have h₄ : (⇑(map f) ∘ ⇑(tprod R)) y = x := by
      calc
        (⇑(map f) ∘ ⇑(tprod R)) y = ⇑(map f) (⇑(tprod R) y) := by rw [h₃]
        _ = ⇑(tprod R) (fun i ↦ f i (y i)) := by rw [h₂]
        _ = x := by rw [h₁]
    exact ⟨y, h₄⟩
  
have h_rhs : x ∈ {t_1 | ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = t_1} ↔ (∃ (m : Π i, s i), ⇑(tprod R) (fun i ↦ f i (m i)) = x) := by
  constructor
  · -- Prove the forward direction: if x is in the set, then there exists m such that ...
    intro h
    simp only [Set.mem_setOf_eq] at h
    -- Now h: ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = x
    obtain ⟨m, hm⟩ := h
    -- We need to show: ∃ m, ⇑(tprod R) (fun i ↦ f i (m i)) = x
    -- Note that (⨂ₜ[R] (i : ι), (f i) (m i)) is exactly ⇑(tprod R) (fun i ↦ f i (m i))
    have h₁ : (⨂ₜ[R] (i : ι), (f i) (m i)) = ⇑(tprod R) (fun i ↦ f i (m i)) := by
      rfl
    rw [h₁] at hm
    exact ⟨m, hm⟩
  · -- Prove the backward direction: if there exists m such that ..., then x is in the set
    rintro ⟨m, hm⟩
    have h₁ : ⇑(tprod R) (fun i ↦ f i (m i)) = x := hm
    have h₂ : (⨂ₜ[R] (i : ι), (f i) (m i)) = ⇑(tprod R) (fun i ↦ f i (m i)) := by
      rfl
    have h₃ : (⨂ₜ[R] (i : ι), (f i) (m i)) = x := by
      linarith
    -- Now we need to show: x ∈ {t_1 | ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = t_1}
    -- Which is equivalent to: ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = x
    refine' ⟨m, _⟩
    linarith
  
have h_final : (∃ (y : Π i, s i), ⇑(tprod R) (fun i ↦ f i (y i)) = x) ↔ (∃ (m : Π i, s i), ⇑(tprod R) (fun i ↦ f i (m i)) = x) := by
  constructor
  · -- Prove the forward direction: if there exists y, then there exists m (just rename y to m)
    intro h
    obtain ⟨y, hy⟩ := h
    refine' ⟨y, _⟩
    exact hy
  · -- Prove the backward direction: if there exists m, then there exists y (just rename m to y)
    intro h
    obtain ⟨m, hm⟩ := h
    refine' ⟨m, _⟩
    exact hm
  
-- Now we can combine all the pieces to get the final result
have h_main : x ∈ Set.range (⇑(map f) ∘ ⇑(tprod R)) ↔ x ∈ {t_1 | ∃ m, (⨂ₜ[R] (i : ι), (f i) (m i)) = t_1} := by
  rw [h_lhs]
  rw [h_rhs]
  -- Now we need to show that (∃ y, ⇑(tprod R) (fun i ↦ f i (y i)) = x) ↔ (∃ m, ⇑(tprod R) (fun i ↦ f i (m i)) = x)
  -- This is exactly h_final
  exact h_final
  
exact h_main
```

**lean_error:** tail step 1/71 ('have h_lhs : x ∈ Set.range (⇑(map f) ∘ ⇑(tprod R)) ↔ (∃ (y : Π i, s i), ⇑(tprod R) (fun i ↦ f i (y i)) = x) := by'): <stdin>:1:113: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.1s, in=1527, out=400)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```
