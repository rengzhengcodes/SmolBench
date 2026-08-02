# List.Sublist.erase   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact Sublist.eraseP h
```

**True premises at k:** `List.Sublist.eraseP`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=339, out=441)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.eraseP (fun x => a == x)
```

**lean_error:** tail step 1/1 ('exact h.eraseP (fun x => a == x)'): function expected at

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.3s, verify 0.1s, in=285, out=14554)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (filter (fun x => x ≠ a) l₁) <+ (filter (fun x => x ≠ a) l₂) := List.filter_subseq h
have h₂ : List.eraseP (fun x => a == x) l₁ = filter (fun x => x ≠ a) l₁ := by
  have h₂₁ : List.eraseP (fun x => a == x) l₁ = filter (fun x => ¬ (a == x)) l₁ := by
    rw [List.eraseP_eq_filter_not]
  rw [h₂₁]
  apply filter_congr rfl
  intro x
  have h₂₂ : ¬ (a == x) ↔ x ≠ a := by
    constructor
    · intro h
      by_contra h₃
      have h₄ : x = a := by simpa using h₃
      have h₅ : a == x := by
        have h₆ : a == x ↔ a = x := by apply beq_eq
        have h₇ : a = x := by
          rw [h₄]
          <;> rfl
        exact mp h₆ h₇
      exact h h₅
    · intro h
      have h₃ : a == x := by
        have h₄ : a == x ↔ a = x := by apply beq_eq
        have h₅ : a = x := by
          tauto
        exact mp h₄ h₅
      exact h h₃
  exact h₂₂
have h₃ : List.eraseP (fun x => a == x) l₂ = filter (fun x => x ≠ a) l₂ := by
  have h₃₁ : List.eraseP (fun x => a == x) l₂ = filter (fun x => ¬ (a == x)) l₂ := by
    rw [List.eraseP_eq_filter_not]
  rw [h₃₁]
  apply filter_congr rfl
  intro x
  have h₃₂ : ¬ (a == x) ↔ x ≠ a := by
    constructor
    · intro h
      by_contra h₄
      have h₅ : x = a := by simpa using h₄
      have h₆ : a == x := by
        have h₇ : a == x ↔ a = x := by apply beq_eq
        have h₈ : a = x := by
          rw [h₅]
          <;> rfl
        exact mp h₇ h₈
      exact h h₆
    · intro h
      have h₄ : a == x := by
        have h₅ : a == x ↔ a = x := by apply beq_eq
        have h₆ : a = x := by
          tauto
        exact mp h₅ h₆
      exact h h₄
  exact h₃₂
rw [h₂, h₃]
exact h₁
```

**lean_error:** tail step 1/55 ('have h₁ : (filter (fun x => x ≠ a) l₁) <+ (filter (fun x => x ≠ a) l₂) := List.filter_subseq h'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.9s, verify 0.1s, in=277, out=1324)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.filter (fun x => ¬(a == x))
```

**lean_error:** tail step 1/1 ('exact h.filter (fun x => ¬(a == x))'): invalid field 'filter', the environment does not contain 'List.Sublist.filter'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.9s, verify 0.1s, in=618, out=615)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (Sublist.eraseP (p:=fun x => a == x) h)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 30.6s, verify 0.1s, in=578, out=3989)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply List.Sublist.eraseP
<;> assumption
```

**lean_error:** tail step 2/2 ('<;> assumption'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.8s, verify 0.1s, in=555, out=466)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.eraseP
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=837, out=666)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (Sublist.eraseP (p:=fun x => a == x) h)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=805, out=716)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact List.Sublist.eraseP h
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=768, out=524)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply List.Sublist.eraseP
exact h
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.7s, verify 0.1s, in=832, out=706)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.eraseP
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 21.6s, verify 0.1s, in=850, out=2581)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [erase_eq_eraseP] at *
exact List.Sublist.eraseP h
```

**lean_error:** tail step 1/2 ('rw [erase_eq_eraseP] at *'): tactic 'rewrite' failed, did not find instance of the pattern in the current goal

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.1s, in=791, out=459)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply List.Sublist.eraseP
exact h
```
