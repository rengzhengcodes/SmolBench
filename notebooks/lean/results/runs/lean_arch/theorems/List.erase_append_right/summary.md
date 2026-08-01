# List.erase_append_right   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact h h'
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=268, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact absurd h h'
```

**lean_error:** tail step 1/1 ("exact absurd h h'"): application type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=242, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LawfulBEq.eq_of_beq] at h''
subst b
exact h h'
```

**lean_error:** tail step 1/3 ("rw [LawfulBEq.eq_of_beq] at h''"): tactic 'rewrite' failed, pattern is a metavariable

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=257, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
contradiction
```
