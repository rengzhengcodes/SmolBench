# antitone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**True premises at k:** `antitone_toDual_comp_iff`, `monotone_comp_ofDual_iff`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.2s, in=351, out=2253)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Antitone, Function.comp]
```

**lean_error:** tail step 1/1 ('simpa [Antitone, Function.comp]'): tactic 'assumption' failed

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=700, out=1214)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Function.comp] using
  (antitone_toDual_comp_iff (f := f ∘ ofDual) (α := αᵒᵈ)).trans
    (monotone_comp_ofDual_iff (f := f))
```

**lean_error:** tail step 1/3 ('simpa [Function.comp] using'): <stdin>:1:27: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.2s, verify 0.1s, in=1052, out=1237)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Function.comp] using (antitone_toDual_comp_iff (f := f ∘ ofDual)).trans (monotone_comp_ofDual_iff (f := f))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=1028, out=1858)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Function.comp] using (antitone_toDual_comp_iff (f := f ∘ ofDual)).trans (monotone_comp_ofDual_iff (f := f))
```
