# Std.RBNode.isOrdered_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [isOrdered_iff']
```

**True premises at k:** `Std.RBNode.isOrdered_iff'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=285, out=476)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [isOrdered, Ordered]
```

**lean_error:** tail step 1/1 ('simpa [isOrdered, Ordered]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 65.3s, verify 0.1s, in=230, out=7627)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor <;> intro h <;> exact h
```

**lean_error:** tail step 1/1 ('constructor <;> intro h <;> exact h'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.2s, verify 0.1s, in=229, out=514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction t <;> simp_all [isOrdered, Ordered, Option.bind]
```

**final state (truncated):**
```
case node
α : Type u_1
cmp : α → α → Ordering
inst✝ : TransCmp cmp
c✝ : RBColor
l✝ : RBNode α
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 0.2s, in=948, out=2049)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (isOrdered_iff' (cmp:=cmp) (t:=t) (L:=[]) (R:=[]))
```

**lean_error:** tail step 1/1 ("simpa using (isOrdered_iff' (cmp:=cmp) (t:=t) (L:=[]) (R:=[]))"): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 258.1s, verify 0.1s, in=876, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
α : Type u_1
cmp : α → α → Ordering
inst✝ : TransCmp cmp
t : RBNode α
⊢ isOrdered cmp t none = true ↔ Ordered cmp t
```

**lean_error:** tail step 1/5 ('α : Type u_1'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.3s, verify 0.2s, in=837, out=519)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=1906, out=767)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using
  (isOrdered_iff' (cmp:=cmp) (t:=t) (L:= (none : Option α)) (R:= (none : Option α)))
```

**lean_error:** tail step 1/2 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 53.3s, verify 0.1s, in=1842, out=6219)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₂ : isOrdered cmp t none none ↔ Ordered cmp t := by
  have h₁ : isOrdered cmp t none none ↔ (∀ a ∈ none, t.All (cmpLT cmp a ·)) ∧ (∀ a ∈ none, t.All (cmpLT cmp · a)) ∧ (∀ a ∈ none, ∀ b ∈ none, cmpLT cmp a b) ∧ Ordered cmp t := by
    apply isOrdered_iff'
  have h₂ : (∀ a ∈ none, t.All (cmpLT cmp a ·)) := by simp
  have h₃ : (∀ a ∈ none, t.All (cmpLT cmp · a)) := by simp
  have h₄ : (∀ a ∈ none, ∀ b ∈ none, cmpLT cmp a b) := by simp
  have h₅ : ( (∀ a ∈ none, t.All (cmpLT cmp a ·)) ∧ (∀ a ∈ none, t.All (cmpLT cmp · a)) ∧ (∀ a ∈ none, ∀ b ∈ none, cmpLT cmp a b) ∧ Ordered cmp t ) ↔ Ordered cmp t := by
    constructor <;> intro h₆ <;>
    (try
      {
        exact h₆.2.2.2
      })
    <;> (try
      {
        exact ⟨h₂, h₃, h₄, h₆⟩
      })
  rw [h₁]
  rw [h₅]
  
have h₃ : isOrdered cmp t none = isOrdered cmp t none none := by rfl
  
have h₄ : (isOrdered cmp t none = true) ↔ Ordered cmp t := by
  rw [h₃]
  exact h₂
  
exact h₄
```

**lean_error:** tail step 1/23 ('have h₂ : isOrdered cmp t none none ↔ Ordered cmp t := by'): <stdin>:1:57: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.2s, in=1805, out=580)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.3s, verify 0.1s, in=1822, out=1757)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (isOrdered_iff' (cmp:=cmp) (t:=t) (L:=none) (R:=none))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 109.8s, verify 0.1s, in=2016, out=12769)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : isOrdered cmp t none none ↔ Ordered cmp t := by
  have h₁ : isOrdered cmp t none none ↔ (∀ a ∈ none, t.All (cmpLT cmp a ·)) ∧ (∀ a ∈ none, t.All (cmpLT cmp · a)) ∧ (∀ a ∈ none, ∀ b ∈ none, cmpLT cmp a b) ∧ Ordered cmp t := isOrdered_iff'
  rw [h₁]
  constructor
  · -- Prove the forward direction: if the left is true, then the right is true.
    intro h₂
    -- Then, the right-hand side of the conjunction must be true, so we get Ordered cmp t.
    exact h₂.2.2.2
  · -- Prove the backward direction: if Ordered cmp t is true, then the left is true.
    intro h₂
    -- We need to prove the three conjuncts are true.
    have h₃ : (∀ a ∈ none, t.All (cmpLT cmp a ·)) := by
      intro a ha
      exfalso
      exact ha
    have h₄ : (∀ a ∈ none, t.All (cmpLT cmp · a)) := by
      intro a ha
      exfalso
      exact ha
    have h₅ : (∀ a ∈ none, ∀ b ∈ none, cmpLT cmp a b) := by
      intro a ha b hb
      exfalso
      exact ha
    exact ⟨h₃, h₄, h₅, h₂⟩
have h₂ : isOrdered cmp t none = isOrdered cmp t none none := by rfl
constructor
  · -- Forward direction: isOrdered cmp t none = true → Ordered cmp t
    intro h₁
    have h₃ : isOrdered cmp t none none = true := by
      rw [h₂] at h₁
      exact h₁
    have h₄ : isOrdered cmp t none none := by
      simp [h₃]
    have h₅ : Ordered cmp t := by
      have h₆ : isOrdered cmp t none none ↔ Ordered cmp t := h
      exact (h₆.mp h₄)
    exact h₅
  · -- Backward direction: Ordered cmp t → isOrdered cmp t none = true
    intro h₁
    have h₂ : isOrdered cmp t none none := by
      have h₃ : isOrdered cmp t none none ↔ Ordered cmp t := h
      exact (h₃.mpr h₁)
    have h₃ : isOrdered cmp t none none = true := by
      simp [h₂]
    have h₄ : isOrdered cmp t none = true := by
      rw [h₂] at *
      <;> simp [h₃]
    exact h₄
```

**lean_error:** tail step 1/48 ('have h : isOrdered cmp t none none ↔ Ordered cmp t := by'): <stdin>:1:56: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.8s, verify 0.2s, in=1808, out=955)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isOrdered_iff']
simp
```
