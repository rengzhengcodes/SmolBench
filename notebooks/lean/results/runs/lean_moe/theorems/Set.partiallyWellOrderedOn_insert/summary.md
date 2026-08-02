# Set.partiallyWellOrderedOn_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, partiallyWellOrderedOn_union,
  partiallyWellOrderedOn_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.partiallyWellOrderedOn_union`, `Set.partiallyWellOrderedOn_singleton`, `true_and_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=353, out=1356)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (partiallyWellOrderedOn_insert (s:=s) (a:=a) (r:=r))
```

**lean_error:** tail step 1/1 ('simpa using (partiallyWellOrderedOn_insert (s:=s) (a:=a) (r:=r))'): invalid argument name 's' for function

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 224.5s, verify 0.1s, in=295, out=31410)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem partiallyWellOrderedOn_insert (ι : Type u_1) (α : Type u_2) (β : Type u_3) (γ : Type u_4) (π : ι → Type u_5) (r : α → α → Prop) (r' : β → β → Prop) (f : α → β) (s t : Set α) (a : α) (inst✝ : IsRefl α r) :
    PartiallyWellOrderedOn (insert a s) r ↔ PartiallyWellOrderedOn s r := by
  have h_main : (PartialOrder r ∧ WellFoundedOn r (insert a s)) ↔ (PartialOrder r ∧ WellFoundedOn r s) := by
    constructor
    · -- →: (PartialOrder r ∧ WellFoundedOn r (insert a s)) → (PartialOrder r ∧ WellFoundedOn r s)
      intro h
      have h₁ : PartialOrder r := h.1
      have h₂ : WellFoundedOn r (insert a s) := h.2
      constructor
      · -- Prove PartialOrder r
        exact h₁
      · -- Prove WellFoundedOn r s
        have h₃ : WellFoundedOn r s := by
          rw [Set.WellFounded.iff_isMinimal]
          intro t ht hne
          have h₄ : t ⊆ insert a s := by
            exact Set.subset_trans ht (Set.subset_insert _)
          have h₅ : ∃ m ∈ t, ∀ a' ∈ t, r a' m → a' = m := by
            apply Set.WellFounded.isMinimal
            · exact h₂
            · exact h₄
            · exact hne
          obtain ⟨m, hm, hmin⟩ := h₅
          exact ⟨m, hm, hmin⟩
        exact h₃
    · -- ←: (PartialOrder r ∧ WellFoundedOn r s) → (PartialOrder r ∧ WellFoundedOn r (insert a s))
      intro h
      have h₁ : PartialOrder r := h.1
      have h₂ : WellFoundedOn r s := h.2
      constructor
      · -- Prove PartialOrder r
        exact h₁
      · -- Prove WellFoundedOn r (insert a s)
        have h₃ : WellFoundedOn r (insert a s) := by
          rw [Set.WellFounded.iff_isMinimal]
          intro t ht hne
          by_cases ha : a ∈ t
          · -- Case: a ∈ t
            have h₄ : t ⊆ insert a s := ht
            -- Now, we need to find a minimal element in t
            if h : t \ {a} = ∅ then
              -- Subcase: t = {a}
              have h₅ : t = {a} := by
                apply Set.Subset.antisymm
                · -- Show t ⊆ {a}
                  intro x hx
                  by_contra h₆
                  -- If x ≠ a, then x ∈ t \ {a}
                  have h₇ : x ∈ t \ {a} := by
                    exact ⟨hx, by simp_all [Set.mem_singleton_iff]⟩
                  rw [h] at h₇
                  exact Set.not_mem_empty x h₇
                · -- Show {a} ⊆ t
                  intro x hx
                  simp only [Set.mem_singleton_iff] at hx ⊢
                  exact ha
              -- Then a is minimal in t
              have h₆ : ∃ m ∈ t, ∀ a' ∈ t, r a' m → a' = m := by
                refine' ⟨a, by simp [h₅], _⟩
                intro a' hₐ' hra
                have h₇ : a' = a := by
                  simp only [Set.mem_singleton_iff] at hₐ' ⊢
                  <;> tauto
                simp_all
              exact h₆
            else
              -- Subcase: t \ {a} ≠ ∅
              have h₅ : t \ {a} ⊆ s := by
                intro x hx
                have h₆ : x ∈ t := hx.1
                have h₇ : x ≠ a := hx.2
                have h₈ : x ∈ insert a s := ht h₆
                cases h₈ with
                | inl h₈ =>
                  exact h₈
                | inr h₈ =>
                  have h₉ : x = a := h₈
                  contradiction
              have h₆ : WellFoundedOn r s := h₂
              have h₇ : ∃ m ∈ t \ {a}, ∀ a' ∈ t \ {a}, r a' m → a' = m := by
                apply Set.WellFounded.isMinimal
                · exact h₆
                · exact h₅
                · exact (by simp [h])
              obtain ⟨m, hm, hmin⟩ := h₇
              have h₈ : m ∈ t := by
                exact hm.1
              -- Now, we need to show that either m is minimal in t or a is minimal in t
              by_cases h₉ : (∀ a' ∈ t, r a' m → a' = m)
              · -- m is minimal in t
                exact ⟨m, h₈, h₉⟩
              · -- m is not minimal in t, so we show a is minimal in t
                have h₁₀ : ∃ a' ∈ t, r a' m ∧ a' ≠ m := by
                  push_neg at h₉
                  <;> simp_all [Set.mem_setOf_eq]
                  <;> tauto
                obtain ⟨x, hx, hx'⟩ := h₁₀
                have h₁₁ : x = a := by
                  by_contra h₁₂
                  -- If x ≠ a, then x ∈ t \ {a}
                  have h₁₃ : x ∈ t \ {a} := by
                    exact ⟨hx.1, by simp_all [Set.mem_singleton_iff]⟩
                  have h₁₄ : x = m := by
                    have h₁₅ : ∀ a' ∈ t \ {a}, r a' m → a' = m := hmin
                    have h₁₆ : r x m := hx.2.1
                    have h₁₇ : x ∈ t \ {a} := h₁₃
                    have h₁₈ : x = m := h₁₅ x h₁₇ h₁₆
                    exact h₁₈
                  -- But we have x ≠ m
                  exact hx' h₁₄
                -- Now show that a is minimal in t
                have h₁₂ : ∃ m' ∈ t, ∀ a' ∈ t, r a' m' → a' = m' := by
                  refine' ⟨a, by simp [h₁₁], _⟩
                  intro a' hₐ' hra
                  by_contra h₁₃
                  -- If a' ≠ a, then derive contradiction
                  have h₁₄ : a' ∈ t \ {a} := by
                    exact ⟨hₐ'.1, by simp_all [Set.mem_singleton_iff]⟩
                  have h₁₅ : a' = m := by
                    have h₁₆ : r a' a := hra
                    have h₁₇ : r a m := by
                      have h₁₈ : x = a := h₁₁
                      have h₁₉ : r x m := hx.2.1
                      simp_all [h₁₈]
                    have h₁₈ : r a' m := by
                      -- Transitivity: r a' a and r a m implies r a' m
                      have h₁₉ : Transitive r := h₁.trans
                      exact h₁₉ h₁₆ h₁₇
                    have h₁₉ : ∀ a'' ∈ t \ {a}, r a'' m → a'' = m := hmin
                    have h₂₀ : a' ∈ t \ {a} := h₁₄
                    have h₂₁ : r a' m := h₁₈
                    have h₂₂ : a' = m := h₁₉ a' h₂₀ h₂₁
                    exact h₂₂
                  have h₁₆ : r a a' := by
                    have h₁₇ : x = a := h₁₁
                    have h₁₈ : r x m := hx.2.1
                    have h₁₉ : a' = m := h₁₅
                    have h₂₀ : r a m := by
                      simp_all [h₁₇]
                      <;> assumption
                    have h₂₁ : a' = m := h₁₅
                    rw [h₂₁] at h₂₀
                    exact h₂₀
                  have h₁₇ : Antisymmetric r := h₁.antisymm
                  have h₁₈ : a' = a := h₁₇ h₁₆ h₁₇
                  exact h₁₃ h₁₈
                exact h₁₂
          · -- Case: a ∉ t
            have h₄ : t ⊆ s := by
              intro x hx
              have h₅ : x ∈ t := hx
              have h₆ : x ∈ insert a s := ht h₅
              cases h₆ with
              | inl h₆ =>
                exact h₆
              | inr h₆ =>
                have h₇ : x = a := h₆
                contradiction
            have h₅ : WellFoundedOn r s := h₂
            have h₆ : ∃ m ∈ t, ∀ a' ∈ t, r a' m → a' = m := by
              apply Set.WellFounded.isMinimal
              · exact h₅
              · exact h₄
              · exact hne
            obtain ⟨m, hm, hmin⟩ := h₆
            exact ⟨m, hm, hmin⟩
        exact h₃
  exact h_main
```

