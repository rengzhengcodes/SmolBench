# wcovBy_iff_covBy_or_eq   (k=0, 1 tactics total)

file: `Mathlib/Order/Cover.lean`  

**Ground-truth tail (from k):**
```lean
rw [le_antisymm_iff, wcovBy_iff_covBy_or_le_and_le]
```

**True premises at k:** `le_antisymm_iff`, `wcovBy_iff_covBy_or_le_and_le`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=292, out=701)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 70.0s, verify 0.2s, in=237, out=8182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· -- Prove the forward direction: a ⩿ b → a ⋖ b ∨ a = b
  intro h
  by_cases h_eq : a = b
  · -- Case: a = b
    exact Or.inr h_eq
  · -- Case: a ≠ b
    have h_lt : a ⋖ b := by
      -- Since a ⩿ b and a ≠ b, we show a ⋖ b
      have h_le : a ⩿ b := h
      have h_ne : a ≠ b := h_eq
      -- We need to show a ⋖ b, which is a < b in the strict order
      have h_lt : a < b := by
        -- Use the definition of < as a ≤ b ∧ ¬ (b ≤ a)
        constructor
        · -- Prove a ≤ b
          exact h_le
        · -- Prove ¬ (b ≤ a)
          intro h_ba
          -- If b ≤ a, then by antisymmetry a = b, contradicting a ≠ b
          have h_eq' : a = b := le_antisymm h_ba h_le
          contradiction
      exact h_lt
    exact Or.inl h_lt
· -- Prove the backward direction: a ⋖ b ∨ a = b → a ⩿ b
  intro h
  cases h with
  | inl h_lt =>
    -- Case: a ⋖ b (i.e., a < b)
    have h_le : a ⩿ b := by
      -- Since a < b, we have a ≤ b by definition of <
      exact lt_iff_le_not_le.mp h_lt |>.1
    exact h_le
  | inr h_eq =>
    -- Case: a = b
    have h_le : a ⩿ b := by
      -- By reflexivity, a ≤ a, and since a = b, we have a ≤ b
      rw [h_eq]
      exact le_refl a
    exact h_le

</think>
constructor
· -- Prove the forward direction: a ⩿ b → a ⋖ b ∨ a = b
  intro h
  by_cases h_eq : a = b
  · -- Case: a = b
    exact Or.inr h_eq
  · -- Case: a ≠ b
    have h_lt : a ⋖ b := by
      -- Since a ⩿ b and a ≠ b, we show a ⋖ b
      have h_le : a ⩿ b := h
      have h_ne : a ≠ b := h_eq
      -- We need to show a ⋖ b, which is a < b in the strict order
      have h_lt : a < b := by
        -- Use the definition of < as a ≤ b ∧ ¬ (b ≤ a)
        constructor
        · -- Prove a ≤ b
          exact h_le
        · -- Prove ¬ (b ≤ a)
          intro h_ba
          -- If b ≤ a, then by antisymmetry a = b, contradicting a ≠ b
          have h_eq' : a = b := le_antisymm h_ba h_le
          contradiction
      exact h_lt
    exact Or.inl h_lt
· -- Prove the backward direction: a ⋖ b ∨ a = b → a ⩿ b
  intro h
  cases h with
  | inl h_lt =>
    -- Case: a ⋖ b (i.e., a < b)
    have h_le : a ⩿ b := by
      -- Since a < b, we have a ≤ b by definition of <
      exact lt_iff_le_not_le.mp h_lt |>.1
    exact h_le
  | inr h_eq =>
    -- Case: a = b
    have h_le : a ⩿ b := by
      -- By reflexivity, a ≤ a, and since a = b, we have a ≤ b
      rw [h_eq]
      exact le_refl a
    exact h_le
  <;>
  assumption
