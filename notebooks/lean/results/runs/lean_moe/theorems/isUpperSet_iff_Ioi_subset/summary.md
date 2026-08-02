# isUpperSet_iff_Ioi_subset   (k=0, 1 tactics total)

file: `Mathlib/Order/UpperLower/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [isUpperSet_iff_forall_lt, subset_def, @forall_swap (_ ∈ s)]
```

**True premises at k:** `isUpperSet_iff_forall_lt`, `Set.subset_def`, `forall_swap`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=343, out=1417)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro hs a ha b hb
  exact hs ha (le_of_lt hb)
· intro h a b ha hle
  rcases lt_or_eq_of_le hle with hlt | rfl
  · exact h ha hlt
  · exact ha
```

**lean_error:** tail step 2/7 ('· intro hs a ha b hb'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 74.3s, verify 0.2s, in=283, out=8664)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  intro a ha
  intro b hb
  have hab : a ≤ b := le_of_lt hb
  exact h hab ha
· intro h
  intro a b hab hsa
  by_contra hb
  have hne : a ≠ b := by
    intro h_eq
    have h_eq' : b = a := by rw [h_eq]
    rw [h_eq'] at hb
    exact hb hsa
  have hab' : a < b := lt_of_le_of_ne hab hne
  have hbI : b ∈ Ioi a := exact hab'
  have hI : Ioi a ⊆ s := h a hsa
  have hbs : b ∈ s := hI hbI
  exact hb hbs
```

**lean_error:** tail step 2/19 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.2s, in=279, out=614)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h a ha b hb
  apply h ha (le_of_lt hb)
· intro h a ha b hab
  cases' lt_or_eq_of_le hab with hlt heq
  · have : b ∈ Ioi a := hlt
    exact h ha this
  · rw [heq]
    exact ha
```

**lean_error:** tail step 2/9 ('· intro h a ha b hb'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.9s, verify 0.2s, in=828, out=3345)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro hs a ha b hb
    exact (isUpperSet_iff_forall_lt.mp hs) hb ha
  · intro h
    refine (isUpperSet_iff_forall_lt.mpr ?_)
    intro a b hab ha
    have hsub : Ioi a ⊆ s := h ha
    exact hsub hab
```

**lean_error:** tail step 2/8 ('· intro hs a ha b hb'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 117.9s, verify 0.3s, in=766, out=13612)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
constructor
· -- Prove the forward direction: (∀ ⦃a b, a < b → a ∈ s → b ∈ s) → (∀ ⦃a, a ∈ s → Ioi a ⊆ s)
  intro h
  intro a ha
  have h₂ : Ioi a ⊆ s := by
    apply Set.subset_def
    intro x hx
    have h₃ : ∀ ⦃b a : α⦄, a < b → a ∈ s → b ∈ s := by
      exact forall_swap h
    have h₄ : a < x → a ∈ s → x ∈ s := h₃ x a
    have h₅ : x ∈ s := h₄ hx ha
    exact h₅
· -- Prove the backward direction: (∀ ⦃a, a ∈ s → Ioi a ⊆ s) → (∀ ⦃a b, a < b → a ∈ s → b ∈ s)
  intro h
  intro a b hab ha
  have h₂ : Ioi a ⊆ s := h a ha
  have h₃ : ∀ x, x ∈ Ioi a → x ∈ s := by
    rw [Set.subset_def] at h₂
    exact h₂
  have h₄ : b ∈ Ioi a := hab
  have h₅ : b ∈ s := h₃ b h₄
  exact h₅
```

**lean_error:** tail step 3/23 ('· -- Prove the forward direction: (∀ ⦃a b, a < b → a ∈ s → b ∈ s) → (∀ ⦃a, a ∈ s → Ioi a ⊆ s)'): <stdin>:1:93: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.3s, in=733, out=870)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
simp [Set.subset_def, Set.mem_Ioi]
exact forall_swap (fun a b => a < b → a ∈ s → b ∈ s)
```

