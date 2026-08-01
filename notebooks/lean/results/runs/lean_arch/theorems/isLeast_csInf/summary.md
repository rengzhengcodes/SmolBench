# isLeast_csInf   (k=1, 2 tactics total)

file: `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨argminOn_mem _ _ _ _, fun a ha => argminOn_le id _ _ ha⟩
```

**True premises at k:** `Function.argminOn_mem`, `Function.argminOn_le`, `id`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.4s, in=298, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· apply argminOn_mem
· intro y hy
  apply argminOn_le _ _ _ hy hs
```

**lean_error:** tail step 3/4 ('· intro y hy'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=270, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsLeast, mem_argminOn hs]
exact min_mem _ _ hs
simp only [le_id]
```

**lean_error:** tail step 1/3 ('rw [IsLeast, mem_argminOn hs]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=287, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply argminOn_isLeast
```

**lean_error:** tail step 1/1 ('apply argminOn_isLeast'): unknown identifier 'argminOn_isLeast'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=961, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨argminOn_mem _ hs, _⟩
intro x hx
exact argminOn_le _ hx hs
```

**lean_error:** tail step 1/3 ("refine' ⟨argminOn_mem _ hs, _⟩"): application type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=926, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsLeast, sInf_mem, Function.argminOn_mem]
exact Function.argminOn_le _ (by assumption) hs
apply id_apply
```

**lean_error:** tail step 1/3 ('rw [IsLeast, sInf_mem, Function.argminOn_mem]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 34.2s, verify 0.1s, in=950, out=2083)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isLeast_mk (argminOn_mem s hs) (argminOn_le s)
```

**lean_error:** tail step 1/1 ('apply isLeast_mk (argminOn_mem s hs) (argminOn_le s)'): unknown identifier 'isLeast_mk'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2003, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨argminOn_mem s hs, fun a ha => argminOn_le s ha hs⟩
```

**lean_error:** tail step 1/1 ('exact ⟨argminOn_mem s hs, fun a ha => argminOn_le s ha hs⟩'): application type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1967, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨Function.argminOn_mem s hs, fun a ha => Function.argminOn_le s ha⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Function.argminOn_mem s hs, fun a ha => Function.argminOn_le s ha⟩'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1992, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isLeast.mk
exact argminOn_mem s hs
intro x hx
apply argminOn_le s hx hs
```

**lean_error:** tail step 1/4 ('apply isLeast.mk'): unknown identifier 'isLeast.mk'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2029, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨argminOn_mem s hs, fun a ha => argminOn_le s ha hs⟩
```

**lean_error:** tail step 1/1 ('exact ⟨argminOn_mem s hs, fun a ha => argminOn_le s ha hs⟩'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=2115, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨Function.argminOn_mem s hs, fun a ha => Function.argminOn_le s ha⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Function.argminOn_mem s hs, fun a ha => Function.argminOn_le s ha⟩'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2018, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isLeast_mk
exact argminOn_mem s hs
intros a ha
exact argminOn_le s ha
```

**lean_error:** tail step 1/4 ('apply isLeast_mk'): unknown identifier 'isLeast_mk'
