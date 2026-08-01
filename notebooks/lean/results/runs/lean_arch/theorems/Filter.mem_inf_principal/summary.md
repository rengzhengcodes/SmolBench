# Filter.mem_inf_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=298, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
constructor
· intro h
  apply mem_of_superset h
  intro x
  simp
  tauto
· intro h
  apply mem_of_superset h
  intro x
  simp
  tauto
```

**lean_error:** tail step 1/12 ('ext'): applyExtTheorem only applies to equations, not

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=270, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [compl_union, compl_compl]
simp only [mem_setOf_eq, not_not]
rfl
```

**lean_error:** tail step 1/3 ('rw [compl_union, compl_compl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.1s, in=287, out=579)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.compl_union]
```

**lean_error:** tail step 1/1 ('rw [Set.compl_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