**lean_error:** tail step 3/3 ('exact forall_swap (fun a b => a < b → a ∈ s → b ∈ s)'): function expected at

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=1393, out=1376)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Set.subset_def, Ioi, Set.mem_setOf_eq, forall_swap, imp_left_comm] using (isUpperSet_iff_forall_lt (s:=s))
```

**lean_error:** tail step 1/1 ('simpa [Set.subset_def, Ioi, Set.mem_setOf_eq, forall_swap, imp_left_comm] using (isUpperSet_iff_forall_lt (s:=s))'): unknown identifier 'imp_left_comm'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 114.7s, verify 0.1s, in=1324, out=13116)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem isUpperSet_iff_Ioi_subset {α : Type u_1} [PartialOrder α] (s : Set α) :
    IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s :=
  by
    have h₁ : IsUpperSet s ↔ (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s) := isUpperSet_iff_forall_lt
    rw [h₁]
    constructor
    · -- Prove the forward direction: (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s) → (∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s)
      intro h
      intro a ha
      have h₂ : Ioi a ⊆ s := by
        intro b hb
        -- Unfold the definition of Ioi to get a < b from hb : b ∈ Ioi a
        have hab : a < b := by
          dsimp [Ioi] at hb
          exact hb
        -- Apply h to get b ∈ s
        exact h a b hab ha
      exact h₂
    · -- Prove the backward direction: (∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s) → (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s)
      intro h
      intro a b hab ha
      -- Since a ∈ s, we have Ioi a ⊆ s by h
      have h₂ : Ioi a ⊆ s := h a ha
      -- Since a < b, we have b ∈ Ioi a
      have h₃ : b ∈ Ioi a := by
        dsimp [Ioi]
        exact hab
      -- Therefore, b ∈ s because Ioi a ⊆ s
      exact h₂ h₃
```

**lean_error:** tail step 1/29 ('theorem isUpperSet_iff_Ioi_subset {α : Type u_1} [PartialOrder α] (s : Set α) :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 17.1s, verify 0.3s, in=1256, out=1891)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
constructor
· intro h a ha b hb
  exact h hb ha
· intro h a b hab ha
  exact h ha (Set.mem_Ioi.mpr hab)
```

**lean_error:** tail step 3/6 ('· intro h a ha b hb'): unsolved goals

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.2s, in=1314, out=2242)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
  · intro hs a ha b hb
    have hlt := (isUpperSet_iff_forall_lt (s:=s)).1 hs
    exact hlt hb ha
  · intro h
    apply (isUpperSet_iff_forall_lt (s:=s)).2
    intro a b hab ha
    have hsub := h ha
    exact hsub hab
```

**lean_error:** tail step 2/9 ('· intro hs a ha b hb'): unsolved goals

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 111.3s, verify 0.1s, in=1394, out=12847)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isUpperSet_iff_forall_lt
constructor
  · intro h
    intro a ha
    apply Set.subset_def
    intro b hb
    have h2 : (∀ ⦃b : α⦄, ∀ ⦃a : α⦄, a < b → a ∈ s → b ∈ s) := by
      have h3 : (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s) ↔ (∀ ⦃b : α⦄, ∀ ⦃a : α⦄, a < b → a ∈ s → b ∈ s) := by
        apply forall_swap
      exact (h3.mp h)
    have h4 : a < b → a ∈ s → b ∈ s := h2 b a
    have h5 : a < b := by simpa [Set.mem_Ioi] using hb
    have h6 : a ∈ s := ha
    have h7 : b ∈ s := h4 h5 h6
    exact h7
  · intro h
    have h2 : (∀ ⦃b : α⦄, ∀ ⦃a : α⦄, a < b → a ∈ s → b ∈ s) := by
      intro b
      intro a
      hab ha
      have h3 : Ioi a ⊆ s := h a ha
      have h4 : b ∈ Ioi a := by
        exact Set.mem_Ioi.mpr hab
      have h5 : b ∈ s := h3 h4
      exact h5
    have h3 : (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s) := by
      have h4 : (∀ ⦃b : α⦄, ∀ ⦃a : α⦄, a < b → a ∈ s → b ∈ s) ↔ (∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s) := by
        apply forall_swap
      exact (h4.mpr h2)
    exact h3
```

**lean_error:** tail step 1/30 ('apply isUpperSet_iff_forall_lt'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.2s, in=1271, out=509)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUpperSet_iff_forall_lt]
rw [Set.subset_def]
simp [Set.mem_Ioi]
rw [forall_swap]
simp [imp_comm]
```

**lean_error:** tail step 2/5 ('rw [Set.subset_def]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
