# Std.RBNode.Stream.next?_toList   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases s <;> simp [next?, toStream_toList']
```

**True premises at k:** `Std.RBNode.Stream.next?`, `Std.RBNode.toStream_toList'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | · | · |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=332, out=972)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases h : next? s with
| none =>
    simp [Option.map, h, List.next?, toList]
| some p =>
    rcases p with ⟨a, b⟩
    simp [Option.map, h, List.next?, toList]
```

**lean_error:** tail step 1/6 ('cases h : next? s with'): <stdin>:1:22: unexpected end of input; expected '|'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.1s, verify 0.1s, in=276, out=18348)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases s with
| nil => simp [next?, toList, List.next?]
| cons a s =>
  simp [next?, toList, List.next?, Option.map]
  <;>
  (try congr 1) <;>
  (try ext) <;>
  (try simp_all [Prod.mk.injEq]) <;>
  (try aesop)
```

**lean_error:** tail step 1/9 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 3.5s, verify 0.1s, in=283, out=315)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases h : next? s <;> simp_all [Option.map]
```

**final state (truncated):**
```
case none
α : Type u_1
s : RBNode.Stream α
h : next? s = none
⊢ none = List.next? (toList s)

...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=759, out=1404)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases s with
| nil => simp
| cons v r tail => 
    simp [Option.map, List.next?, RBNode.Stream.next?, toStream_toList']
```

**lean_error:** tail step 1/4 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.9s, verify 0.1s, in=700, out=4645)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases s with
| nil =>
  simp [next?, Option.map, toList, List.next?]
| cons v r tail =>
  simp [next?, Option.map, toList, List.next?]
  <;>
  (try simp_all [toStream_toList']) <;>
  (try aesop) <;>
  (try
    {
      rw [toStream_toList']
    }) <;>
  (try simp_all [List.cons_append, List.append_assoc]) <;>
  (try aesop)
```

**lean_error:** tail step 1/14 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.5s, verify 0.1s, in=712, out=527)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases s <;> simp [next?, List.next?, toStream_toList']
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=1306, out=1335)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s with
| nil =>
    simp [RBNode.Stream.next?, List.next?, Option.map]
| cons v r tail =>
    simp [RBNode.Stream.next?, List.next?, Option.map, toStream_toList']
```

**lean_error:** tail step 1/5 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 23.4s, verify 0.1s, in=1249, out=2691)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s <;> simp [next?, Option.map, List.next?, toList, toStream_toList']
```

**final state (truncated):**
```
case cons
α : Type u_1
v✝ : α
r✝ : RBNode α
tail✝ : RBNode.Stream α
⊢ foldr (fun x x_1 => x :: x_1) (toStream r✝ tail✝) [] =
...
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.9s, verify 0.1s, in=1271, out=465)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s <;> simp [next?, List.next?, toList]
```

**final state (truncated):**
```
case cons
α : Type u_1
v✝ : α
r✝ : RBNode α
tail✝ : RBNode.Stream α
⊢ foldr (fun x x_1 => x :: x_1) (toStream r✝ tail✝) [] =
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=1271, out=1349)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s with
| nil => simp [Std.RBNode.Stream.next?, List.next?]
| cons v r tail => 
    simp [Std.RBNode.Stream.next?, List.next?, Std.RBNode.toStream_toList']
```

**lean_error:** tail step 1/4 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.5s, verify 0.1s, in=1365, out=5432)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s <;> simp [next?, toList, Option.map, List.next?] <;> rfl
```

**lean_error:** tail step 1/1 ('cases s <;> simp [next?, toList, Option.map, List.next?] <;> rfl'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.3s, in=1279, out=658)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s
· simp [next?, List.next?]
· simp [next?, List.next?, toStream_toList']
```
