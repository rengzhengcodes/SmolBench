# Set.Finite.latticeClosure   (k=1, 2 tactics total)

file: `Mathlib/Order/SupClosed.lean`  

**Ground-truth tail (from k):**
```lean
exact hs.infClosure.supClosure
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=266, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Set.Finite.supClosure (Set.Finite.infClosure hs)
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.3s, in=240, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← infClosure_eq_self_iff, ← supClosure_eq_self_iff]
exact hs.supClosure_infClosure
```

**lean_error:** tail step 1/2 ('rw [← infClosure_eq_self_iff, ← supClosure_eq_self_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.3s, in=255, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.Finite.supClosure
apply Set.Finite.infClosure
assumption
```
