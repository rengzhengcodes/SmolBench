# autEquivRootsOfUnity_apply_rootOfSplit   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/KummerExtension.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.7s, verify 2.1s, in=429, out=660)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 101.3s, verify 0.1s, in=392, out=15154)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (↑↑η : L) • rootOfSplitsXPowSubC hn a L = (↑↑η : L) * rootOfSplitsXPowSubC hn a L := by rw [smul_eq_mul]
  _ = (↑(↑η : K) : L) * rootOfSplitsXPowSubC hn a L := by rfl
  _ = (↑(↑η : K) : L) • rootOfSplitsXPowSubC hn a L := by rw [smul_eq_mul]
  _ = (η : ↥(rootsOfUnity { val := n, property := hn } K)) • rootOfSplitsXPowSubC hn a L := by rw [Subtype.smul_def]
```

**lean_error:** tail step 1/5 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=376, out=471)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
