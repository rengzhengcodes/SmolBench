# covBy_sup_of_inf_covBy_of_inf_covBy_right   (k=1, 2 tactics total)

file: `Mathlib/Order/ModularLattice.lean`  

**Ground-truth tail (from k):**
```lean
exact fun ha hb => covBy_sup_of_inf_covBy_of_inf_covBy_left hb ha
```

**True premises at k:** `covBy_sup_of_inf_covBy_of_inf_covBy_left`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.4s, verify 0.1s, in=318, out=3083)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h₁ h₂
exact
  IsWeakUpperModularLattice.covby_sup (a:=b) (b:=a) (c:=b ⊔ a)
    (by
      exact le_sup_left)
    h₁
```

**lean_error:** tail step 2/6 ('exact'): <stdin>:1:5: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 153.4s, verify 0.1s, in=271, out=20403)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem problem {α : Type u_1} [Lattice α] [IsWeakUpperModularLattice α] (a b : α)
    (h₁ : b ⊓ a ⋖ a) (h₂ : b ⊓ a ⋖ b) : b ⋖ b ⊔ a := by
  have h₃ : b < b ⊔ a := by
    by_contra h
    have h₄ : b ⊔ a = b := by
      have h₅ : b ⊔ a ≤ b := by
        -- Since b ≤ b ⊔ a always, if not b < b ⊔ a, then b ⊔ a ≤ b
        have h₅₁ : b ≤ b ⊔ a := le_sup_left
        have h₅₂ : b ⊔ a ≤ b := by
          -- Since we assumed ¬(b < b ⊔ a), and b ≤ b ⊔ a, we have b ⊔ a ≤ b
          exact le_of_not_lt h
        exact h₅₂
      -- Now, b ⊔ a ≤ b implies a ≤ b
      have h₆ : a ≤ b := by
        calc
          a ≤ b ⊔ a := le_sup_right
          _ ≤ b := h₅
      -- Then b ⊓ a = a
      have h₇ : b ⊓ a = a := by
        rw [inf_eq_right h₆]
      -- But h₁ says b ⊓ a ⋖ a, which would mean a ⋖ a, impossible
      have h₈ : b ⊓ a ⋖ a := h₁
      rw [h₇] at h₈
      exact lt_irrefl a h₈
    -- Now we have b ⊔ a = b, but we also have b ≤ b ⊔ a, so b = b ⊔ a
    -- This leads to a contradiction with h₁ as above
    have h₉ : b ⊓ a = a := by
      rw [h₄]
      <;> simp [inf_comm]
    have h₁₀ : b ⊓ a ⋖ a := h₁
    rw [h₉] at h₁₀
    exact lt_irrefl a h₁₀
  
  have h_main : ∀ (z : α), b ≤ z → z ≤ b ⊔ a → b = z ∨ z = b ⊔ a := by
    intro z hz1 hz2
    have h₄ : b ⊓ a ≤ z ⊓ a := by
      apply inf_le_of_le_left
      · -- b ⊓ a ≤ z
        calc
          b ⊓ a ≤ b := inf_le_left
          _ ≤ z := hz1
      · -- b ⊓ a ≤ a
        exact inf_le_right
    have h₅ : z ⊓ a ≤ a := inf_le_right
    have h₆ : z ⊓ a = b ⊓ a ∨ z ⊓ a = a := by
      have h₆₁ : b ⊓ a ⋖ a := h₁
      have h₆₂ : b ⊓ a ≤ z ⊓ a := h₄
      have h₆₃ : z ⊓ a ≤ a := h₅
      have h₆₄ : z ⊓ a = b ⊓ a ∨ z ⊓ a = a := by
        -- Use the fact that if x ⋖ y and x ≤ z ≤ y, then x = z or z = y
        have h₆₅ : b ⊓ a = z ⊓ a ∨ z ⊓ a = a := by
          apply h₆₁.2 h₆₂ h₆₃
        -- But h₆₁.2 gives b ⊓ a = z ⊓ a or z ⊓ a = a, which is the same as z ⊓ a = b ⊓ a or z ⊓ a = a
        cases h₆₅ with
        | inl h₆₅ =>
          exact Or.inl (by rw [h₆₅])
        | inr h₆₅ =>
          exact Or.inr h₆₅
      exact h₆₄
    cases h₆ with
    | inl h₆ =>
      -- Case: z ⊓ a = b ⊓ a
      have h₇ : b ≤ z := hz1
      -- Use modularity: since b ≤ z, we have b ⊔ (a ⊓ z) = (b ⊔ a) ⊓ z
      have h₈ : b ⊔ (a ⊓ z) = (b ⊔ a) ⊓ z := by
        have h₈₁ : b ≤ z := hz1
        have h₈₂ : b ⊔ (a ⊓ z) = (b ⊔ a) ⊓ z := by
          -- Apply the modular law (wmod)
          have h₈₃ : b ⊔ (a ⊓ z) = (b ⊔ a) ⊓ z := by
            -- Use the weak upper modular law: x ≤ z → x ⊔ (y ⊓ z) = (x ⊔ y) ⊓ z
            -- Here, x = b, y = a, z = z, and we need x ≤ z, which is b ≤ z
            have h₈₄ : b ⊔ (a ⊓ z) = (b ⊔ a) ⊓ z := by
              apply Eq.symm
              apply IsWeakUpperModularLattice.wmod inst✝
              <;> assumption
            exact h₈₄
          exact h₈₃
        exact h₈₂
      -- Now, a ⊓ z = z ⊓ a = b ⊓ a (by h₆)
      have h₉ : a ⊓ z = b ⊓ a := by
        rw [h₆]
        <;> simp [inf_comm]
      -- So LHS becomes b ⊔ (b ⊓ a)
      have h₁₀ : b ⊔ (a ⊓ z) = b ⊔ (b ⊓ a) := by
        rw [h₉]
      -- And RHS becomes z (since z ≤ b ⊔ a, so (b ⊔ a) ⊓ z = z)
      have h₁₁ : (b ⊔ a) ⊓ z = z := by
        rw [inf_eq_right (by
          -- Prove z ≤ b ⊔ a
          exact hz2)]
      -- Therefore, b ⊔ (a ⊓ z) = z
      have h₁₂ : b ⊔ (a ⊓ z) = z := by
        linarith
      -- But b ⊔ (b ⊓ a) = b
      have h₁₃ : b ⊔ (b ⊓ a) = b := by
        rw [sup_inf_absorb b a]
      -- Hence, z = b
      have h₁₄ : z = b := by
        linarith
      exact Or.inl h₁₄
    | inr h₆ =>
      -- Case: z ⊓ a = a
      have h₇ : a ≤ z := by
        -- Since z ⊓ a = a, we have a ≤ z
        have h₇₁ : a ≤ z := by
          -- In a lattice, x ≤ y iff x ⊓ y = x
          have h₇₂ : z ⊓ a = a := h₆
          have h₇₃ : a ≤ z := by
            rw [le_iff_inf_eq_left] at *
            -- We need to show a ⊓ z = a
            have h₇₄ : a ⊓ z = z ⊓ a := by rw [inf_comm]
            rw [h₇₄, h₇₂]
            <;> simp
          exact h₇₃
        exact h₇₁
      -- Since b ≤ z and a ≤ z, we have b ⊔ a ≤ z
      have h₈ : b ⊔ a ≤ z := sup_le hz1 h₇
      -- But z ≤ b ⊔ a, so z = b ⊔ a
      have h₉ : z = b ⊔ a := by
        apply le_antisymm
        · exact h₈
        · exact hz2
      -- Therefore, z = b ⊔ a
      exact Or.inr h₉
  
  have h_final : b ⋖ b ⊔ a := by
    refine' ⟨h₃, _⟩
    intro z hz1 hz2
    have h₄ : b = z ∨ z = b ⊔ a := h_main z hz1 hz2
    cases h₄ with
    | inl h₄ =>
      exact Or.inl h₄
    | inr h₄ =>
      exact Or.inr h₄
  
  exact h_final
```

