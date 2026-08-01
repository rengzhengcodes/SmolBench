# String.extract.go₁_add_right_cancel   (k=7, 8 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact ih
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 0.2s, verify 0.1s, in=406, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ih
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 1.2s, in=380, out=47)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [go₁]
split
· simp_all only [add_assoc, Nat.add_comm n]
· simp_all only [add_assoc, Nat.add_comm n]
· simp_all only [add_assoc, Nat.add_comm n]
```

**lean_error:** tail step 1/5 ('rw [go₁]'): failed to rewrite using equation theorems for 'String.extract.go₁'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=395, out=109)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ih
```
