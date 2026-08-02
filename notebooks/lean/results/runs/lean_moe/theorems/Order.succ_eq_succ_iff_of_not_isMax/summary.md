# Order.succ_eq_succ_iff_of_not_isMax   (k=0, 1 tactics total)

file: `Mathlib/Order/SuccPred/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**True premises at k:** `eq_iff_le_not_lt`, `eq_iff_le_not_lt`, `Order.succ_le_succ_iff_of_not_isMax`, `Order.succ_lt_succ_iff_of_not_isMax`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.7s, verify 0.2s, in=304, out=1951)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact succ_injective h
· intro h
  simpa [h]
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 233.2s, verify 0.2s, in=249, out=31347)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  rw [h]
· intro h
  have h₁ : a < succ a := succ_lt a
  have h₂ : b < succ b := succ_lt b
  have h₃ : a < succ b := by
    calc
      a < succ a := h₁
      _ = succ b := h
  have h₄ : b < succ a := by
    calc
      b < succ b := h₂
      _ = succ a := h
  cases' lt_or_gt_of_ne h with h₅ h₅
  · -- Case a < b
    have h₆ : succ a ≤ b := succ_le_iff.mpr h₅
    have h₇ : succ b ≤ b := by
      calc
        succ b = succ a := by rw [h]
        _ ≤ b := h₆
    have h₈ : b < succ b := succ_lt b
    have h₉ : b < b := lt_of_le_of_lt h₇ h₈
    exact absurd h₉ (lt_irrefl b)
  · -- Case b < a
    have h₆ : succ b ≤ a := succ_le_iff.mpr h₅
    have h₇ : succ a ≤ a := by
      calc
        succ a = succ b := by rw [h]
        _ ≤ a := h₆
    have h₈ : a < succ a := succ_lt a
    have h₉ : a < a := lt_of_le_of_lt h₇ h₈
    exact absurd h₉ (lt_irrefl a)
```

**lean_error:** tail step 2/33 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.2s, in=245, out=516)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact succ_inj ha hb h
· intro h
  rw [h]
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=1055, out=1156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [eq_iff_le_not_lt,
  succ_le_succ_iff_of_not_isMax ha hb,
  succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/3 ('simpa [eq_iff_le_not_lt,'): <stdin>:1:24: unexpected end of input; expected '*' or '-'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 39.8s, verify 0.2s, in=1029, out=4582)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· intro h
  have h₁ : succ a ≤ succ b := (eq_iff_le_not_lt.mp h).1
  have h₂ : ¬succ a < succ b := (eq_iff_le_not_lt.mp h).2
  have h₃ : a ≤ b := (succ_le_succ_iff_of_not_isMax ha hb).mp h₁
  have h₄ : ¬a < b := by
    have h₅ : succ a < succ b ↔ a < b := succ_lt_succ_iff_of_not_isMax ha hb
    have h₆ : ¬succ a < succ b := h₂
    have h₇ : ¬(a < b) := by
      intro h₈
      have h₉ : succ a < succ b := (h₅.mpr h₈)
      exact h₆ h₉
    exact h₇
  have h₅ : a = b := (eq_iff_le_not_lt.mpr ⟨h₃, h₄⟩)
  exact h₅
· intro h
  rw [h]
  <;> rfl
```

**lean_error:** tail step 2/18 ('· intro h'): unsolved goals

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.8s, verify 0.6s, in=938, out=346)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
rfl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.2s, in=1830, out=1480)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  have h₁ : succ a ≤ succ b := by
    simpa [h]
  have h₂ : succ b ≤ succ a := by
    simpa [h]
  have ha_le : a ≤ b := (succ_le_succ_iff_of_not_isMax ha hb).1 h₁
  have hb_le : b ≤ a := (succ_le_succ_iff_of_not_isMax hb ha).1 h₂
  exact le_antisymm ha_le hb_le
· intro h
  simpa [h]
```

