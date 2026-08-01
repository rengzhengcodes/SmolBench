# CategoryTheory.InjectiveResolution.toRightDerivedZero'_comp_iCycles   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Abelian/RightDerived.lean`  

**Ground-truth tail (from k):**
```lean
simp [toRightDerivedZero']
```

**True premises at k:** `CategoryTheory.InjectiveResolution.toRightDerivedZero'`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.6s, verify 0.2s, in=433, out=685)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [toRightDerivedZero', Category.assoc]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.8s, verify 0.7s, in=835, out=622)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp [toRightDerivedZero']
  simpa
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.5s, verify 0.7s, in=1562, out=665)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [InjectiveResolution.toRightDerivedZero']
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.2s, verify 0.4s, in=1507, out=679)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [InjectiveResolution.toRightDerivedZero']
simp
```
