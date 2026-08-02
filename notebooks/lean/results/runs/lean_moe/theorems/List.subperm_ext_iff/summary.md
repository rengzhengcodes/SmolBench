# List.subperm_ext_iff   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/List/Perm.lean`  

**Ground-truth tail (from k):**
```lean
exact perm_append_comm.trans (subperm_append_diff_self_of_count_le h)
```

**True premises at k:** `List.subperm_append_diff_self_of_count_le`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=332, out=763)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using List.diff_append_self l₂ l₁
```

**lean_error:** tail step 1/1 ('simpa using List.diff_append_self l₂ l₁'): unknown constant 'List.diff_append_self'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 247.1s, verify 0.1s, in=279, out=32523)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : l₁ <+~ l₂ := by
  intro x
  by_cases hx : x ∈ l₁
  · exact h x hx
  · exact Nat.zero_le (count x l₂)
have h₂ : l₂ <+~ l₁ := by
  sorry
have h₃ : l₁ ~ l₂ := by
  apply Eq.symm
  apply Eq.symm
  exact Subperm.antisymm h₁ h₂
have h₄ : List.diff l₂ l₁ ++ l₁ = l₁ := by
  have h₅ : List.diff l₂ l₁ = [] := by
    rw [List.diff_eq_nil_iff]
    <;> aesop
  rw [h₅]
  <;> simp
have h₅ : List.diff l₂ l₁ ++ l₁ ~ l₂ := by
  rw [h₄]
  exact h₃
exact h₅
```

**lean_error:** tail step 1/21 ('have h₁ : l₁ <+~ l₂ := by'): <stdin>:1:25: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=264, out=742)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply List.Perm.diff_append_of_subperm
intro x
by_cases hx : x ∈ l₁
· exact h x hx
· simp [hx]
```

**lean_error:** tail step 1/5 ('apply List.Perm.diff_append_of_subperm'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=857, out=1889)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (perm_append_comm _ _).symm.trans (subperm_append_diff_self_of_count_le h)
```

**lean_error:** tail step 1/1 ('exact (perm_append_comm _ _).symm.trans (subperm_append_diff_self_of_count_le h)'): function expected at

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 185.1s, verify 0.1s, in=823, out=23537)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_pair : (∀ x ∈ l₁, count x l₁ ≤ count x l₂) × (l₁ ++ l₂.diff l₁ ~ l₂) := by
  refine ⟨fun h x _ => h.count_le x, _⟩
  exact subperm_append_diff_self_of_count_le h
have : l₁ <+~ l₂.diff l₁ ++ l₁ := (subperm_append_right l₁).mpr nil_subperm
refine this.trans (Perm.subperm <;> rfl)
have h₁ : l₁ ++ l₂.diff l₁ ~ l₂ := h_pair.2
have h₂ : l₁ ++ l₂.diff l₁ ~ l₂.diff l₁ ++ l₁ := append_comm l₁ (l₂.diff l₁)
have h₃ : l₂.diff l₁ ++ l₁ ~ l₂ := h₂.symm.trans h₁
exact h₃
```

**lean_error:** tail step 1/9 ('have h_pair : (∀ x ∈ l₁, count x l₁ ≤ count x l₂) × (l₁ ++ l₂.diff l₁ ~ l₂) := by'): <stdin>:1:81: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 301.9s, verify 0.0s, in=767, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=1971, out=1566)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (perm_append_comm _ _).trans (subperm_append_diff_self_of_count_le h)
```

**lean_error:** tail step 1/1 ('exact (perm_append_comm _ _).trans (subperm_append_diff_self_of_count_le h)'): function expected at

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 208.4s, verify 0.1s, in=1953, out=26667)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h' : ∀ x : α, count x l₁ ≤ count x l₂ := by
  intro x
  by_cases hx : x ∈ l₁
  · exact h x hx
  · have h₁ : count x l₁ = 0 := by
      simp [hx, List.count_nil]
    rw [h₁]
    <;> omega
have h_mset : (l₁ : Multiset α) ≤ (l₂ : Multiset α) := by
  apply Multiset.le_iff_count.mpr
  intro x
  exact h' x
have h_eq : (List.diff l₂ l₁ ++ l₁ : Multiset α) = (l₂ : Multiset α) := by
  calc
    (List.diff l₂ l₁ ++ l₁ : Multiset α) = (List.diff l₂ l₁ : Multiset α) + (l₁ : Multiset α) := by
      simp [Multiset.add_assoc]
    _ = ((l₂ : Multiset α) - (l₁ : Multiset α)) + (l₁ : Multiset α) := by
      rw [multiset_diff]
    _ = (l₂ : Multiset α) := by
      rw [add_sub_cancel h_mset]
have h_perm : List.diff l₂ l₁ ++ l₁ ~ l₂ := by
  apply List.perm_iff.mpr
  exact h_eq
exact h_perm
```

**lean_error:** tail step 1/24 ("have h' : ∀ x : α, count x l₁ ≤ count x l₂ := by"): <stdin>:1:48: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=1839, out=634)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (List.subperm_append_diff_self_of_count_le h).trans (List.perm_append_comm _ _)
```

**lean_error:** tail step 1/1 ('exact (List.subperm_append_diff_self_of_count_le h).trans (List.perm_append_comm _ _)'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=1824, out=1583)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
by
  simpa [append_comm] using (subperm_append_diff_self_of_count_le h)
```

**lean_error:** tail step 1/2 ('by'): <stdin>:1:0: expected tactic

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.4s, verify 0.1s, in=2086, out=5645)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : List.diff l₂ l₁ ++ l₁ ~ l₁ ++ List.diff l₂ l₁ := by
  rw [← perm_iff_mset_eq]
  <;> simp [mset_append, add_comm]
  <;>
  rfl
have h₂ : l₁ ++ List.diff l₂ l₁ ~ l₂ := List.subperm_append_diff_self_of_count_le h
exact Perm.trans h₁ h₂
```

**lean_error:** tail step 1/7 ('have h₁ : List.diff l₂ l₁ ++ l₁ ~ l₁ ++ List.diff l₂ l₁ := by'): <stdin>:1:61: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=1842, out=525)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (subperm_append_diff_self_of_count_le h).symm.trans (append_comm _ _)
```

**lean_error:** tail step 1/1 ('exact (subperm_append_diff_self_of_count_le h).symm.trans (append_comm _ _)'): type mismatch
