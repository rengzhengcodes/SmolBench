# Filter.mem_inf_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=346, out=1444)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 10.3s, verify 0.1s, in=285, out=1627)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : tᶜ ∪ s = {x | x ∉ t ∨ x ∈ s} := by
  apply Set.ext
  intro x
  simp only [Set.mem_union, Set.mem_compl_iff, Set.mem_setOf_eq]
  <;> tauto
rw [h]
<;> tauto
```

**lean_error:** tail step 1/7 ('have h : tᶜ ∪ s = {x | x ∉ t ∨ x ∈ s} := by'): <stdin>:1:43: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=283, out=533)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Set.mem_union, Set.mem_compl_iff, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('simp [Set.mem_union, Set.mem_compl_iff, Set.mem_setOf_eq]'): simp made no progress
