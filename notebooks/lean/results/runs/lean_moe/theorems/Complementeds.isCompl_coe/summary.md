# Complementeds.isCompl_coe   (k=0, 1 tactics total)

file: `Mathlib/Order/Disjoint.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**True premises at k:** `isCompl_iff`, `Complementeds.disjoint_coe`, `Complementeds.codisjoint_coe`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=289, out=754)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.1s, in=239, out=1594)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.3s, verify 0.1s, in=236, out=748)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsCompl]
```

**lean_error:** tail step 1/1 ('simp [IsCompl]'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=839, out=787)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [isCompl_iff] using
  (and_congr (Complementeds.disjoint_coe (a:=a) (b:=b))
    (Complementeds.codisjoint_coe (a:=a) (b:=b)))
```

**lean_error:** tail step 1/3 ('simpa [isCompl_iff] using'): <stdin>:1:25: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 54.9s, verify 0.2s, in=789, out=6266)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h
    rw [isCompl_iff] at h
    have h₁ : Disjoint (a : α) (b : α) := disjoint_coe.mp h.1
    have h₂ : Codisjoint (a : α) (b : α) := codisjoint_coe.mp h.2
    exact ⟨h₁, h₂⟩
  · intro h
    rw [isCompl_iff] at h
    have h₁ : Disjoint (a : α) (b : α) := disjoint_coe.mpr h.1
    have h₂ : Codisjoint (a : α) (b : α) := codisjoint_coe.mpr h.2
    exact ⟨h₁, h₂⟩
```

**lean_error:** tail step 2/11 ('· intro h'): unsolved goals

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.9s, verify 0.2s, in=777, out=444)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp [disjoint_coe, codisjoint_coe]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.9s, verify 0.1s, in=1617, out=1058)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [isCompl_iff]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 25.0s, verify 0.2s, in=1558, out=2789)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
    have h₁ : Disjoint (↑a) (↑b) := h.disjoint
    have h₂ : Codisjoint (↑a) (↑b) := h.codisjoint
    have h₃ : Disjoint a b := by
        rw [disjoint_coe] at *
        exact h₁
    have h₄ : Codisjoint a b := by
        rw [codisjoint_coe] at *
        exact h₂
    exact ⟨h₃, h₄⟩
· intro h
    have h₁ : Disjoint a b := h.disjoint
    have h₂ : Codisjoint a b := h.codisjoint
    have h₃ : Disjoint (↑a) (↑b) := by
        rw [disjoint_coe]
        exact h₁
    have h₄ : Codisjoint (↑a) (↑b) := by
        rw [codisjoint_coe]
        exact h₂
    exact ⟨h₃, h₄⟩
```

**lean_error:** tail step 2/21 ('· intro h'): unsolved goals

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.2s, in=1546, out=527)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp [disjoint_coe, codisjoint_coe]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.4s, verify 0.1s, in=1533, out=1128)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 64.7s, verify 0.2s, in=1693, out=7634)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
· intro h
  have h₁ : Disjoint (↑a) (↑b) ∧ Codisjoint (↑a) (↑b) := by
    rw [isCompl_iff] at h
    exact h
  have h₂ : Disjoint a b := by
    rw [Complementeds.disjoint_coe]
    exact h₁.1
  have h₃ : Codisjoint a b := by
    rw [Complementeds.codisjoint_coe]
    exact h₁.2
  have h₄ : IsCompl a b := by
    rw [isCompl_iff]
    exact ⟨h₂, h₃⟩
  exact h₄
· intro h
  have h₁ : Disjoint a b ∧ Codisjoint a b := by
    rw [isCompl_iff] at h
    exact h
  have h₂ : Disjoint (↑a) (↑b) := by
    rw [← Complementeds.disjoint_coe]
    exact h₁.1
  have h₃ : Codisjoint (↑a) (↑b) := by
    rw [← Complementeds.codisjoint_coe]
    exact h₁.2
  have h₄ : IsCompl ↑a ↑b := by
    rw [isCompl_iff]
    exact ⟨h₂, h₃⟩
  exact h₄
```

**lean_error:** tail step 2/29 ('· intro h'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.0s, verify 0.2s, in=1547, out=458)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp [disjoint_coe, codisjoint_coe]
```
