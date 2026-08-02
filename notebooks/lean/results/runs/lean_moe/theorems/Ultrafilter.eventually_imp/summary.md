# Ultrafilter.eventually_imp   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Ultrafilter.lean`  

**Ground-truth tail (from k):**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

**True premises at k:** `imp_iff_not_or`, `Ultrafilter.eventually_or`, `Ultrafilter.eventually_not`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 1.3s, in=382, out=629)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (Filter.eventually_imp (f := (↑f : Filter α)) (p := p) (q := q))
```

**lean_error:** tail step 1/1 ('simpa using (Filter.eventually_imp (f := (↑f : Filter α)) (p := p) (q := q))'): unknown constant 'Filter.eventually_imp'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.8s, verify 0.2s, in=328, out=4619)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
- intro h
  intro h₁
  exact Filter.eventually_mp h h₁
- intro h
  have h₁ : (∀ᶠ x in ↑f, p x) ∨ (∀ᶠ x in ↑f, ¬ p x) := by
    have h₂ : ({x : α | p x} : Set α) ∈ f ∨ ({x : α | p x} : Set α)ᶜ ∈ f := Ultrafilter.exists_mem_or_mem_compl f
    cases h₂ with
    | inl h₂ =>
      have h₃ : ∀ᶠ x in ↑f, p x := by
        simpa [mem_iff_eventually] using h₂
      exact Or.inl h₃
    | inr h₂ =>
      have h₃ : ∀ᶠ x in ↑f, ¬ p x := by
        have h₄ : ({x : α | p x} : Set α)ᶜ = {x : α | ¬ p x} := by ext x; simp
        rw [h₄] at h₂
        simpa [mem_iff_eventually] using h₂
      exact Or.inr h₃
  cases h₁ with
  | inl hnp =>
    have hq : ∀ᶠ x in ↑f, q x := h hnp
    have h₂ : ∀ᶠ x in ↑f, p x → q x := by
      have h₃ : ∀ᶠ x in ↑f, q x := hq
      have h₄ : ∀ᶠ x in ↑f, (p x → q x) := by
        apply Filter.eventually_mono h₃
        intro x hx
        exact fun hp => hx
      exact h₄
    exact h₂
  | inr hnp =>
    have h₂ : ∀ᶠ x in ↑f, p x → q x := by
      have h₃ : ∀ᶠ x in ↑f, ¬ p x := hnp
      have h₄ : ∀ᶠ x in ↑f, (p x → q x) := by
        apply Filter.eventually_mono h₃
        intro x hx
        exact fun hp => hx hp
      exact h₄
    exact h₂
```

**lean_error:** tail step 2/38 ('- intro h'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=322, out=505)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Filter.eventually_imp]
```

**lean_error:** tail step 1/1 ('simp [Filter.eventually_imp]'): unknown constant 'Filter.eventually_imp'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.6s, verify 0.8s, in=859, out=3756)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [imp_iff_not_or, eventually_not] using
    (eventually_or (f := f) (p := fun x => ¬ p x) (q := q))
```

**lean_error:** tail step 1/2 ('simpa [imp_iff_not_or, eventually_not] using'): <stdin>:1:44: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 46.0s, verify 0.1s, in=801, out=5207)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  (∀ᶠ (x : α) in ↑f, p x → q x) ↔ (∀ᶠ (x : α) in ↑f, ¬p x ∨ q x) := by
    apply Filter.eventually_congr'
    intro x
    exact imp_iff_not_or
  _ ↔ ((∀ᶠ (x : α) in ↑f, ¬p x) ∨ (∀ᶠ (x : α) in ↑f, q x)) := by
    rw [Ultrafilter.eventually_or]
  _ ↔ (¬∀ᶠ (x : α) in ↑f, p x) ∨ (∀ᶠ (x : α) in ↑f, q x) := by
    apply Or.congr
    · -- Prove (∀ᶠ x in ↑f, ¬p x) ↔ (¬∀ᶠ x in ↑f, p x)
      exact Ultrafilter.eventually_not
    · -- Prove (∀ᶠ x in ↑f, q x) ↔ (∀ᶠ x in ↑f, q x)
      exact Iff.refl
  _ ↔ ((∀ᶠ (x : α) in ↑f, p x) → ∀ᶠ (x : α) in ↑f, q x) := by
    rw [imp_iff_not_or]
```

**lean_error:** tail step 1/15 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.0s, verify 0.7s, in=768, out=688)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.7s, verify 0.9s, in=1135, out=2386)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [imp_iff_not_or, eventually_not] using
  (Ultrafilter.eventually_or (f := f) (p := fun x => ¬ p x) (q := q))
```

