# Set.Finite.latticeClosure   (k=1, 2 tactics total)

file: `Mathlib/Order/SupClosed.lean`  

**Ground-truth tail (from k):**
```lean
exact hs.infClosure.supClosure
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=304, out=702)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (hs.infClosure).supClosure
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 214.4s, verify 0.3s, in=256, out=28896)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : Set.Finite (infClosure s) := Set.Finite.infClosure hs
have h2 : Set.Finite (supClosure (infClosure s)) := Set.Finite.supClosure h1
exact h2
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.0s, verify 0.2s, in=251, out=310)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.Finite.supClosure
apply Set.Finite.infClosure
exact hs
```