**lean_error:** tail step 1/133 ('theorem problem {α : Type u_1} [Lattice α] [IsWeakUpperModularLattice α] (a b : α)'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=263, out=516)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h₁ h₂
exact IsWeakUpperModularLattice.sup_cover_of_inf_cover h₁ h₂
```

**lean_error:** tail step 2/2 ('exact IsWeakUpperModularLattice.sup_cover_of_inf_cover h₁ h₂'): unknown constant 'IsWeakUpperModularLattice.sup_cover_of_inf_cover'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.7s, verify 0.1s, in=576, out=1780)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
intro h₁ h₂
have h₁' : b ⊓ a ⋖ a := by
  simpa [inf_comm] using h₁
have h₂' : b ⊓ a ⋖ b := by
  simpa [inf_comm] using h₂
simpa [sup_comm] using covBy_sup_of_inf_covBy_of_inf_covBy_left h₂' h₁'
```

**lean_error:** tail step 2/6 ("have h₁' : b ⊓ a ⋖ a := by"): <stdin>:1:26: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.5s, verify 0.2s, in=567, out=10509)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
intro h₃ h₄
have h₅ : b ⋖ b ⊔ a := covBy_sup_of_inf_covBy_of_inf_covBy_left h₂ h₁
rw [sup_comm] at h₅
exact h₅
```

**lean_error:** tail step 2/4 ('have h₅ : b ⋖ b ⊔ a := covBy_sup_of_inf_covBy_of_inf_covBy_left h₂ h₁'): unknown identifier 'h₂'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.1s, verify 0.1s, in=525, out=1392)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('apply covBy_sup_of_inf_covBy_of_inf_covBy_left'): tactic 'apply' failed, failed to unify
