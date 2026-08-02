# antitone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**True premises at k:** `antitone_toDual_comp_iff`, `monotone_comp_ofDual_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.2s, in=351, out=2253)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Antitone, Function.comp]
```

**lean_error:** tail step 1/1 ('simpa [Antitone, Function.comp]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 129.7s, verify 0.2s, in=302, out=14995)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro hg
  refine' fun a b hab => _
  have h₁ : (ofDual b : Dual α) ≤ (ofDual a : Dual α) := by
    rw [Dual.le]
    <;> simp [toDual_ofDual]
    <;> exact hab
  have h₂ : (⇑toDual ∘ f ⇑ofDual) (ofDual a) ≤ (⇑toDual ∘ f ⇑ofDual) (ofDual b) := hg h₁
  have h₃ : (⇑toDual ∘ f ⇑ofDual) (ofDual a) = ⇑toDual (f a) := by
    simp [Function.comp_apply]
    <;> simp [toDual_ofDual]
    <;> rfl
  have h₄ : (⇑toDual ∘ f ⇑ofDual) (ofDual b) = ⇑toDual (f b) := by
    simp [Function.comp_apply]
    <;> simp [toDual_ofDual]
    <;> rfl
  rw [h₃] at h₂
  rw [h₄] at h₂
  have h₅ : f b ≤ f a := by
    have h₅₁ : (⇑toDual (f a) : Dual β) ≤ (⇑toDual (f b) : Dual β) := h₂
    have h₅₂ : (f b : β) ≤ (f a : β) := by
      rw [le_toDual] at h₅₁
      exact h₅₁
    exact h₅₂
  exact h₅
· intro hf
  refine' fun x y hxy => _
  have h₁ : (ofDual y : α) ≤ (ofDual x : α) := by
    exact Dual.le hxy
  have h₂ : f (ofDual x) ≤ f (ofDual y) := hf h₁
  have h₃ : (⇑toDual ∘ f ⇑ofDual) y ≤ (⇑toDual ∘ f ⇑ofDual) x := by
    have h₄ : (⇑toDual ∘ f ⇑ofDual) y = ⇑toDual (f (ofDual y)) := by
      simp [Function.comp_apply]
      <;> simp [toDual_ofDual]
      <;> rfl
    have h₅ : (⇑toDual ∘ f ⇑ofDual) x = ⇑toDual (f (ofDual x)) := by
      simp [Function.comp_apply]
      <;> simp [toDual_ofDual]
      <;> rfl
    rw [h₄, h₅]
    have h₆ : (f (ofDual x) : β) ≤ (f (ofDual y) : β) := h₂
    rw [le_toDual]
    exact h₆
  exact h₃
```

**lean_error:** tail step 2/44 ('· intro hg'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.4s, verify 0.2s, in=293, out=610)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Antitone, Function.comp_apply, toDual_le_toDual, ofDual_le_ofDual]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=700, out=1214)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Function.comp] using
  (antitone_toDual_comp_iff (f := f ∘ ofDual) (α := αᵒᵈ)).trans
    (monotone_comp_ofDual_iff (f := f))
```

**lean_error:** tail step 1/3 ('simpa [Function.comp] using'): <stdin>:1:27: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 131.5s, verify 0.2s, in=666, out=15198)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff]
rw [monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.3s, in=632, out=736)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← monotone_comp_ofDual_iff]
rw [← antitone_toDual_comp_iff]
<;> simp [Function.comp.assoc]
```

**lean_error:** tail step 3/3 ('<;> simp [Function.comp.assoc]'): <stdin>:1:0: expected tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=1052, out=1237)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Function.comp] using (antitone_toDual_comp_iff (f := f ∘ ofDual)).trans (monotone_comp_ofDual_iff (f := f))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 170.6s, verify 0.1s, in=1016, out=21168)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  Antitone (toDual ∘ f ∘ ofDual) = Antitone (toDual ∘ (f ∘ ofDual)) := by
    rw [Function.comp_assoc]
  _ ↔ Monotone (f ∘ ofDual) := antitone_toDual_comp_iff
  _ ↔ Antitone f := monotone_comp_ofDual_iff
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.1s, verify 0.3s, in=979, out=1221)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← monotone_comp_ofDual_iff]
rw [← antitone_toDual_comp_iff]
rfl
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=1028, out=1858)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Function.comp] using (antitone_toDual_comp_iff (f := f ∘ ofDual)).trans (monotone_comp_ofDual_iff (f := f))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 78.4s, verify 0.1s, in=1088, out=9022)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_eq : (⇑toDual ∘ f ∘ ⇑ofDual) = (⇑toDual ∘ (f ∘ ⇑ofDual)) := by
  funext x
  simp [Function.comp_apply]
  <;>
  rfl

rw [h_eq]

have h₂ : Antitone (⇑toDual ∘ (f ∘ ⇑ofDual)) ↔ Monotone (f ∘ ⇑ofDual) := by
  apply antitone_toDual_comp_iff

have h₃ : Monotone (f ∘ ⇑ofDual) ↔ Antitone f := by
  apply monotone_comp_ofDual_iff

constructor <;> intro h <;>
(try {
  have h₄ : Monotone (f ∘ ⇑ofDual) := h₂.mp h
  have h₅ : Antitone f := h₃.mp h₄
  exact h₅
}) <;>
(try {
  have h₄ : Antitone f := h₃.mpr h
  have h₅ : Antitone (⇑toDual ∘ (f ∘ ⇑ofDual)) := h₂.mpr h₄
  exact h₅
})
```

**lean_error:** tail step 1/21 ('have h_eq : (⇑toDual ∘ f ∘ ⇑ofDual) = (⇑toDual ∘ (f ∘ ⇑ofDual)) := by'): <stdin>:1:69: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.3s, verify 0.1s, in=994, out=588)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]'): tactic 'rewrite' failed, equality or iff proof expected
