# Filter.isUnit_iff_singleton   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

**True premises at k:** `Filter.isUnit_iff`, `Group.isUnit`, `and_true_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=365, out=1302)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (Filter.isUnit_iff (f := f))
```

**lean_error:** tail step 1/1 ('simpa using (Filter.isUnit_iff (f := f))'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 85.6s, verify 0.2s, in=312, out=11740)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop
```

**final state (truncated):**
```
case mp
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
...
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=306, out=335)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Filter.isUnit_iff
```

**lean_error:** tail step 1/1 ('exact Filter.isUnit_iff'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.3s, in=896, out=1091)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h
    rcases (Filter.isUnit_iff (f:=f)).1 h with ⟨a, ha, _⟩
    exact ⟨a, ha⟩
  · rintro ⟨a, ha⟩
    have ha' : IsUnit a := Group.isUnit a
    exact (Filter.isUnit_iff (f:=f)).2 ⟨a, ha, ha'⟩
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 18.2s, verify 0.1s, in=833, out=2066)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h : IsUnit f ↔ (∃ a, f = pure a ∧ IsUnit a) := Filter.isUnit_iff f
rw [h]
constructor
· intro h
  obtain ⟨a, ha1, ha2⟩ := h
  exact ⟨a, ha1⟩
· intro h
  obtain ⟨a, ha⟩ := h
  have h₁ : IsUnit a := Group.isUnit a
  exact ⟨a, ha, h₁⟩
```

**lean_error:** tail step 1/10 ('have h : IsUnit f ↔ (∃ a, f = pure a ∧ IsUnit a) := Filter.isUnit_iff f'): function expected at

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.6s, verify 0.2s, in=793, out=463)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
simp [Group.isUnit]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.6s, in=1553, out=978)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
  · intro h
    rcases (Filter.isUnit_iff (f:=f)).1 h with ⟨a, ha, _⟩
    exact ⟨a, ha⟩
  · rintro ⟨a, ha⟩
    have ha' : IsUnit a := Group.isUnit a
    exact (Filter.isUnit_iff (f:=f)).2 ⟨a, ha, ha'⟩
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 46.2s, verify 0.4s, in=1502, out=5690)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
constructor
· intro h
  obtain ⟨a, ha₁, ha₂⟩ := h
  exact ⟨a, ha₁⟩
· intro h
  obtain ⟨a, ha⟩ := h
  have h₁ : IsUnit a := Group.isUnit a
  exact ⟨a, ha, h₁⟩
```

**lean_error:** tail step 3/9 ('· intro h'): unsolved goals

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.2s, in=1449, out=492)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
simp [Group.isUnit]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.6s, in=1497, out=1185)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
  · intro h
    rcases (Filter.isUnit_iff.mp h) with ⟨a, hfa, _⟩
    exact ⟨a, hfa⟩
  · rintro ⟨a, hfa⟩
    have ha : IsUnit a := Group.isUnit a
    exact (Filter.isUnit_iff.mpr ⟨a, hfa, ha⟩)
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 30.3s, verify 0.1s, in=1615, out=3465)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Filter.isUnit_iff_singleton {F : Type u_1} {α : Type u_2} {β : Type u_3} {γ : Type u_4} {δ : Type u_5} {ε : Type u_6}
    [Group α] [DivisionMonoid β] [FunLike F α β] [MonoidHomClass F α β]
    (f : F) : IsUnit f ↔ ∃ a, f = pure a := by
  have h_main : IsUnit f ↔ ∃ a, f = pure a := by
    rw [Filter.isUnit_iff]
    constructor
    · -- Prove the forward direction: (∃ a, f = pure a ∧ IsUnit a) → (∃ a, f = pure a)
      intro h
      obtain ⟨a, hfa, hunit⟩ := h
      exact ⟨a, hfa⟩
    · -- Prove the backward direction: (∃ a, f = pure a) → (∃ a, f = pure a ∧ IsUnit a)
      intro h
      obtain ⟨a, hfa⟩ := h
      have hunit : IsUnit a := Group.isUnit a
      exact ⟨a, hfa, hunit⟩
  exact h_main
```

**lean_error:** tail step 1/16 ('theorem Filter.isUnit_iff_singleton {F : Type u_1} {α : Type u_2} {β : Type u_3} {γ : Type u_4} {δ : Type u_5} {ε : Type u_6}'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.3s, verify 0.2s, in=1459, out=652)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
simp [Group.isUnit]
```
