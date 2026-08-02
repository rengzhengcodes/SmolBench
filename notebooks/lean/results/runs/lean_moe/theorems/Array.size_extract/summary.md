# Array.size_extract   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [size_extract_loop, size_empty, Nat.zero_add, Nat.sub_min_sub_right,
Nat.min_assoc, Nat.min_self]
```

**True premises at k:** `Array.size_extract_loop`, `Array.size_empty`, `Nat.zero_add`, `Nat.sub_min_sub_right`, `Nat.min_assoc`, `Nat.min_self`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.4s, in=303, out=524)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [extract.loop]
```

**lean_error:** tail step 1/1 ('simpa [extract.loop]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.2s, verify 0.1s, in=247, out=4025)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : size (extract.loop as (min stop (size as) - start) start #[]) = size #[] + (min stop (size as) - start) := by
  apply extract.loop_size
rw [h]
<;> simp [size_empty, add_zero]
```

**lean_error:** tail step 1/4 ('have h : size (extract.loop as (min stop (size as) - start) start #[]) = size #[] + (min stop (size as) - start) := by'): <stdin>:1:118: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=248, out=342)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [extract.loop_size]
```

**lean_error:** tail step 1/1 ('simp [extract.loop_size]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.4s, verify 0.1s, in=1372, out=1652)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Array.size_extract_loop, Array.size_empty, Nat.zero_add,
  Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

**lean_error:** tail step 1/2 ('simpa [Array.size_extract_loop, Array.size_empty, Nat.zero_add,'): <stdin>:1:63: unexpected end of input; expected '*' or '-'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 40.2s, verify 0.1s, in=1335, out=4346)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem Array.size_extract (α : Type u_1) (as : Array α) (stop start : Nat) :
    size (extract as stop start) = min stop (size as) - start := by
  simp [extract]
  have h₁ : size (extract.loop as (min stop (size as) - start) start #[]) = (#[]).size + min (min stop (size as) - start) (size as - start) := by
    rw [Array.size_extract_loop]
    <;>
    simp_all [Nat.sub_eq_zero_of_le]
    <;>
    ring_nf at *
    <;>
    omega
  
  have h₂ : (#[]).size + min (min stop (size as) - start) (size as - start) = min (min stop (size as) - start) (size as - start) := by
    rw [Array.size_empty]
    <;> simp [zero_add]
  
  have h₃ : min (min stop (size as) - start) (size as - start) = min (min stop (size as)) (size as) - start := by
    have h₃₁ : min (min stop (size as) - start) (size as - start) = min (min stop (size as)) (size as) - start := by
      rw [Nat.sub_min_sub_right]
    rw [h₃₁]
  
  have h₄ : min (min stop (size as)) (size as) = min stop (size as) := by
    apply min_eq_left
    <;> exact min_le_right stop (size as)
  
  have h₅ : min (min stop (size as) - start) (size as - start) = min stop (size as) - start := by
    rw [h₃]
    rw [h₄]
    <;>
    simp [Nat.sub_eq_zero_of_le]
    <;>
    ring_nf at *
    <;>
    omega
  
  have h₆ : size (extract.loop as (min stop (size as) - start) start #[]) = min stop (size as) - start := by
    calc
      size (extract.loop as (min stop (size as) - start) start #[]) = (#[]).size + min (min stop (size as) - start) (size as - start) := by rw [h₁]
      _ = min (min stop (size as) - start) (size as - start) := by rw [h₂]
      _ = min stop (size as) - start := by rw [h₅]
  
  exact h₆
```

**lean_error:** tail step 1/36 ('theorem Array.size_extract (α : Type u_1) (as : Array α) (stop start : Nat) :'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=1324, out=640)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Array.size_extract_loop, Array.size_empty, Nat.zero_add]
<;> simp [Nat.min_assoc, Nat.min_self]
<;> rw [←Nat.sub_min_sub_right]
<;> simp [Nat.min_assoc, Nat.min_self]
```

**lean_error:** tail step 2/4 ('<;> simp [Nat.min_assoc, Nat.min_self]'): <stdin>:1:0: expected tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.2s, in=4813, out=1947)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [size_extract_loop, size_empty, Nat.zero_add]
  have hle : min stop as.size - start ≤ as.size - start := by
    have h := Nat.min_le_right (a:=stop) (b:=as.size)
    exact Nat.sub_le_sub_right h start
  simpa [Nat.min_eq_left hle]
```

**lean_error:** tail step 2/5 ('have hle : min stop as.size - start ≤ as.size - start := by'): <stdin>:1:59: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 84.8s, verify 0.1s, in=4850, out=9547)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  size (extract.loop as (min stop (size as) - start) start #[]) = (#[]).size + min (min stop (size as) - start) (as.size - start) := by apply Array.size_extract_loop
  _ = 0 + min (min stop (size as) - start) (as.size - start) := by rw [Array.size_empty]
  _ = min (min stop (size as) - start) (as.size - start) := by simp [Nat.zero_add]
  _ = min (min stop (size as) - start) (size as - start) := by rfl
  _ = min (min stop (size as)) (size as) - start := by rw [Nat.sub_min_sub_right]
  _ = min stop (size as) - start := by
    rw [min_eq_left (min_le_right : min stop (size as) ≤ size as)]
    <;> rfl
```

**lean_error:** tail step 1/9 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.2s, verify 0.4s, in=4760, out=1233)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Array.size_extract_loop]
simp [Array.size_empty]
rw [Nat.sub_min_sub_right]
rw [Nat.min_assoc]
simp [Nat.min_self]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.8s, verify 0.2s, in=4421, out=1844)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Array.size_extract_loop, Array.size_empty, Nat.zero_add]
simp [Nat.sub_min_sub_right, Nat.min_assoc, Nat.min_self]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 45.4s, verify 0.1s, in=5325, out=5006)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Array.size_extract (as : Array α) (start stop : Nat) :
    size (extract as start stop) = if stop ≤ size as then stop - start else 0 := by
  have h₁ : size (extract.loop as (min stop (size as) - start) start #[]) = (#[]).size + min (min stop (size as) - start) (as.size - start) := by
    rw [Array.size_extract_loop]
    <;>
    simp [add_comm]
    <;>
    ring_nf
    <;>
    simp_all [Nat.min_sub_sub_distrib]
    <;>
    omega
  
  have h₂ : (#[]).size = 0 := by
    rw [Array.size_empty]
  
  have h₃ : size (extract.loop as (min stop (size as) - start) start #[]) = 0 + min (min stop (size as) - start) (as.size - start) := by
    rw [h₁]
    rw [h₂]
    <;>
    simp [add_zero]
  
  have h₄ : size (extract.loop as (min stop (size as) - start) start #[]) = min (min stop (size as) - start) (as.size - start) := by
    rw [h₃]
    <;>
    simp [zero_add]
  
  have h₅ : min (min stop (size as) - start) (as.size - start) = min stop (size as) - start := by
    have h₅₁ : min (min stop (size as) - start) (as.size - start) = (min (min stop (size as)) (as.size)) - start := by
      rw [Nat.sub_min_sub_right]
    have h₅₂ : min (min stop (size as)) (as.size) = min stop (size as) := by
      apply Nat.min_eq_left
      exact Nat.min_le_right _ _
    rw [h₅₁, h₅₂]
    <;>
    simp [Nat.sub_self]
  
  have h₆ : size (extract.loop as (min stop (size as) - start) start #[]) = min stop (size as) - start := by
    rw [h₄]
    rw [h₅]
  
  exact h₆
```

**lean_error:** tail step 1/36 ('theorem Array.size_extract (as : Array α) (start stop : Nat) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 21.9s, verify 0.2s, in=4720, out=2295)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Array.size_extract_loop, Array.size_empty, Nat.zero_add]
rw [← Nat.sub_min_sub_right (min stop (size as)) (size as) start]
rw [← Nat.min_assoc stop (size as) (size as)]
simp [Nat.min_self]
```

**lean_error:** tail step 2/4 ('rw [← Nat.sub_min_sub_right (min stop (size as)) (size as) start]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
