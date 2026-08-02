# Set.isPWO_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.isPWO_union`, `Set.isPWO_singleton`, `true_and_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.9s, verify 0.2s, in=325, out=1620)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    exact h.mono (by
      intro x hx
      exact Set.mem_insert_of_mem _ hx)
  · intro h
    exact h.insert _
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 258.0s, verify 0.1s, in=268, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
⟨fun h => by
  intro t hts hs
  have h₂ : t ⊆ insert a s := by
    apply Set.subset_trans hs
    exact subset_insert s a
  have h₃ : ∃ m ∈ t, ∀ y ∈ t, ¬(y < m) := h h₂ hts
  obtain ⟨m, hm₁, hm₂⟩ := h₃
  exact ⟨m, hm₁, hm₂⟩,
fun h => by
  intro t hts
  by_cases ha : a ∈ t
  · -- Case: a ∈ t
    have h₃ : a ∈ t := ha
    set t' := t \ {a} with ht'
    by_cases h₄ : t' = ∅
    · -- Subcase: t' = ∅
      have h₅ : t = {a} := by
        apply Set.Subset.antisymm
        · -- t ⊆ {a}
          intro x hx
          have h₅₁ : x ∈ t := hx
          have h₅₂ : x ≠ a := by
            intro h₅₃
            have h
```

**lean_error:** tail step 1/24 ('⟨fun h => by'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.2s, in=267, out=605)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact h.mono (Set.subset_insert a s)
· intro h
  exact h.insert a
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=823, out=875)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Set.singleton_union, Set.isPWO_union]
```

**lean_error:** tail step 1/1 ('simpa [Set.singleton_union, Set.isPWO_union]'): tactic 'assumption' failed

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 28.3s, verify 0.1s, in=781, out=3233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  IsPWO (insert a s) = IsPWO ({a} ∪ s) := by rw [Set.singleton_union]
  _ ↔ (IsPWO {a} ∧ IsPWO s) := by rw [Set.isPWO_union]
  _ ↔ (True ∧ IsPWO s) := by
    have h : IsPWO ({a} : Set α) := Set.isPWO_singleton a
    rw [h]
  _ ↔ IsPWO s := by rw [true_and_iff]
```

**lean_error:** tail step 1/7 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.3s, in=751, out=595)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [isPWO_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=1259, out=1099)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff] using
  (Set.isPWO_union (s := ({a} : Set α)) (t := s))
```

**lean_error:** tail step 1/2 ('simpa [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff] using'): <stdin>:1:85: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 64.5s, verify 0.1s, in=1226, out=7536)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
IsPWO (insert a s) ↔ IsPWO s := by
  rw [singleton_union]
  rw [isPWO_union]
  have h : IsPWO ({a} : Set α) := isPWO_singleton
  have h₂ : IsPWO ({a} : Set α) ↔ True := by
    constructor
    · intro h; trivial
    · exact h
  rw [h₂]
  rw [true_and_iff]
```

**lean_error:** tail step 1/10 ('IsPWO (insert a s) ↔ IsPWO s := by'): <stdin>:1:1: unknown tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.3s, in=1172, out=544)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [isPWO_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.2s, in=1214, out=810)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simpa [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]'): tactic 'assumption' failed

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 106.7s, verify 0.2s, in=1285, out=12883)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleton_union]
rw [isPWO_union]
have h : IsPWO ({a} : Set α) := isPWO_singleton a
have h₁ : (IsPWO {a} ∧ IsPWO s) ↔ (True ∧ IsPWO s) := by
  constructor
  · intro h₂
    exact ⟨by trivial, h₂.2⟩
  · intro h₂
    exact ⟨h, h₂.2⟩
rw [h₁, true_and_iff]
<;> rfl
```

**lean_error:** tail step 1/11 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=1184, out=663)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 1/4 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
