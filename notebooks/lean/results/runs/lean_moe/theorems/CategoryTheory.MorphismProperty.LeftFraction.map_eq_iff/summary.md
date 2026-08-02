# CategoryTheory.MorphismProperty.LeftFraction.map_eq_iff   (k=7, 8 tactics total)

file: `Mathlib/CategoryTheory/Localization/CalculusOfFractions.lean`  

**Ground-truth tail (from k):**
```lean
exact Quot.sound h
```

**True premises at k:** `Quot.sound`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.6s, verify 3.1s, in=370, out=364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Quot.sound
  exact h
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 71.6s, verify 0.1s, in=327, out=9552)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Localization.Hom.mk_eq_mk
<;> assumption
```

**lean_error:** tail step 1/2 ('apply Localization.Hom.mk_eq_mk'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=314, out=458)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Localization.Hom.mk_eq_mk h
```

**lean_error:** tail step 1/1 ('exact Localization.Hom.mk_eq_mk h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.7s, verify 0.6s, in=1056, out=643)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using Quot.sound h
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 16.5s, verify 0.1s, in=1038, out=2195)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_main : Localization.Hom.mk φ = Localization.Hom.mk ψ := by
  apply Quot.sound
  <;> assumption
exact h_main
```

**lean_error:** tail step 1/4 ('have h_main : Localization.Hom.mk φ = Localization.Hom.mk ψ := by'): <stdin>:1:65: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=1009, out=448)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=3054, out=668)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 32.1s, verify 0.2s, in=3072, out=4186)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.2s, in=3038, out=443)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.7s, verify 0.1s, in=2848, out=1395)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 30.5s, verify 0.1s, in=3377, out=3947)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.2s, in=3004, out=456)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```
