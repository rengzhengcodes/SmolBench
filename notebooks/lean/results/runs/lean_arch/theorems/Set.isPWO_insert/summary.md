# Set.isPWO_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.isPWO_union`, `Set.isPWO_singleton`, `true_and_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | · | · |
| `hint:3` | ✘ | ✓ | · |
| `noise:3` | ✘ | · | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 13.6s, verify 0.2s, in=284, out=450)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    rw [IsPWO] at *
    intro t
    specialize h (t \ {a})
    cases h
    · left
      intro x hx
      cases hx
      · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ)
      · exact h_ᾰ hx
    · cases h
      · right
        refine' ⟨a, h_ᾰ, _⟩
        intro x hx
        cases hx
        · exact h_ᾰ_1 hx
        · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ_2)
      · right
        refine' ⟨h_ᾰ, _⟩
        intro x hx
        cases hx
        · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ_1)
        · exact h_ᾰ_2 hx
  · intro h
    rw [IsPWO] at *
    intro t
    cases (em (a ∈ t))
    · specialize h (t \ {a})
      cases h
      · left
        intro x hx
        cases hx
        · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ)
        · exact h_ᾰ hx
      · cases h
        · right
          refine' ⟨a, h_ᾰ, _⟩
          intro x hx
          cases hx
          · exact h_ᾰ_1 hx
          · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ_2)
        · right
          refine' ⟨h_ᾰ, _⟩
          intro x hx
          cases hx
          · exact lt_of_lt_of_le ha (le_of_mem h_ᾰ_1)
          · exact h_ᾰ_2 hx
    · specialize h t
      cases h
      · left
        intro x hx
        exact h_ᾰ hx
      · right
        refine' ⟨h_ᾰ, _⟩
        intro x hx
        exact h_ᾰ_1 hx
```

**lean_error:** tail step 2/57 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=258, out=79)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPWO_iff_WF_and_has_min, IsPWO_iff_WF_and_has_min, and_congr_right_iff]
intro h₁ h₂
exact ⟨min_insert s a, fun ⟨b, hb⟩ ↦ by simpa [h₂.min_mem] using h₁.min_mem (insert_subset.2 ⟨hb, h₂.subset⟩)⟩
```

**lean_error:** tail step 1/3 ('rw [IsPWO_iff_WF_and_has_min, IsPWO_iff_WF_and_has_min, and_congr_right_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 48.0s, verify 0.1s, in=273, out=2873)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
exact is_pwo_subset (subset_insert s) h
intro h
apply is_pwo.union
exact h
apply is_pwo_singleton a
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=747, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union],
rw isPWO_union,
rw isPWO_singleton,
apply true_and_iff
```

**lean_error:** tail step 1/4 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=723, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union]
simp [isPWO_union, isPWO_singleton, true_and_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=736, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union]
simp [isPWO_union, isPWO_singleton, true_and_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1149, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union],
rw isPWO_union,
rw isPWO_singleton,
apply true_and_iff
```

**lean_error:** tail step 1/4 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1121, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp_rw [isPWO_union, isPWO_singleton, true_and_iff]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=1138, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp [isPWO_union, isPWO_singleton, true_and_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1173, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union],
rw isPWO_union,
rw isPWO_singleton,
exact true_and_iff
```

**lean_error:** tail step 1/4 ('rw [← singleton_union],'): <stdin>:1:22: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.5s, verify 0.2s, in=1194, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp [isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=1162, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union]
simp [isPWO_union, isPWO_singleton, true_and_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```
