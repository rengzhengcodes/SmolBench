# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.6s, verify 0.2s, in=338, out=2539)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases hs with ⟨y, hy⟩
have hb : BddBelow {a | ∀ x ∈ s, x ≤ a} :=
  ⟨y, by
    intro a ha
    exact ha y hy⟩
apply le_antisymm
·
  have hmem : ∀ x ∈ s, x ≤ sSup s :=
    by
      intro x hx
      exact le_csSup h hx
  exact csInf_le hb hmem
·
  apply le_csInf hb
  intro a ha
  exact csSup_le h ha
```

**lean_error:** tail step 2/16 ('have hb : BddBelow {a | ∀ x ∈ s, x ≤ a} :='): <stdin>:1:42: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 46.9s, verify 0.2s, in=281, out=5371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨b, hb⟩ := h
have hU_nonempty : ({a : α | ∀ x ∈ s, x ≤ a}).Nonempty := by
  refine' ⟨b, _⟩
  intro x hx
  exact hb x hx
obtain ⟨x0, hx0⟩ := hs
have hU_bdd_below : BddBelow ({a : α | ∀ x ∈ s, x ≤ a}) := by
  use x0
  intro a ha
  have h₁ : ∀ x ∈ s, x ≤ a := ha
  have h₂ : x0 ∈ s := hx0
  have h₃ : x0 ≤ a := h₁ x0 h₂
  exact h₃
have hSup_in_U : sSup s ∈ ({a : α | ∀ x ∈ s, x ≤ a}) := by
  apply csSup_mem h hs
have hSup_le_U : ∀ b ∈ ({a : α | ∀ x ∈ s, x ≤ a}), sSup s ≤ b := by
  intro b hb
  have h₁ : ∀ x ∈ s, x ≤ b := hb
  exact csSup_le h hs h₁
have h_main : sInf ({a : α | ∀ x ∈ s, x ≤ a}) = sSup s := by
  apply csInf_eq_of_forall_le_of_mem hU_nonempty hU_bdd_below hSup_in_U hSup_le_U
exact h_main
```

**lean_error:** tail step 2/22 ('have hU_nonempty : ({a : α | ∀ x ∈ s, x ≤ a}).Nonempty := by'): <stdin>:1:60: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=279, out=766)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [csSup_eq_csInf]
```

**lean_error:** tail step 1/1 ('rw [csSup_eq_csInf]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=602, out=515)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 16.3s, verify 0.1s, in=561, out=1832)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=547, out=527)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=946, out=622)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 34.4s, verify 0.1s, in=903, out=3911)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₂ : {a | ∀ x ∈ s, x ≤ a} = upperBounds s := by
  apply Set.ext
  intro y
  constructor
  · intro h
    intro a ha
    exact h a ha
  · intro h
    intro x hx
    exact h x hx
rw [h₂]
apply csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/12 ('have h₂ : {a | ∀ x ∈ s, x ≤ a} = upperBounds s := by'): <stdin>:1:52: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.2s, verify 0.2s, in=886, out=289)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.7s, verify 0.1s, in=922, out=803)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 23.9s, verify 0.1s, in=972, out=2705)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply csInf_upper_bounds_eq_csSup h hs
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=900, out=475)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [upperBounds]
exact csInf_upper_bounds_eq_csSup h hs
```

**lean_error:** tail step 1/2 ('rw [upperBounds]'): failed to rewrite using equation theorems for 'upperBounds'
