# String.contains_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [contains, any_iff]
```

**True premises at k:** `String.contains`, `String.any_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=264, out=906)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [String.contains]
```

**lean_error:** tail step 1/1 ('simpa [String.contains]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 13.6s, verify 0.2s, in=204, out=1522)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [String.contains]
constructor
· intro h
  exact Array.contains_mem h
· intro h
  exact Array.mem_contains h
```

**lean_error:** tail step 3/6 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 3.7s, verify 0.1s, in=205, out=273)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [String.contains]
```

**final state (truncated):**
```
s : String
c : Char
⊢ (any s fun a => a == c) = true ↔ c ∈ s.data
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.6s, verify 0.2s, in=558, out=4252)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h
    have h' : any s (fun a => a == c) = true := by
      simpa [String.contains] using h
    rcases (String.any_iff s (fun a => a == c)).1 h' with ⟨a, ha, hac⟩
    have : a = c := by
      have : (a == c) = true := by
        simpa using hac
      simpa [decide_eq_true] using this
    simpa [this] using ha
  · intro hc
    have h' : any s (fun a => a == c) = true := by
      apply (String.any_iff s (fun a => a == c)).2
      exact ⟨c, hc, by simp⟩
    simpa [String.contains] using h'
```

**lean_error:** tail step 2/15 ('· intro h'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 121.8s, verify 0.2s, in=491, out=13760)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· intro h
  have h₁ : contains s c = s.any (fun a => a == c) := rfl
  rw [h₁] at h
  have h₂ : s.any (fun a => a == c) = true ↔ ∃ c' ∈ s.1, (fun a => a == c) c' = true := by
    apply Eq.symm
    apply String.any_iff
  have h₃ : ∃ c' ∈ s.1, (fun a => a == c) c' = true := by
    rw [h₂] at h
    exact h
  obtain ⟨c', hc', hc'⟩ := h₃
  have h₄ : (fun a => a == c) c' = true := hc'
  have h₅ : c' == c := by
    simp [h₄]
    <;> aesop
  have h₆ : c' = c := by exact_mod_eq h₅
  have h₇ : c' ∈ s.1 := hc'
  have h₈ : c ∈ s.1 := by
    rw [h₆] at h₇
    exact h₇
  exact h₈
· intro h
  have h₁ : s.any (fun a => a == c) = true ↔ ∃ c' ∈ s.1, (fun a => a == c) c' = true := by
    apply Eq.symm
    apply String.any_iff
  have h₂ : (∃ c' ∈ s.1, (fun a => a == c) c' = true) := by
    refine' ⟨c, h, _⟩
    simp
    <;> aesop
  have h₃ : s.any (fun a => a == c) = true := by
    rw [h₁]
    exact h₂
  exact h₃
```
```

**lean_error:** tail step 2/34 ('· intro h'): unsolved goals

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=494, out=485)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [String.contains, String.any_iff, Bool.eq_true_iff]
```

**lean_error:** tail step 1/1 ('simp [String.contains, String.any_iff, Bool.eq_true_iff]'): unknown constant 'Bool.eq_true_iff'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.2s, verify 0.1s, in=1167, out=2001)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [String.contains] using (String.any_iff s (fun a => a == c))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.8s, verify 0.1s, in=1108, out=9215)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.contains]
have h₁ : s.any (fun a => a == c) = true ↔ (∃ a ∈ s.1, (a == c) = true) := by
  exact String.any_iff s (fun a => a == c)
rw [h₁]
have h₂ : (∃ a ∈ s.1, (a == c) = true) ↔ (∃ a ∈ s.1, a = c) := by
  apply Set.mem_setOf_eq
  intro a ha
  <;> simp_all [Bool.eq_true_iff]
  <;> tauto
rw [h₂]
have h₃ : s.1 = s.data := by rfl
rw [h₃]
<;> simp [Set.mem_setOf_eq]
<;> tauto
```
```

**lean_error:** tail step 2/15 ('have h₁ : s.any (fun a => a == c) = true ↔ (∃ a ∈ s.1, (a == c) = true) := by'): <stdin>:1:77: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.2s, in=1119, out=647)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [String.contains]
rw [String.any_iff]
simp [List.mem_def]
```

**lean_error:** tail step 3/3 ('simp [List.mem_def]'): unknown constant 'List.mem_def'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.6s, verify 0.1s, in=1122, out=2354)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [String.contains] using (String.any_iff s (fun a => a == c))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 145.8s, verify 0.1s, in=1222, out=16525)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [String.contains, String.any_iff]
<;> constructor <;> tauto
```

**lean_error:** tail step 2/2 ('<;> constructor <;> tauto'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.2s, in=1120, out=604)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [String.contains]
rw [String.any_iff]
simp [Bool.eq_true_iff, List.mem_iff_exists_eq]
```

**lean_error:** tail step 3/3 ('simp [Bool.eq_true_iff, List.mem_iff_exists_eq]'): unknown constant 'Bool.eq_true_iff'
