# CategoryTheory.MorphismProperty.LeftFraction.map_eq_iff   (k=7, 8 tactics total)

file: `Mathlib/CategoryTheory/Localization/CalculusOfFractions.lean`  

**Ground-truth tail (from k):**
```lean
exact Quot.sound h
```

**True premises at k:** `Quot.sound`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=330, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Localization.Hom.mk_eq_mk_iff.mpr h
```

**lean_error:** tail step 1/1 ('exact Localization.Hom.mk_eq_mk_iff.mpr h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=305, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Localization.Hom.ext
intro Z
simp only [Localization.Hom.mk, assoc, ← L.map_comp, ← φ.hg, ← ψ.hg, h.w]
rw [L.map_comp, L.map_comp]
```

**lean_error:** tail step 1/4 ('apply Localization.Hom.ext'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=319, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Localization.Hom.mk_eq
exact h
```

**lean_error:** tail step 1/2 ('apply Localization.Hom.mk_eq'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1010, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.9s, in=969, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Quot.sound h
```
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=999, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=2955, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=2928, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=2944, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound h
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=2981, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=3163, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h ```
```

**lean_error:** tail step 1/1 ('exact Quot.sound h ```'): <stdin>:1:22: unexpected end of input

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=2970, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```
