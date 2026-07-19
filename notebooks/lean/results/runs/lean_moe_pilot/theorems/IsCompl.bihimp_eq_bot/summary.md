# IsCompl.bihimp_eq_bot   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

**True premises at k:** `compl_bihimp_self`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 28.0s, verify 0.1s, in=304, out=4498)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [IsCompl, inf_eq_bot, sup_eq_top] using h
```

**lean_error:** tail step 1/1 ('simpa [IsCompl, inf_eq_bot, sup_eq_top] using h'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 86.9s, verify 0.1s, in=252, out=9131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : a ∧ b = ⊥ := h.1
have h₂ : a ∨ b = ⊤ := h.2
have h₃ : a → b ≤ b := by
  have h₃₁ : a → b = (a → b) ∧ (a ∨ b) := by
    rw [h₂]
    <;> simp [inf_comm]
  rw [h₃₁]
  have h₃₂ : (a → b) ∧ (a ∨ b) = ((a → b) ∧ a) ∨ ((a → b) ∧ b) := by
    rw [inf_sup]
    <;> simp [inf_comm, inf_left_comm, inf_assoc]
    <;> ring_nf
    <;> simp_all [inf_comm, inf_left_comm, inf_assoc]
    <;> tauto
  rw [h₃₂]
  have h₃₃ : ((a → b) ∧ a) ∨ ((a → b) ∧ b) ≤ b ∨ b := by
    apply sup_le
    · -- prove (a → b) ∧ a ≤ b
      have h₃₄ : a ∧ (a → b) ≤ b := imp_le a b
      have h₃₅ : (a → b) ∧ a = a ∧ (a → b) := by rw [inf_comm]
      rw [h₃₅]
      exact h₃₄
    · -- prove (a → b) ∧ b ≤ b
      apply inf_le_right
  have h₃₆ : b ∨ b = b := by rw [sup_idempotent]
  rw [h₃₆] at h₃₃
  exact h₃₃
have h₄ : b → a ≤ a := by
  have h₄₁ : b → a = (b → a) ∧ (b ∨ a) := by
    have h₄₂ : b ∨ a = a ∨ b := by rw [sup_comm]
    rw [h₄₂]
    have h₄₃ : a ∨ b = ⊤ := h₂
    rw [h₄₃]
    <;> simp [inf_comm]
  rw [h₄₁]
  have h₄₄ : (b → a) ∧ (b ∨ a) = ((b → a) ∧ b) ∨ ((b → a) ∧ a) := by
    rw [inf_sup]
    <;> simp [inf_comm, inf_left_comm, inf_assoc]
    <;> ring_nf
    <;> simp_all [inf_comm, inf_left_comm, inf_assoc]
    <;> tauto
  rw [h₄₄]
  have h₄₅ : ((b → a) ∧ b) ∨ ((b → a) ∧ a) ≤ a ∨ a := by
    apply sup_le
    · -- prove (b → a) ∧ b ≤ a
      have h₄₆ : b ∧ (b → a) ≤ a := imp_le b a
      have h₄₇ : (b → a) ∧ b = b ∧ (b → a) := by rw [inf_comm]
      rw [h₄₇]
      exact h₄₆
    · -- prove (b → a) ∧ a ≤ a
      apply inf_le_right
  have h₄₈ : a ∨ a = a := by rw [sup_idempotent]
  rw [h₄₈] at h₄₅
  exact h₄₅
have h₅ : (a → b) ∧ (b → a) ≤ ⊥ := by
  have h₅₁ : (a → b) ∧ (b → a) ≤ b ∧ a := by
    apply inf_le_inf
    · exact h₃
    · exact h₄
  have h₅₂ : b ∧ a = a ∧ b := by rw [inf_comm]
  rw [h₅₂] at h₅₁
  rw [h₁] at h₅₁
  exact h₅₁
have h₆ : (a → b) ∧ (b → a) = ⊥ := by
  apply le_antisymm
  · -- ⊥ ≤ (a → b) ∧ (b → a)
    exact bot_le
  · -- (a → b) ∧ (b → a) ≤ ⊥
    exact h₅
have h₇ : a ⇔ b = (a → b) ∧ (b → a) := by
  simp [Iff]
rw [h₇]
exact h₆
```

