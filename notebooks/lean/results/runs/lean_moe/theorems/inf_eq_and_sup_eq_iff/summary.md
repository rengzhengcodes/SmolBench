# inf_eq_and_sup_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/Order/Lattice.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

**True premises at k:** `inf_idem`, `sup_idem`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=294, out=371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· exact inf_idem
· exact sup_idem
```

**lean_error:** tail step 2/3 ('· exact inf_idem'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=239, out=414)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idempotent b, sup_idempotent b⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idempotent b, sup_idempotent b⟩'): unknown identifier 'inf_idempotent'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=232, out=454)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [inf_idempotent, sup_idempotent]
```

**lean_error:** tail step 1/1 ('simp [inf_idempotent, sup_idempotent]'): unknown identifier 'inf_idempotent'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.7s, verify 0.1s, in=591, out=1893)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 31.1s, verify 0.1s, in=529, out=3532)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=516, out=402)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem b, sup_idem b⟩
```
