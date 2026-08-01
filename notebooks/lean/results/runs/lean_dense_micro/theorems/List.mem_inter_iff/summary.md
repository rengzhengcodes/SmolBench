# List.mem_inter_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases l₁ <;> simp [List.inter_def, mem_filter]
```

**True premises at k:** `List.inter_def`, `List.mem_filter`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.4s, verify 0.1s, in=258, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact mem_inter_iff
```

**lean_error:** tail step 1/1 ('exact mem_inter_iff'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.4s, verify 0.1s, in=258, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Mem.inter_iff
```

**lean_error:** tail step 1/1 ('exact Mem.inter_iff'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=258, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.inter]
rfl
```

**lean_error:** tail step 1/2 ('rw [List.inter]'): failed to rewrite using equation theorems for 'List.inter'

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=258, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Iff.intro 
  (fun h => 
    And.intro 
      (List.mem_inter.mp h).left 
      (List.mem_inter.mp h).right) 
  (fun h => List.mem_inter.mpr h)
```

**lean_error:** tail step 1/6 ('exact Iff.intro'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.6s, verify 0.2s, in=626, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
exact mem_filter
```

**lean_error:** tail step 2/2 ('exact mem_filter'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.8s, verify 0.2s, in=626, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
exact mem_filter
```

**lean_error:** tail step 2/2 ('exact mem_filter'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.0s, verify 0.2s, in=626, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
exact mem_filter
```

**lean_error:** tail step 2/2 ('exact mem_filter'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=626, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inter_def]
rw [mem_filter]
exact Iff.rfl
```

**lean_error:** tail step 3/3 ('exact Iff.rfl'): type mismatch
