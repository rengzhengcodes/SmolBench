# Std.UnionFind.parent'_lt   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/UnionFind/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← parentD_eq, parentD_lt, Fin.is_lt, Array.data_length]
```

**True premises at k:** `Std.UnionFind.parentD_eq`, `Std.UnionFind.parentD_lt`, `Fin.is_lt`, `Array.data_length`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=266, out=936)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact self.parent_lt i
```

**lean_error:** tail step 1/1 ('exact self.parent_lt i'): invalid field 'parent_lt', the environment does not contain 'Std.UnionFind.parent_lt'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.4s, verify 0.1s, in=212, out=10644)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases self with
| mk arr size h =>
  exact h i
```

**lean_error:** tail step 1/3 ('cases self with'): <stdin>:1:15: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=212, out=645)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact self.property i
```

**lean_error:** tail step 1/1 ('exact self.property i'): invalid field 'property', the environment does not contain 'Std.UnionFind.property'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=721, out=926)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h := self.parentD_lt (i := i.1) (by
    simpa using i.is_lt)
  simpa [parentD_eq] using h
```

**lean_error:** tail step 1/3 ('have h := self.parentD_lt (i := i.1) (by'): <stdin>:1:40: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 80.7s, verify 0.1s, in=678, out=10427)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : (i : ℕ) < size self := Fin.is_lt i
have h₂ : (Array.get self.arr i).parent = parentD self.arr (i : ℕ) := by
  apply parentD_eq
have h₃ : parentD self.arr (i : ℕ) < size self := by
  apply UnionFind.parentD_lt
  <;> assumption
have h₄ : (Array.get self.arr i).parent < size self := by
  rw [h₂]
  exact h₃
exact h₄
```

**lean_error:** tail step 1/10 ('have h₁ : (i : ℕ) < size self := Fin.is_lt i'): unknown identifier 'ℕ'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 7.3s, verify 0.1s, in=673, out=512)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Std.UnionFind.parentD_eq]
apply Std.UnionFind.parentD_lt
```

**final state (truncated):**
```
case a
self : UnionFind
i : Fin (size self)
⊢ ↑i < Array.size self.arr
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=1939, out=869)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [parentD_eq] using self.parentD_lt i
```

**lean_error:** tail step 1/1 ('simpa [parentD_eq] using self.parentD_lt i'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 159.4s, verify 0.1s, in=1919, out=21232)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : i.val < self.arr.size := by
  have h₂ : i : Fin (self.arr.size) := by
    exact inferInstance
  exact h₂.is_lt
have h₂ : size self = self.arr.size := by
  rfl
have h₃ : parentD self.arr i.val < self.arr.size := by
  have h₄ : i.val < self.arr.size := h₁
  have h₅ : parentD self.arr i.val < self.arr.size := by
    apply Std.UnionFind.parentD_lt
    <;> assumption
  exact h₅
have h₄ : parentD self.arr i.val < size self := by
  rw [h₂] at *
  exact h₃
have h₅ : (self.arr.get i).parent = parentD self.arr i.val := by
  apply parentD_eq
  <;> simp [i]
have h₆ : (self.arr.get i).parent < size self := by
  rw [h₅]
  exact h₄
exact h₆
```

**lean_error:** tail step 1/22 ('have h₁ : i.val < self.arr.size := by'): <stdin>:1:37: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.8s, verify 0.2s, in=1912, out=788)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Std.UnionFind.parentD_eq]
apply Std.UnionFind.parentD_lt
exact Fin.is_lt i
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=1826, out=1059)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hlt : (Array.get self.arr i).parent < self.arr.size := by
    have : parentD self.arr i.1 < self.arr.size := by
      have hi : (i : Nat) < self.arr.size := by
        simpa using (Fin.is_lt i)
      exact parentD_lt hi
    simpa [parentD_eq] using this
  simpa [UnionFind.size] using hlt
```

**lean_error:** tail step 1/7 ('have hlt : (Array.get self.arr i).parent < self.arr.size := by'): <stdin>:1:62: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 137.7s, verify 0.2s, in=2118, out=18308)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : size self = self.arr.data.length := by rfl
have h₂ : self.arr.data.length = self.arr.size := by rw [Array.data_length]
have h₃ : size self = self.arr.size := by linarith
have h₄ : (i : Nat) < size self := Fin.is_lt i
have h₅ : (i : Nat) < self.arr.size := by linarith
have h₆ : parentD self.arr i.1 < self.arr.size := by apply parentD_lt h₅
have h₇ : parentD self.arr i.1 < size self := by linarith
have h₈ : (Array.get self.arr i).parent = parentD self.arr i.1 := by rw [parentD_eq]
have h₉ : (Array.get self.arr i).parent < size self := by linarith
exact h₉
```

**lean_error:** tail step 3/10 ('have h₃ : size self = self.arr.size := by linarith'): <stdin>:1:43: unknown tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 13.6s, verify 0.1s, in=1901, out=1525)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← parentD_eq]
apply parentD_lt
```

**final state (truncated):**
```
case a
self : UnionFind
i : Fin (size self)
⊢ ↑i < Array.size self.arr
```