**lean_error:** tail step 1/2 ('simpa [imp_iff_not_or, eventually_not] using'): <stdin>:1:44: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 147.7s, verify 0.1s, in=1076, out=18615)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) := by
    apply Filter.Eventually.congr'
    intro x
    exact imp_iff_not_or
  _ ↔ ((∀ᶠ x in ↑f, ¬p x) ∨ (∀ᶠ x in ↑f, q x)) := by
    rw [Ultrafilter.eventually_or]
  _ ↔ ((¬∀ᶠ x in ↑f, p x) ∨ (∀ᶠ x in ↑f, q x)) := by
    have h : (∀ᶠ x in ↑f, ¬p x) ↔ (¬∀ᶠ x in ↑f, p x) := by rw [Ultrafilter.eventually_not]
    apply Iff.congr_right (fun x => x ∨ (∀ᶠ x in ↑f, q x)) h
  _ ↔ ((∀ᶠ x in ↑f, p x) → (∀ᶠ x in ↑f, q x)) := by
    apply Iff.symm
    exact imp_iff_not_or
```

**lean_error:** tail step 1/13 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=1020, out=502)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not, imp_iff_not_or]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not, imp_iff_not_or]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.6s, verify 0.3s, in=1107, out=1817)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

**lean_error:** tail step 1/1 ('simpa [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]'): tactic 'simp' failed, nested error:

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 80.2s, verify 0.1s, in=1117, out=9167)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) := by
  apply Filter.eventually_congr'
  intro x
  exact imp_iff_not_or

have h₂ : (∀ᶠ x in ↑f, ¬p x ∨ q x) ↔ ((∀ᶠ x in ↑f, ¬p x) ∨ (∀ᶠ x in ↑f, q x)) := by
  apply Ultrafilter.eventually_or

have h₃ : ((∀ᶠ x in ↑f, ¬p x) ∨ (∀ᶠ x in ↑f, q x)) ↔ (¬∀ᶠ x in ↑f, p x ∨ ∀ᶠ x in ↑f, q x) := by
  constructor
  · intro h
    cases h with
    | inl h =>
      have h₁ : ¬∀ᶠ x in ↑f, p x := by
        rw [Ultrafilter.eventually_not]
        exact h
      exact Or.inl h₁
    | inr h =>
      exact Or.inr h
  · intro h
    cases h with
    | inl h =>
      have h₁ : ∀ᶠ x in ↑f, ¬p x := by
        rw [Ultrafilter.eventually_not]
        exact h
      exact Or.inl h₁
    | inr h =>
      exact Or.inr h

have h₄ : (¬∀ᶠ x in ↑f, p x ∨ ∀ᶠ x in ↑f, q x) ↔ ((∀ᶠ x in ↑f, p x) → ∀ᶠ x in ↑f, q x) := by
  constructor
  · intro h
    cases h with
    | inl h =>
      intro h₂
      exact h h₂
    | inr h =>
      intro h₂
      exact h
  · intro h
    by_cases h₂ : ∀ᶠ x in ↑f, p x
    · have h₃ : ∀ᶠ x in ↑f, q x := h h₂
      exact Or.inr h₃
    · exact Or.inl h₂

have h_main : (∀ᶠ x in ↑f, p x → q x) ↔ ((∀ᶠ x in ↑f, p x) → ∀ᶠ x in ↑f, q x) := by
  calc
    (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) := h₁
    _ ↔ ((∀ᶠ x in ↑f, ¬p x) ∨ (∀ᶠ x in ↑f, q x)) := h₂
    _ ↔ (¬∀ᶠ x in ↑f, p x ∨ ∀ᶠ x in ↑f, q x) := h₃
    _ ↔ ((∀ᶠ x in ↑f, p x) → ∀ᶠ x in ↑f, q x) := h₄

exact h_main
```

**lean_error:** tail step 1/48 ('have h₁ : (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) := by'): <stdin>:1:66: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.6s, in=1039, out=974)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [show (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) by
  apply Filter.eventually_congr
  intro x
  rw [imp_iff_not_or]]
rw [Ultrafilter.eventually_or]
rw [Ultrafilter.eventually_not]
rw [←imp_iff_not_or]
```

**lean_error:** tail step 1/7 ('rw [show (∀ᶠ x in ↑f, p x → q x) ↔ (∀ᶠ x in ↑f, ¬p x ∨ q x) by'): <stdin>:1:62: unexpected end of input; expected '{'