```

**lean_error:** tail step 2/83 ('· -- Prove the forward direction: a ⩿ b → a ⋖ b ∨ a = b'): <stdin>:1:55: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=237, out=461)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=753, out=1987)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 89.7s, verify 0.2s, in=697, out=10614)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : a ⩿ b ↔ a ⋖ b ∨ a ≤ b ∧ b ≤ a := wcovBy_iff_covBy_or_le_and_le
have h₂ : (a ⋖ b ∨ a ≤ b ∧ b ≤ a) ↔ (a ⋖ b ∨ a = b) := by
  constructor
  · intro h
    cases h with
    | inl h => exact Or.inl h
    | inr h =>
      have h₃ : a = b := by
        have h₄ : a ≤ b := h.1
        have h₅ : b ≤ a := h.2
        exact le_antisymm h₄ h₅
      exact Or.inr h₃
  · intro h
    cases h with
    | inl h => exact Or.inl h
    | inr h =>
      have h₃ : a = b := h
      have h₄ : a ≤ b := by rw [h₃]; exact le_refl _
      have h₅ : b ≤ a := by rw [h₃]; exact le_refl _
      exact Or.inr ⟨h₄, h₅⟩
rw [h₁, h₂]
```

**lean_error:** tail step 2/21 ('have h₂ : (a ⋖ b ∨ a ≤ b ∧ b ≤ a) ↔ (a ⋖ b ∨ a = b) := by'): <stdin>:1:57: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=663, out=387)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=899, out=476)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 69.4s, verify 0.1s, in=847, out=8105)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : a ⩿ b ↔ a ⋖ b ∨ a ≤ b ∧ b ≤ a := by
  apply wcovBy_iff_covBy_or_le_and_le
have h₂ : a = b ↔ a ≤ b ∧ b ≤ a := by
  apply le_antisymm_iff
have h₃ : (a ⋖ b ∨ a ≤ b ∧ b ≤ a) ↔ (a ⋖ b ∨ a = b) := by
  constructor
  · intro h
    cases h with
    | inl h =>
      exact Or.inl h
    | inr h =>
      have h₄ : a = b := by
        have h₅ : a ≤ b ∧ b ≤ a := h
        have h₆ : a = b ↔ a ≤ b ∧ b ≤ a := h₂
        have h₇ : a = b := by
          rw [h₂] at h₅
          exact h₅
        exact h₇
      exact Or.inr h₄
  · intro h
    cases h with
    | inl h =>
      exact Or.inl h
    | inr h =>
      have h₄ : a ≤ b ∧ b ≤ a := by
        have h₅ : a = b := h
        have h₆ : a = b ↔ a ≤ b ∧ b ≤ a := h₂
        have h₇ : a ≤ b ∧ b ≤ a := by
          rw [h₂] at *
          exact h₅
        exact h₇
      exact Or.inr h₄
have h₄ : a ⩿ b ↔ a ⋖ b ∨ a = b := by
  rw [h₁]
  rw [h₃]
exact h₄
```

**lean_error:** tail step 1/36 ('have h₁ : a ⩿ b ↔ a ⋖ b ∨ a ≤ b ∧ b ≤ a := by'): <stdin>:1:45: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.9s, verify 0.1s, in=809, out=455)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.7s, verify 0.1s, in=907, out=1597)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [le_antisymm_iff] using (wcovBy_iff_covBy_or_le_and_le (a:=a) (b:=b))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 41.5s, verify 0.3s, in=891, out=4629)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
constructor
  · intro h
    cases h with
    | inl h => exact Or.inl h
    | inr h =>
      have h₂ : a = b := le_antisymm h.1 h.2
      exact Or.inr h₂
  · intro h
    cases h with
    | inl h => exact Or.inl h
    | inr h =>
      have h₂ : a ≤ b ∧ b ≤ a := by
        rw [h]
        exact ⟨le_refl a, le_refl a⟩
      exact Or.inr h₂
```

**lean_error:** tail step 3/16 ('· intro h'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=830, out=255)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [wcovBy_iff_covBy_or_le_and_le]
rw [le_antisymm_iff]
```