**lean_error:** tail step 1/72 ('have h₁ : a ∧ b = ⊥ := h.1'): application type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.1s, in=247, out=985)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.1, inf_comm]
```

**lean_error:** tail step 1/1 ('simp [h.1, inf_comm]'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 13.8s, verify 0.1s, in=491, out=1164)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [h.compl_eq, bihimp_comm] using (compl_bihimp_self (a:=a))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 150.3s, verify 0.1s, in=448, out=16606)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : a ∧ b = ⊥ := h.1
have h₂ : a ∨ b = ⊤ := h.2
have h₃ : b ≤ a → ⊥ := by
  have h₄ : a ∧ b ≤ ⊥ := by simpa using h₁
  exact le_imp.mp h₄
have h₄ : a → ⊥ ≤ b := by
  calc
    a → ⊥ = (a → ⊥) ∧ ⊤ := by simp
    _ = (a → ⊥) ∧ (a ∨ b) := by rw [h₂]
    _ = ((a → ⊥) ∧ a) ∨ ((a → ⊥) ∧ b) := by
      rw [inf_sup_distrib]
    _ = (⊥) ∨ ((a → ⊥) ∧ b) := by
      have h₅ : (a → ⊥) ∧ a = ⊥ := by
        have h₅₁ : a ∧ (a → ⊥) = ⊥ := by
          apply le_antisymm
          · -- Show a ∧ (a → ⊥) ≤ ⊥
            have h₅₂ : (a → ⊥) ≤ a → ⊥ := le_refl
            exact inf_le_of_le h₅₂
          · -- Show ⊥ ≤ a ∧ (a → ⊥)
            exact bot_le
        have h₅₃ : (a → ⊥) ∧ a = a ∧ (a → ⊥) := by
          rw [inf_comm]
        rw [h₅₃]
        exact h₅₁
      rw [h₅]
      <;> simp [inf_comm]
    _ = (a → ⊥) ∧ b := by simp [sup_bot]
    _ ≤ b := by exact inf_le_right
have h₅ : b = a → ⊥ := by
  apply le_antisymm
  · exact h₃
  · exact h₄
have h₆ : a ⇔ b = ⊥ := by
  rw [h₅]
  have h₇ : a ⇔ (a → ⊥) = (a → ⊥) ⇔ a := by
    have h₁ : a ⇔ (a → ⊥) = (a → (a → ⊥)) ∧ ((a → ⊥) → a) := rfl
    have h₂ : (a → ⊥) ⇔ a = ((a → ⊥) → a) ∧ (a → (a → ⊥)) := rfl
    rw [h₁, h₂]
    <;> rw [inf_comm]
  rw [h₇]
  rw [compl_bihimp_self]
exact h₆
```

**lean_error:** tail step 1/42 ('have h₁ : a ∧ b = ⊥ := h.1'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.2s, in=438, out=492)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← h.compl_eq]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 15.2s, verify 0.1s, in=605, out=1437)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [h.compl_eq, bihimp_comm] using (compl_bihimp_self (a:=a))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 116.3s, verify 0.1s, in=565, out=12550)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_nota_and_a : a ⊓ ¬a = ⊥ := by
  have h₁ : a ⊓ ¬a ≤ ⊥ := by
    have h₂ : a ⊓ ¬a = a ⊓ (a → ⊥) := by simp [not_eq]
    rw [h₂]
    exact imp_le (by simp [inf_comm])
  have h₂ : ⊥ ≤ a ⊓ ¬a := bot_le
  exact le_antisymm h₁ h₂

have h_b_le_nota : b ≤ ¬a := by
  have h₁ : a ⊓ b = ⊥ := h.inf_eq_bot
  have h₂ : a ⊓ b ≤ ⊥ := by rw [h₁]; exact le_bot
  have h₃ : b ≤ a → ⊥ := by
    rw [inf_le_iff] at h₂
    exact h₂
  have h₄ : a → ⊥ = ¬a := by simp [not_eq]
  rw [h₄] at h₃
  exact h₃

