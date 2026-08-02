# Finset.map_subtype_embedding_Ioi   (k=1, 2 tactics total)

file: `Mathlib/Order/LocallyFinite.lean`  

**Ground-truth tail (from k):**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.1 hx).le a.prop
```

**True premises at k:** `Finset.subtype_map_of_mem`, `Finset.mem_Ioi`, `LT.lt.le`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.4s, in=361, out=2850)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · intro hx
    rcases Finset.mem_map.1 hx with ⟨y, hy, rfl⟩
    simpa using hy
  · intro hx
    have hpx : p x := hp (le_of_lt hx) a.property
    refine Finset.mem_map.2 ?_
    refine ⟨⟨x, hpx⟩, ?_, rfl⟩
    simpa using hx
```

**lean_error:** tail step 3/10 ('· intro hx'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.5s, verify 0.3s, in=313, out=11003)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
rw [Finset.mem_map]
rw [Finset.mem_subtype]
simp [Embedding.subtype_apply]
constructor
· intro h
  obtain ⟨y, hy₁, hy₂⟩ := h
  have h₃ : x ∈ Ioi ↑a := by rw [hy₂]; exact hy₁
  exact h₃
· intro hx
  have h₁ : p x := by
    have h₂ : ↑a < x := hx
    have h₃ : ↑a ≤ x := by exact lt_le_iff_le.mpr h₂
    have h₄ : p (↑a) := a.prop
    exact hp h₃ h₄
  refine' ⟨⟨x, h₁⟩, hx, _⟩
  <;> simp
```

**lean_error:** tail step 3/17 ('rw [Finset.mem_subtype]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.4s, in=307, out=1472)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
constructor
· intro hx
  simp only [Finset.mem_map, Finset.mem_subtype] at hx
  rcases hx with ⟨⟨y, hy⟩, hxy, rfl⟩
  exact hxy
· intro hx
  have hpx : p x := hp (le_of_lt hx) a.property
  simp only [Finset.mem_map, Finset.mem_subtype]
  use ⟨x, hpx⟩
  constructor
  · exact hx
  · rfl
```

**lean_error:** tail step 3/13 ('· intro hx'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.9s, verify 2.7s, in=886, out=1640)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intro x hx
have hx' : (a : α) < x := (Finset.mem_Ioi).1 hx
have hle : (a : α) ≤ x := le_of_lt hx'
exact hp hle a.property
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 67.4s, verify 0.5s, in=869, out=8736)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : ∀ x ∈ (Ioi ↑a : Finset α), p x := by
  intro x hx
  simp only [Finset.mem_Ioi] at hx
  have h₂ : ↑a < x := hx
  have h₃ : ↑a ≤ x := by exact lt_le h₂
  have h₄ : p (↑a) := a.prop
  exact hp h₃ h₄
have h₂ : (Finset.subtype p (Ioi ↑a)).map (Embedding.subtype p) = Ioi ↑a := by
  calc
    (Finset.subtype p (Ioi ↑a)).map (Embedding.subtype p) = ((Ioi ↑a : Finset α).subtype p).map (Embedding.subtype p) := by rfl
    _ = (Ioi ↑a : Finset α) := by apply Finset.subtype_map_of_mem; exact h₁
    _ = Ioi ↑a := by rfl
exact h₂
```

**lean_error:** tail step 1/13 ('have h₁ : ∀ x ∈ (Ioi ↑a : Finset α), p x := by'): <stdin>:1:46: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.6s, in=837, out=536)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intro x hx
rw [Finset.mem_Ioi] at hx
apply hp
· exact LT.lt.le hx
· exact a.prop
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.6s, verify 0.4s, in=2019, out=1998)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
  intro x hx
  have hlt : (a : α) < x := (Finset.mem_Ioi).1 hx
  exact hp (le_of_lt hlt) a.property
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 15.5s, verify 0.1s, in=2044, out=1911)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : ∀ x ∈ (Ioi ↑a : Finset α), p x := by
  intro x hx
  have h₁ : (↑a : α) < x := by simpa [Finset.mem_Ioi] using hx
  have h₂ : p (↑a : α) := a.prop
  have h₃ : (↑a : α) ≤ x := lt_le h₁
  have h₄ : p x := hp h₃ h₂
  exact h₄
rw [Finset.subtype_map_of_mem h]
```

**lean_error:** tail step 1/8 ('have h : ∀ x ∈ (Ioi ↑a : Finset α), p x := by'): <stdin>:1:45: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.9s, verify 0.4s, in=1980, out=711)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intro x hx
rw [Finset.mem_Ioi] at hx
exact hp (LT.lt.le hx) a.prop
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.4s, verify 0.1s, in=1906, out=2543)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [subtype_Ioi_eq] using
  (Finset.subtype_map_of_mem (p:=p) (s:=Ioi (a : α)) (by
    intro x hx
    have hx' : (a : α) < x := (Finset.mem_Ioi).1 hx
    have hax : (a : α) ≤ x := (le_of_lt hx')
    exact hp hax a.property))
```

**lean_error:** tail step 1/6 ('simpa [subtype_Ioi_eq] using'): <stdin>:1:28: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.0s, verify 0.1s, in=2197, out=5033)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Finset.map_subtype_embedding_Ioi {α : Type u_1} {β : Type u_2} [Preorder α] {p : α → Prop} [DecidablePred p] [LocallyFiniteOrderTop α] (a : Subtype p) (hp : ∀ ⦃a x : α⦄, a ≤ x → p a → p x) :
    map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a := by
  have h_main : (∀ x ∈ Finset.Ioi (↑a), p x) := by
    intro x hx
    have h₁ : (↑a : α) < x := Finset.mem_Ioi.mp hx
    have h₂ : (↑a : α) ≤ x := by exact_le_of_lt h₁
    have h₃ : p (↑a : α) := a.prop
    have h₄ : p x := hp h₂ h₃
    exact h₄
  
  have h_final : map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a := by
    have h₁ : (Finset.subtype p (Finset.Ioi (↑a))).map (Embedding.subtype p) = Finset.Ioi (↑a) := by
      apply Finset.subtype_map_of_mem
      intro x hx
      exact h_main x hx
    -- Simplify the left-hand side to match the goal
    calc
      map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = (Finset.subtype p (Finset.Ioi (↑a))).map (Embedding.subtype p) := rfl
      _ = Finset.Ioi (↑a) := h₁
      _ = Ioi ↑a := rfl
  
  exact h_final
```

**lean_error:** tail step 1/20 ('theorem Finset.map_subtype_embedding_Ioi {α : Type u_1} {β : Type u_2} [Preorder α] {p : α → Prop} [DecidablePred p] [LocallyFiniteOrderTop α] (a : Subtype p) (hp : ∀ ⦃a x : α⦄, a ≤ x → p a → p x) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.3s, in=1970, out=509)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intro x hx
rw [Finset.mem_Ioi] at hx
exact hp (LT.lt.le hx) a.2
```
