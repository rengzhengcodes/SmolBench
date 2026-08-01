# List.erase_append_right   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact h h'
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✓ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **success**  (gen 0.4s, verify 0.1s, in=268, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact absurd h' h
```

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.5s, verify 0.1s, in=268, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact absurd h h'
```

**lean_error:** tail step 1/1 ("exact absurd h h'"): application type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=268, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact absurd h' h
```

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=268, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact absurd h h'
```

**lean_error:** tail step 1/1 ("exact absurd h h'"): application type mismatch