have h_nota_le_b : ¬a ≤ b := by
  calc
    ¬a = ¬a ⊓ ⊤ := by simp [inf_top]
    _ = ¬a ⊓ (a ⊔ b) := by rw [h.sup_eq_top]
    _ = (¬a ⊓ a) ⊔ (¬a ⊓ b) := by rw [inf_sup]
    _ = ⊥ ⊔ (¬a ⊓ b) := by
      have h₁ : ¬a ⊓ a = ⊥ := by
        have h₂ : a ⊓ ¬a = ⊥ := h_nota_and_a
        have h₃ : ¬a ⊓ a = a ⊓ ¬a := by rw [inf_comm]
        rw [h₃]
        exact h₂
      rw [h₁]
      <;> simp [sup_bot]
    _ = ¬a ⊓ b := by simp [sup_bot]
    _ ≤ b := inf_le_right

have h_b_eq_nota : b = ¬a := by
  apply le_antisymm
  · exact h_b_le_nota
  · exact h_nota_le_b

have h_main : a ⇔ b = ⊥ := by
  calc
    a ⇔ b = a ⇔ ¬a := by rw [h_b_eq_nota]
    _ = ¬a ⇔ a := by
      calc
        a ⇔ ¬a = (a → ¬a) ⊓ (¬a → a) := rfl
        _ = (¬a → a) ⊓ (a → ¬a) := by rw [inf_comm]
        _ = ¬a ⇔ a := by rfl
    _ = ⊥ := by apply compl_bihimp_self

exact h_main
```

**lean_error:** tail step 1/45 ('have h_nota_and_a : a ⊓ ¬a = ⊥ := by'): <stdin>:1:36: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 63.4s, verify 0.1s, in=552, out=6946)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.compl_eq, biimp_comm]
exact compl_bihimp_self
```

**lean_error:** tail step 1/2 ('rw [h.compl_eq, biimp_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 0.1s, in=616, out=1583)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [h.compl_eq] using (compl_bihimp_self (a:=a))
```

**lean_error:** tail step 1/1 ('simpa [h.compl_eq] using (compl_bihimp_self (a:=a))'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 121.3s, verify 0.1s, in=603, out=13122)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : a ⊓ b = ⊥ := h.1
have h₂ : a ⊔ b = ⊤ := h.2
have h₃ : b ≤ ¬a := by
  have h₄ : a ⊓ b ≤ ⊥ := by rw [h₁]; exact le_refl _
  exact imp_le h₄
have h₄ : ¬a ≤ b := by
  have h₅ : a ⊓ ¬a ≤ ⊥ := by exact le_of_imp (by intro h₆; exact imp_le (le_refl _))
  have h₆ : a ⊓ ¬a ≤ b := by
    calc
      a ⊓ ¬a ≤ ⊥ := h₅
      _ ≤ b := by exact bot_le
  have h₇ : ¬a = ¬a ⊓ (a ⊔ b) := by
    rw [h₂]
    <;> simp [inf_comm]
  have h₈ : ¬a ⊓ (a ⊔ b) = (¬a ⊓ a) ⊔ (¬a ⊓ b) := by
    rw [inf_sup_distrib]
  have h₉ : ¬a ⊓ a = ⊥ := by
    have h₁₀ : a ⊓ ¬a ≤ ⊥ := h₅
    have h₁₁ : ⊥ ≤ a ⊓ ¬a := bot_le
    have h₁₂ : a ⊓ ¬a = ⊥ := by apply le_antisymm h₁₀ h₁₁
    have h₁₃ : ¬a ⊓ a = a ⊓ ¬a := by rw [inf_comm]
    rw [h₁₃]
    exact h₁₂
  calc
    ¬a = ¬a ⊓ (a ⊔ b) := h₇
    _ = (¬a ⊓ a) ⊔ (¬a ⊓ b) := h₈
    _ = ⊥ ⊔ (¬a ⊓ b) := by rw [h₉]
    _ = ¬a ⊓ b := by simp [inf_comm]
    _ ≤ b := by apply inf_le_right
have h₅ : b = ¬a := by apply le_antisymm h₃ h₄
have h₆ : a ⇔ b = ⊥ := by
  rw [h₅]
  have h₇ : a ⇔ ¬a = ⊥ := by
    have h₈ : a ⇔ ¬a = ¬a ⇔ a := by rw [iff_comm]
    rw [h₈]
    exact compl_bihimp_self
  exact h₇
exact h₆
```

**lean_error:** tail step 1/38 ('have h₁ : a ⊓ b = ⊥ := h.1'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=575, out=589)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.compl_eq]
simp [compl_bihimp_self]
```

**lean_error:** tail step 1/2 ('rw [h.compl_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