**lean_error:** tail step 2/11 ('· intro h'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.8s, verify 0.1s, in=1813, out=3598)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem Order.succ_eq_succ_iff_of_not_isMax {α : Type u_1} [PartialOrder α] [SuccOrder α] {a b : α} (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a = succ b ↔ a = b := by
  have h_forward : succ a = succ b → a = b := by
    intro h
    have h₁ : a ≤ b := by
      have h₂ : succ a ≤ succ b := by
        exact le_of_eq h
      have h₃ : succ a ≤ succ b ↔ a ≤ b := Order.succ_le_succ_iff_of_not_isMax ha hb
      have h₄ : a ≤ b := by
        rw [h₃] at h₂
        exact h₂
      exact h₄
    have h₂ : ¬(a < b) := by
      have h₃ : ¬(succ a < succ b) := by
        intro h₄
        apply h
        exact lt_irrefl _ h₄
      have h₄ : succ a < succ b ↔ a < b := Order.succ_lt_succ_iff_of_not_isMax ha hb
      have h₅ : ¬(a < b) := by
        intro h₆
        have h₇ : succ a < succ b := by
          rw [h₄] at *
          exact h₆
        exact h₃ h₇
      exact h₅
    have h₃ : a = b := by
      have h₄ : a = b ↔ a ≤ b ∧ ¬a < b := eq_iff_le_not_lt
      have h₅ : a ≤ b ∧ ¬a < b := ⟨h₁, h₂⟩
      have h₆ : a = b := by
        rw [h₄]
        exact h₅
      exact h₆
    exact h₃
  
  have h_backward : a = b → succ a = succ b := by
    intro h
    rw [h]
    <;> simp
  
  have h_main : succ a = succ b ↔ a = b := by
    constructor
    · -- Prove the forward direction: succ a = succ b → a = b
      exact h_forward
    · -- Prove the backward direction: a = b → succ a = succ b
      exact h_backward
  
  exact h_main
```

**lean_error:** tail step 1/44 ('theorem Order.succ_eq_succ_iff_of_not_isMax {α : Type u_1} [PartialOrder α] [SuccOrder α] {a b : α} (ha : ¬IsMax a) (hb : ¬IsMax b) :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.4s, verify 0.2s, in=1672, out=582)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
simp only [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=1727, out=958)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,
    succ_lt_succ_iff_of_not_isMax ha hb]
```

**lean_error:** tail step 1/2 ('simpa [eq_iff_le_not_lt, succ_le_succ_iff_of_not_isMax ha hb,'): <stdin>:1:61: unexpected end of input; expected '*' or '-'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 56.2s, verify 0.1s, in=1901, out=6503)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Order.succ_eq_succ_iff_of_not_isMax {α : Type u_1} [PartialOrder α] [SuccOrder α] {a b : α} (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a = succ b ↔ a = b := by
  have h_imp : succ a = succ b → a = b := by
    intro h
    have h₁ : a ≤ b := (Order.succ_le_succ_iff_of_not_isMax ha hb).mp (le_of_eq h)
    have h₂ : ¬(a < b) := by
      intro h₃
      have h₄ : succ a < succ b := (Order.succ_lt_succ_iff_of_not_isMax ha hb).mp h₃
      have h₅ : succ a = succ b := h
      have h₆ : succ a < succ a := by
        rw [h₅] at h₄
        exact h₄
      exact lt_irrefl (succ a) h₆
    have h₃ : a = b := by
      apply eq_iff_le_not_lt.mpr
      exact ⟨h₁, h₂⟩
    exact h₃
  
  have h_conv : a = b → succ a = succ b := by
    intro h
    rw [h]
  
  have h_main : succ a = succ b ↔ a = b := by
    constructor
    · -- Prove the forward direction: succ a = succ b → a = b
      intro h
      exact h_imp h
    · -- Prove the backward direction: a = b → succ a = succ b
      intro h
      exact h_conv h
  
  exact h_main
```

**lean_error:** tail step 1/29 ('theorem Order.succ_eq_succ_iff_of_not_isMax {α : Type u_1} [PartialOrder α] [SuccOrder α] {a b : α} (ha : ¬IsMax a) (hb : ¬IsMax b) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.2s, in=1683, out=421)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [eq_iff_le_not_lt, eq_iff_le_not_lt]
rw [Order.succ_le_succ_iff_of_not_isMax ha hb, Order.succ_lt_succ_iff_of_not_isMax ha hb]
```
