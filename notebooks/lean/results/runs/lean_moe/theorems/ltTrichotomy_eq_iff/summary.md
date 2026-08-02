# ltTrichotomy_eq_iff   (k=3, 4 tactics total)

file: `Mathlib/Order/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne']
```

**True premises at k:** `ltTrichotomy_gt`, `false_and`, `true_and`, `false_or`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | · |
| `hint:3` | ✘ | · | · |
| `noise:3` | ✘ | · | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 1.3s, in=394, out=1736)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hx : ¬ x < y := by
    intro hx
    exact lt_asymm hx h
  have hxy : x ≠ y := by
    intro h_eq
    have : y < y := by simpa [h_eq] using h
    exact lt_irrefl _ this
  simp [ltTrichotomy, hx, hxy, h]
```

**lean_error:** tail step 1/8 ('have hx : ¬ x < y := by'): <stdin>:1:23: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 104.0s, verify 0.1s, in=337, out=12547)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : ¬(x < y) := by
  intro hxy
  have h₂ : y < x := h
  exact lt_irrefl x (lt_trans hxy h₂)
have h₂ : ¬(x = y) := by
  intro hxy
  have h₃ : y < x := h
  rw [hxy] at h₃
  exact lt_irrefl y h₃
have h₃ : ltTrichotomy x y p q r = r := by
  dsimp [ltTrichotomy]
  split_ifs <;>
  (try { contradiction }) <;>
  (try { 
    exfalso
    apply h₁
    <;> tauto
  }) <;>
  (try { 
    exfalso
    apply h₂
    <;> tauto
  }) <;>
  rfl
have h₄ : (ltTrichotomy x y p q r = s) ↔ (r = s) := by
  rw [h₃]
  <;> simp
have h₅ : (r = s) ↔ (x < y ∧ p = s) ∨ (x = y ∧ q = s) ∨ (y < x ∧ r = s) := by
  constructor
  · -- Prove (r = s) → R
    intro hrs
    -- Since we have y < x, the third disjunct is true
    exact Or.inr (Or.inr ⟨h, hrs⟩)
  · -- Prove R → (r = s)
    intro hR
    -- Case on hR
    cases hR with
    | inl hR =>
      -- Case: x < y ∧ p = s
      exfalso
      have h₄ : x < y := hR.1
      have h₅ : y < x := h
      have h₆ : x = y := lt_antisymm h₄ h₅
      have h₇ : y < x := h
      rw [h₆] at h₇
      exact lt_irrefl y h₇
    | inr hR =>
      cases hR with
      | inl hR =>
        -- Case: x = y ∧ q = s
        exfalso
        have h₄ : x = y := hR.1
        have h₅ : y < x := h
        rw [h₄] at h₅
        exact lt_irrefl y h₅
      | inr hR =>
        -- Case: y < x ∧ r = s
        exact hR.2
exact h₄.trans h₅
```

**lean_error:** tail step 1/59 ('have h₁ : ¬(x < y) := by'): <stdin>:1:24: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.3s, in=330, out=529)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ltTrichotomy]
simp [h, lt_irrefl, lt_asymm, h]
<;> tauto
```

**lean_error:** tail step 3/3 ('<;> tauto'): <stdin>:1:0: expected tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 8.2s, verify 0.1s, in=996, out=1454)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, or_false, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 131.9s, verify 0.4s, in=956, out=16494)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : ¬(x < y) := lt_asymm h
have h₂ : x ≠ y := ne_of_gt h
have h₃ : ltTrichotomy x y p q r = r := ltTrichotomy_gt h
have h₄ : (x < y ∧ p = s) ∨ (x = y ∧ q = s) ∨ (y < x ∧ r = s) = (r = s) := by
  have h₅ : y < x := h
  have h₆ : ¬(x < y) := h₁
  have h₇ : ¬(x = y) := h₂
  have h₈ : (x < y ∧ p = s) = False := by
    apply False.eq_true_of_false
    intro h₉
    exact h₆ h₉.1
  have h₉ : (x = y ∧ q = s) = False := by
    apply False.eq_true_of_false
    intro h₁₀
    exact h₇ h₁₀.1
  have h₁₀ : (y < x ∧ r = s) = (r = s) := by
    constructor <;> intro h₁₁ <;>
    (try { exact h₁₁.2 }) <;>
    (try { exact ⟨h, h₁₁⟩ })
  calc
    (x < y ∧ p = s) ∨ (x = y ∧ q = s) ∨ (y < x ∧ r = s) = False ∨ False ∨ (r = s) := by
      rw [h₈, h₉, h₁₀]
    _ = (r = s) := by
      simp [false_or]
      <;> tauto
rw [h₃]
have h₅ : (x < y ∧ p = s) ∨ (x = y ∧ q = s) ∨ (y < x ∧ r = s) = (r = s) := h₄
rw [h₅]
<;> tauto
```

**lean_error:** tail step 4/29 ('have h₄ : (x < y ∧ p = s) ∨ (x = y ∧ q = s) ∨ (y < x ∧ r = s) = (r = s) := by'): <stdin>:1:77: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 56.2s, verify 0.1s, in=929, out=5703)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.2s, in=1766, out=1130)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, or_false, false_or, h, h.not_lt, h.ne]
simp
```

**lean_error:** tail step 2/2 ('simp'): simp made no progress

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 78.1s, verify 0.1s, in=1722, out=8747)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ltTrichotomy_gt h, false_and, true_and, false_or]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.8s, verify 0.1s, in=1684, out=562)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 3.4s, in=1685, out=1628)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [ltTrichotomy_gt h]
```

**lean_error:** tail step 1/1 ('simpa [ltTrichotomy_gt h]'): tactic 'assumption' failed

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 95.7s, verify 0.2s, in=1853, out=11516)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ltTrichotomy_gt h]
simp [h, false_and, true_and, false_or]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.4s, verify 0.1s, in=1693, out=528)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```
