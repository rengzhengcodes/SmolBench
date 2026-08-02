# SupIrred.ne_bot   (k=1, 2 tactics total)

file: `Mathlib/Order/Irreducible.lean`  

**Ground-truth tail (from k):**
```lean
exact not_supIrred_bot ha
```

**True premises at k:** `not_supIrred_bot`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=295, out=456)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases ha with ⟨hne, _⟩
exact hne rfl
```

**lean_error:** tail step 2/2 ('exact hne rfl'): application type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 242.6s, verify 0.1s, in=240, out=32232)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (∅ : Finset α).sup = ⊥ := by
  have h₂ : ∀ a : α, (∅ : Finset α).sup ≤ a := by
    intro a
    have h₃ : (∅ : Finset α) ⊆ ({a} : Finset α) := by
      intro x hx
      simp only [Finset.mem_singleton, Finset.mem_empty] at hx
      exact Set.not_mem_empty x hx
    have h₄ : (∅ : Finset α).sup ≤ ({a} : Finset α).sup := Finset.sup_le_sup h₃
    have h₅ : ({a} : Finset α).sup = a := by
      simp [Finset.sup_singleton]
    rw [h₅] at h₄
    exact h₄
  have h₃ : (∅ : Finset α).sup = ⊥ := by
    apply le_antisymm
    · -- (∅ : Finset α).sup ≤ ⊥
      have h₄ : (∅ : Finset α).sup ≤ ⊥ := h₂ ⊥
      exact h₄
    · -- ⊥ ≤ (∅ : Finset α).sup
      exact bot_le
  exact h₃
have h₂ : (∅ : Set α).sup = (∅ : Finset α).sup := by
  apply Finset.sup_eq_sup
have h₃ : (∅ : Set α).sup = ⊥ := by
  rw [h₂]
  exact h₁
have h₄ : ⊥ ∈ (∅ : Set α) := ha h₃
have h₅ : False := by
  have h₆ : ⊥ ∉ (∅ : Set α) := by simp
  exact h₆ h₄
exact h₅
```

**lean_error:** tail step 1/30 ('have h₁ : (∅ : Finset α).sup = ⊥ := by'): <stdin>:1:38: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.2s, in=237, out=672)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases ha
<;> simp_all
```

**lean_error:** tail step 2/2 ('<;> simp_all'): <stdin>:1:0: expected tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=473, out=397)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 3.0s, verify 0.1s, in=432, out=329)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.2s, verify 0.1s, in=418, out=201)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=596, out=188)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (not_supIrred_bot ha)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=553, out=261)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.3s, verify 0.1s, in=539, out=211)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=605, out=448)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=597, out=203)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.8s, verify 0.1s, in=562, out=274)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_supIrred_bot ha
```
