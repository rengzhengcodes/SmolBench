# Std.UnionFind.equiv_empty   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/UnionFind/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [Equiv]
```

**True premises at k:** `Std.UnionFind.Equiv`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.1s, verify 0.1s, in=257, out=1266)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 84.2s, verify 0.1s, in=199, out=9675)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iff.rfl
```

**lean_error:** tail step 1/1 ('apply iff.rfl'): unknown identifier 'iff.rfl'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=200, out=531)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  induction h
  · rfl
· intro h
  rw [h]
  exact Equiv.refl empty
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.0s, verify 0.2s, in=456, out=1223)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· intro h
  simpa [Std.UnionFind.Equiv, Std.UnionFind.rootD] using h
· intro h
  simpa [Std.UnionFind.Equiv, Std.UnionFind.rootD] using h
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 263.4s, verify 0.1s, in=395, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem equiv_empty {a b : ℕ} : Equiv empty a b ↔ a = b := by
  constructor
  · intro h
    aesop
  · intro h
    aesop
```

**lean_error:** tail step 1/6 ('theorem equiv_empty {a b : ℕ} : Equiv empty a b ↔ a = b := by'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.4s, verify 0.1s, in=399, out=485)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Equiv]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=1437, out=758)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Equiv, empty]
```

**lean_error:** tail step 1/1 ('simpa [Equiv, empty]'): tactic 'assumption' failed

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 45.4s, verify 0.1s, in=1381, out=5009)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem Std.UnionFind.equiv_empty {a b : Nat} : Equiv empty a b ↔ a = b := by
  have h_root : ∀ a : Nat, empty.rootD a = a := by
    intro a
    rfl
  
  have h_imp : Equiv empty a b → a = b := by
    intro h
    have h₁ : empty.rootD a = empty.rootD b := by
      simpa [Equiv] using h
    have h₂ : empty.rootD a = a := h_root a
    have h₃ : empty.rootD b = b := h_root b
    linarith
  
  have h_conv : a = b → Equiv empty a b := by
    intro h
    have h₁ : empty.rootD a = empty.rootD b := by
      rw [h]
    simp [Equiv, h₁]
  
  have h_main : Equiv empty a b ↔ a = b := by
    constructor
    · -- Prove the forward direction: Equiv empty a b → a = b
      exact h_imp
    · -- Prove the backward direction: a = b → Equiv empty a b
      exact h_conv
  
  exact h_main
```

**lean_error:** tail step 1/23 ('theorem Std.UnionFind.equiv_empty {a b : Nat} : Equiv empty a b ↔ a = b := by'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.6s, in=1392, out=953)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  simp [Equiv] at h
  exact h
· intro h
  simp [Equiv, h]
```

**lean_error:** tail step 2/6 ('· intro h'): unsolved goals

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.2s, verify 0.5s, in=1346, out=623)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Equiv]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 62.8s, verify 0.1s, in=1557, out=7086)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
  · intro h
    simp [Equiv] at h
    have h₁ : empty.rootD a = a := by
      simp [UnionFind.empty, UnionFind.rootD]
      <;> rfl
    have h₂ : empty.rootD b = b := by
      simp [UnionFind.empty, UnionFind.rootD]
      <;> rfl
    have h₃ : a = b := by linarith
    exact h₃
  · intro h
    simp [Equiv]
    have h₁ : empty.rootD a = empty.rootD b := by rw [h]
    exact h₁
```

**lean_error:** tail step 2/15 ('· intro h'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.2s, verify 0.1s, in=1389, out=462)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Equiv, UnionFind.rootD_empty]
```
