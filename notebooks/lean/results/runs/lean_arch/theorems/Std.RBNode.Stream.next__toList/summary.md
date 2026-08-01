# Std.RBNode.Stream.next?_toList   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases s <;> simp [next?, toStream_toList']
```

**True premises at k:** `Std.RBNode.Stream.next?`, `Std.RBNode.toStream_toList'`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | · | ✘ |
| `hint:3` | ✓ | ✘ | · |
| `noise:3` | ✓ | · | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.4s, in=292, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases s
· simp [toList, next?]
· simp [toList, next?, Option.map]
```

**lean_error:** tail step 3/3 ('· simp [toList, next?, Option.map]'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=268, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.next?_toList, next?_eq_some_iff]
simp only [Option.map_eq_some', Option.mem_def]
constructor
· rfl
· simp only [toList_toList]
```

**lean_error:** tail step 1/5 ('rw [List.next?_toList, next?_eq_some_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=281, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases s
simp [next?, List.next?, toList]
```

**final state (truncated):**
```
case cons
α : Type u_1
v✝ : α
r✝ : RBNode α
tail✝ : RBNode.Stream α
⊢ Option.map
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.9s, verify 0.3s, in=704, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases s
· simp [next?]
· simp [next?, toStream_toList']
```

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=685, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases s <;> simp [*, List.next?, Std.RBNode.Stream.next?, toList, toStream, Std.RBNode.toStream_toList']
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

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.4s, in=693, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases next? s
simp [next?, List.next?]
rw [toStream_toList']
simp
```

**lean_error:** tail step 3/4 ("rw [toStream_toList']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.5s, in=1238, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s
· simp [next?]
· simp [next?, toStream_toList']
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1220, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases s <;> simp [*, List.next?, toList, toStream, Std.RBNode.Stream.next?, Std.RBNode.toStream_toList'] <;> rfl
```

**lean_error:** tail step 1/1 ("cases s <;> simp [*, List.next?, toList, toStream, Std.RBNode.Stream.next?, Std.RBNode.toStream_toList'] <;> rfl"): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 12.1s, verify 0.3s, in=1227, out=723)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
cases next? s
simp [next?, toList, toStream_toList']
```

**final state (truncated):**
```
case none
α : Type u_1
s : RBNode.Stream α
⊢ none = List.next? (foldr (fun x x_1 => x :: x_1) s [])

case some
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.2s, verify 0.3s, in=1263, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s
· simp [next?]
· simp [next?, toStream_toList']
  rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.2s, in=1307, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
cases s <;> simp [*, List.next?, next?, toList, toStream, Std.RBNode.toStream_toList']
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

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=1252, out=315)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Option.map_ext
intro x
cases x
simp [toList_toStream', toList_cons]
```

**lean_error:** tail step 1/4 ('apply Option.map_ext'): unknown constant 'Option.map_ext'