**lean_error:** tail step 1/168 ("theorem partiallyWellOrderedOn_insert (ι : Type u_1) (α : Type u_2) (β : Type u_3) (γ : Type u_4) (π : ι → Type u_5) (r : α → α → Prop) (r' : β → β → Prop) (f : α → β) (s t : Set α) (a : α) (inst✝ : IsRefl α r) :"): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.3s, in=295, out=793)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  apply PartiallyWellOrderedOn.mono h
  intro x hx
  simp only [Set.mem_insert_iff] at hx
  exact hx.2
· intro h
  apply PartiallyWellOrderedOn.insert h
```

**lean_error:** tail step 2/8 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=935, out=1374)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Set.singleton_union]
simpa [Set.partiallyWellOrderedOn_union, true_and_iff]
```

**lean_error:** tail step 2/2 ('simpa [Set.partiallyWellOrderedOn_union, true_and_iff]'): tactic 'assumption' failed

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=895, out=1456)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
<;> rfl
```

**lean_error:** tail step 1/5 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.3s, in=860, out=527)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [partiallyWellOrderedOn_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=1286, out=1003)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Set.singleton_union, Set.partiallyWellOrderedOn_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simpa [Set.singleton_union, Set.partiallyWellOrderedOn_union, true_and_iff]'): tactic 'assumption' failed

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.0s, verify 0.1s, in=1251, out=3531)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleton_union]
rw [partiallyWellOrderedOn_union]
constructor
  · intro h; exact h.2
  · intro h; exact ⟨partiallyWellOrderedOn_singleton a, h⟩
```

**lean_error:** tail step 1/5 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.3s, in=1199, out=350)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [partiallyWellOrderedOn_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=1257, out=1508)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Set.singleton_union] using
    (Set.partiallyWellOrderedOn_union (s := ({a} : Set α)) (t := s) (r := r))
```

**lean_error:** tail step 1/2 ('simpa [Set.singleton_union] using'): <stdin>:1:33: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.7s, verify 0.3s, in=1309, out=4653)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union]
rw [partiallyWellOrderedOn_union]
rw [show {a}.PartiallyWellOrderedOn r ↔ True by
  constructor
  · intro h; trivial
  · exact partiallyWellOrderedOn_singleton a]
rw [true_and_iff]
<;> rfl
```

**lean_error:** tail step 3/8 ('rw [show {a}.PartiallyWellOrderedOn r ↔ True by'): <stdin>:1:47: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.3s, in=1215, out=576)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [partiallyWellOrderedOn_singleton]'): tactic 'rewrite' failed, equality or iff proof expected
