# monotone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

**True premises at k:** `monotone_toDual_comp_iff`, `antitone_comp_ofDual_iff`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.2s, verify 0.2s, in=355, out=3042)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  simpa [Monotone, Function.comp] using h
· intro h
  simpa [Monotone, Function.comp] using h
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 86.1s, verify 0.2s, in=306, out=9812)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    refine' fun a b hab => _
    have h₁ : (toDual b : Dual α) ≤ (toDual a : Dual α) := by
      rw [dual_le_iff]
      <;> simp_all [hab]
      <;> exact le_of_le hab
    have h₂ : (toDual ∘ f ∘ ofDual) (toDual b) ≤ (toDual ∘ f ∘ ofDual) (toDual a) := h h₁
    have h₃ : (toDual ∘ f ∘ ofDual) (toDual b) = toDual (f b) := by
      simp [toDual_ofDual, ofDual_toDual, Function.comp_apply]
    have h₄ : (toDual ∘ f ∘ ofDual) (toDual a) = toDual (f a) := by
      simp [toDual_ofDual, ofDual_toDual, Function.comp_apply]
    rw [h₃] at h₂
    rw [h₄] at h₂
    have h₅ : (f a : β) ≤ (f b : β) := by
      rw [dual_le_iff] at h₂
      exact h₂
    exact h₅
  · intro h
    refine' fun x y hxy => _
    have h₁ : (ofDual y : α) ≤ (ofDual x : α) := by
      rw [dual_le_iff] at hxy
      exact hxy
    have h₂ : f (ofDual y) ≤ f (ofDual x) := h h₁
    have h₃ : (toDual ∘ f ∘ ofDual) x = toDual (f (ofDual x)) := by
      simp [Function.comp_apply]
    have h₄ : (toDual ∘ f ∘ ofDual) y = toDual (f (ofDual y)) := by
      simp [Function.comp_apply]
    rw [h₃, h₄]
    rw [dual_le_iff]
    exact h₂
```

**lean_error:** tail step 2/31 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 12.3s, verify 0.2s, in=297, out=1154)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h a b hab
  have : toDual (f b) ≤ toDual (f a) := h (toDual b) (toDual a) (by simpa [le_def])
  simpa [le_def] using this
· intro h a b hab
  have : f (ofDual b) ≤ f (ofDual a) := h (ofDual b) (ofDual a) (by simpa [le_def])
  simpa [le_def] using this
```

**lean_error:** tail step 2/7 ('· intro h a b hab'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=705, out=1135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Function.comp] using
  (monotone_toDual_comp_iff (f := f ∘ ofDual)).trans
    (antitone_comp_ofDual_iff (f := f))
```

**lean_error:** tail step 1/3 ('simpa [Function.comp] using'): <stdin>:1:27: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 229.8s, verify 0.1s, in=671, out=27258)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  Monotone (⇑toDual ∘ f ∘ ⇑ofDual) = Monotone (⇑toDual ∘ (f ∘ ⇑ofDual)) := by rw [Function.comp_assoc]
  _ ↔ Antitone (f ∘ ⇑ofDual) := by apply monotone_toDual_comp_iff
  _ ↔ Monotone f := by apply antitone_comp_ofDual_iff
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 13.5s, verify 0.1s, in=637, out=1358)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=1057, out=1199)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Function.comp] using
  (monotone_toDual_comp_iff (f := f ∘ ofDual)).trans
    (antitone_comp_ofDual_iff (f := f))
```

**lean_error:** tail step 1/3 ('simpa [Function.comp] using'): <stdin>:1:27: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 104.2s, verify 0.1s, in=1021, out=11885)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : toDual ∘ f ∘ ofDual = toDual ∘ (f ∘ ofDual) := by
  funext x
  <;> simp [Function.comp_apply]
  <;> rfl
have h₁ : Monotone (toDual ∘ f ∘ ofDual) ↔ Monotone f := by
  calc
    Monotone (toDual ∘ f ∘ ofDual) = Monotone (toDual ∘ (f ∘ ofDual)) := by rw [h]
    _ ↔ Antitone (f ∘ ofDual) := by apply monotone_toDual_comp_iff
    _ ↔ Monotone f := by apply antitone_comp_ofDual_iff
exact h₁
```

**lean_error:** tail step 1/10 ('have h : toDual ∘ f ∘ ofDual = toDual ∘ (f ∘ ofDual) := by'): <stdin>:1:58: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.0s, verify 0.5s, in=984, out=1274)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Function.comp_assoc]
rw [monotone_toDual_comp_iff]
rw [antitone_comp_ofDual_iff]
```

**lean_error:** tail step 1/3 ('rw [Function.comp_assoc]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=1033, out=1161)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Function.comp] using
  (monotone_toDual_comp_iff (f := f ∘ ofDual)).trans
    (antitone_comp_ofDual_iff (f := f))
```

**lean_error:** tail step 1/3 ('simpa [Function.comp] using'): <stdin>:1:27: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 111.6s, verify 0.1s, in=1093, out=12907)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply monotone_toDual_comp_iff
apply antitone_comp_ofDual_iff
<;> assumption
<;> try simp_all
<;> try tauto
<;> try aesop
<;> try norm_num
<;> try linarith
<;> try ring_nf
<;> try field_simp
<;> try nlinarith
<;> try nlinarith [sq_nonneg (f x - f y), sq_nonneg (x - y)]
```

**lean_error:** tail step 1/12 ('apply monotone_toDual_comp_iff'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.3s, verify 0.1s, in=999, out=759)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```
