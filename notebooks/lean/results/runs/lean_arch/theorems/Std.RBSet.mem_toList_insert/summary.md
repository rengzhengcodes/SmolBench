# Std.RBSet.mem_toList_insert   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [mem_toList] using RBNode.mem_insert ht₂ ht₁
```

**True premises at k:** `Std.RBSet.mem_toList`, `Std.RBNode.mem_insert`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 4.1s, in=336, out=175)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold toList
unfold insert
cases t
simp
cases h : find? t_val v <;> simp
case none => 
  constructor <;> intro h 
  case left => 
    apply Or.inl 
    constructor 
    assumption
    assumption
  case right => 
    cases h 
    apply Or.inl 
    constructor 
    assumption 
    simp [find?]
    contradiction
    assumption
case some w => 
  constructor <;> intro h 
  case left => 
    cases h 
    apply Or.inl 
    constructor 
    assumption 
    simp [find?]
    assumption
    apply Or.inr 
    assumption
  case right => 
    cases h 
    apply Or.inl 
    constructor 
    assumption 
    simp [find?]
    contradiction
    assumption
```

**lean_error:** tail step 5/39 ('cases h : find? t_val v <;> simp'): unknown identifier 't_val'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=309, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← RBSet.mem_toList_iff, ← RBSet.mem_toList_iff]
simp only [insert, RBSet.mem_insert_iff, ne_comm, find?_eq_some, not_and]
tauto
```

**lean_error:** tail step 1/3 ('rw [← RBSet.mem_toList_iff, ← RBSet.mem_toList_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 132.7s, verify 0.1s, in=325, out=8304)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split_iff
intro h
cases h' : find? t v <;> simp [h'] at *
intro h
cases h <;> cases h' : find? t v <;> simp [h', *]
```

**lean_error:** tail step 1/5 ('split_iff'): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1102, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList, mem_toList, mem_insert ht₂ ht₁]
simp [find?_eq_toList]
```

**lean_error:** tail step 1/2 ('rw [mem_toList, mem_toList, mem_insert ht₂ ht₁]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1069, out=38)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList, RBSet.insert, mem_insert ht₂ ht₁, mem_toList, find?_eq_find?, RBSet.find?_some]
simp [or_assoc]
```

**lean_error:** tail step 1/2 ('rw [mem_toList, RBSet.insert, mem_insert ht₂ ht₁, mem_toList, find?_eq_find?, RBSet.find?_some]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.1s, in=1091, out=444)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mem_toList, RBNode.mem_insert ht₂ ht₁]
simp [mem_toList]
```

**lean_error:** tail step 1/2 ('rw [mem_toList, RBNode.mem_insert ht₂ ht₁]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2589, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_toList, mem_toList, mem_insert ht₂ ht₁]
```

**lean_error:** tail step 1/1 ('rw [mem_toList, mem_toList, mem_insert ht₂ ht₁]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=2540, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_toList, mem_toList, ← RBNode.mem_insert ht₂ ht₁, find?_eq_find?_val]
simp [and_or_left, ← or_assoc, or_left_comm (v' = v)]
```

**lean_error:** tail step 1/2 ('rw [mem_toList, mem_toList, ← RBNode.mem_insert ht₂ ht₁, find?_eq_find?_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=2578, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mem_toList, RBNode.mem_insert ht₁ ht₂]
```

**lean_error:** tail step 1/1 ('rw [mem_toList, RBNode.mem_insert ht₁ ht₂]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=2626, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_toList, mem_toList, RBNode.mem_insert ht₂ ht₁]
```

**lean_error:** tail step 1/1 ('rw [mem_toList, mem_toList, RBNode.mem_insert ht₂ ht₁]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2767, out=38)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [mem_toList, RBSet.insert, RBNode.mem_insert ht₂ ht₁, find?_eq_find?_of_val]
simp [find?_eq_find?_of_val]
```

**lean_error:** tail step 1/2 ('simp [mem_toList, RBSet.insert, RBNode.mem_insert ht₂ ht₁, find?_eq_find?_of_val]'): unknown identifier 'find?_eq_find?_of_val'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 147.8s, verify 0.1s, in=2615, out=9270)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mem_toList, RBSet.mem_insert, mem_toList] at *
simp [ht₁, ht₂]
```

**lean_error:** tail step 1/2 ('rw [mem_toList, RBSet.mem_insert, mem_toList] at *'): tactic 'rewrite' failed, did not find instance of the pattern in the current goal
