# inf_eq_and_sup_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/Order/Lattice.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

**True premises at k:** `inf_idem`, `sup_idem`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=249, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨inf_idem, sup_idem⟩
```

**lean_error:** tail step 1/1 ('exact ⟨inf_idem, sup_idem⟩'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact inf_idem b
exact sup_idem b
```

**lean_error:** tail step 1/2 ('exact inf_idem b'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=523, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
done
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.1s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=523, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```
