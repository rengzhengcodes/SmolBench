# Std.AssocList.find?_eq   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/AssocList.lean`  

**Ground-truth tail (from k):**
```lean
simp [find?_eq_findEntry?]
```

**True premises at k:** `Std.AssocList.find?_eq_findEntry?`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | · |
| `hint:3` | ✘ | ✓ | · |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.6s, in=291, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold find?
unfold toList
simp [List.find?, Option.map]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : BEq α
a : α
l : AssocList α β
⊢ (match l with
...
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 8.1s, verify 0.1s, in=267, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l using AssocList.induction
simp [find?, List.find?, toList]
simp [find?, List.find?, toList]
simp [find?, List.find?, toList, beq_eq_true_eq]
split <;> simp [*]
split <;> simp [*]
aesop
```

**lean_error:** tail step 1/7 ('induction l using AssocList.induction'): unknown constant 'Std.AssocList.induction'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.2s, in=280, out=351)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply eq_of_heq
ext x
simp [find?]
```

**lean_error:** tail step 2/3 ('ext x'): applyExtTheorem only applies to equations, not

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=554, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
rw [toList]
rw [List.find?_eq_findEntry?]
congr
```

**lean_error:** tail step 2/4 ('rw [toList]'): failed to rewrite using equation theorems for 'Std.AssocList.toList'

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 4.4s, in=520, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
simp [findEntry?, List.find?, toList]
split <;> simp [*]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 55.2s, verify 0.1s, in=543, out=3383)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : BEq α
a : α
l : AssocList α β
⊢ Option.map (fun x => x.snd) (findEntry? a l) =
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=755, out=49)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
rw [toList]
rw [List.find?_eq_findEntry?]
rw [Option.map_map]
rw [Option.map_id]
congr
rw [findEntry?_eq]
```

**lean_error:** tail step 2/7 ('rw [toList]'): failed to rewrite using equation theorems for 'Std.AssocList.toList'

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 7.9s, verify 0.2s, in=720, out=61)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
simp [findEntry?, List.find?]
split <;> simp [*] 
rw [toList] 
simp [List.find?, List.findIdx?]
split <;> simp [*] 
simp [Prod.map] 
split <;> simp [*]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 7.8s, verify 0.1s, in=744, out=453)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : BEq α
a : α
l : AssocList α β
⊢ Option.map (fun x => x.snd) (findEntry? a l) =
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=778, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?, List.find?_eq_findEntry?]
simp [AssocList.findEntry?, List.findEntry?]
```

**lean_error:** tail step 1/2 ('rw [find?_eq_findEntry?, List.find?_eq_findEntry?]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 5.0s, verify 2.9s, in=766, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?, AssocList.findEntry?_eq_List_find?, toList]
simp [List.find?_map, Prod.map]
```

**lean_error:** tail step 1/2 ('rw [find?_eq_findEntry?, AssocList.findEntry?_eq_List_find?, toList]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.0s, in=767, out=350)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
