# String.contains_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [contains, any_iff]
```

**True premises at k:** `String.contains`, `String.any_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=222, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold contains
exact Iff.rfl
```

**lean_error:** tail step 2/2 ('exact Iff.rfl'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 2.1s, in=196, out=68)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [contains]
simp [String.containsAux]
rw [Bool.eq_true_iff]
simp only [List.mem_iff_get]
constructor
  · intro h
    simp only [getElem_iff_mem, List.getElem]
    exact ⟨h, rfl⟩
  · rintro ⟨h, -⟩
    exact h
```

**lean_error:** tail step 2/10 ('simp [String.containsAux]'): unknown constant 'String.containsAux'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=211, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [contains, String.coe_to_list, List.mem_to_bool]
```

**lean_error:** tail step 1/1 ('rw [contains, String.coe_to_list, List.mem_to_bool]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=500, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold contains
rw any_iff
simp [Membership.mem, List.Mem] 
exact Iff.rfl
```

**lean_error:** tail step 2/4 ('rw any_iff'): <stdin>:1:3: expected '['

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=471, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [contains, any_iff]
simp only [List.mem_iff_get, beq_iff_eq, eq_comm]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 91.8s, verify 0.1s, in=489, out=5736)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [contains, any_iff]
simp [Bool.eq_eq]
```

**lean_error:** tail step 2/2 ('simp [Bool.eq_eq]'): unknown constant 'Bool.eq_eq'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1093, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold contains
rw any_iff
simp [Membership.mem, List.Mem]
constructor
intro h
cases h
simp
intro h
use c
simp
exact h
```

**lean_error:** tail step 2/11 ('rw any_iff'): <stdin>:1:3: expected '['

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=1074, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [String.contains, String.any_iff]
simp only [beq_iff_eq, List.mem_iff_exists_eq]
rfl
```

**lean_error:** tail step 2/3 ('simp only [beq_iff_eq, List.mem_iff_exists_eq]'): unknown constant 'List.mem_iff_exists_eq'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 18.9s, verify 0.1s, in=1082, out=1154)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [contains, any_iff]
```

**final state (truncated):**
```
s : String
c : Char
⊢ (∃ c_1, c_1 ∈ s.data ∧ (c_1 == c) = true) ↔ c ∈ s.data
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1117, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold contains
simp [any_iff]
simp [Membership.mem]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1155, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [contains, any_iff]
simp only [Char.eq_iff, beq_eq_true_iff, exists_eq_right']
exact List.mem_iff_exists_beq.symm
```

**lean_error:** tail step 2/3 ("simp only [Char.eq_iff, beq_eq_true_iff, exists_eq_right']"): unknown constant 'Char.eq_iff'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=1106, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [contains, any_iff]
constructor
· rw [exists_prop]
  rfl
· intro
  rw [exists_prop]
  simp
```

**lean_error:** tail step 3/7 ('· rw [exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
