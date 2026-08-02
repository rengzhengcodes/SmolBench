# RatFunc.mk_eq_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**True premises at k:** `RatFunc.mk_eq_div'`, `RatFunc.ofFractionRing_div`, `RatFunc.ofFractionRing_algebraMap`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=326, out=152)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.4s, verify 0.1s, in=274, out=5196)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.8s, verify 0.1s, in=276, out=700)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RatFunc.mk]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) p / (algebraMap K[X] (FractionRing K[X])) q } =
    (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.6s, verify 0.2s, in=843, out=585)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div']
  simpa [ofFractionRing_div, ofFractionRing_algebraMap]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 37.0s, verify 0.8s, in=796, out=4260)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
have h₁ : ofFractionRing (algebraMap _ _ p) = algebraMap _ _ p := by apply RatFunc.ofFractionRing_algebraMap
have h₂ : ofFractionRing (algebraMap _ _ q) = algebraMap _ _ q := by apply RatFunc.ofFractionRing_algebraMap
rw [h₁, h₂]
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.3s, in=813, out=582)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
rw [RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.4s, verify 0.3s, in=1464, out=1285)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
  rw [← RatFunc.ofFractionRing_algebraMap (x:=p), ← RatFunc.ofFractionRing_algebraMap (x:=q)]
  rw [← RatFunc.ofFractionRing_div]
  rfl
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 61.9s, verify 0.4s, in=1416, out=7702)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
have h₁ : ofFractionRing (algebraMap _ _ p) = algebraMap _ _ p := RatFunc.ofFractionRing_algebraMap
have h₂ : ofFractionRing (algebraMap _ _ q) = algebraMap _ _ q := RatFunc.ofFractionRing_algebraMap
rw [h₁, h₂]
<;> rfl
```

**lean_error:** tail step 3/6 ('have h₁ : ofFractionRing (algebraMap _ _ p) = algebraMap _ _ p := RatFunc.ofFractionRing_algebraMap'): type mismatch

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.1s, verify 0.3s, in=1440, out=515)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
rw [RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.6s, verify 0.3s, in=1414, out=831)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
rw [RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
rfl
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 27.0s, verify 0.2s, in=1535, out=3128)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : RatFunc.mk p q = ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) := RatFunc.mk_eq_div' p q
have h2 : ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) = ofFractionRing (algebraMap _ _ p) / ofFractionRing (algebraMap _ _ q) := by
  apply RatFunc.ofFractionRing_div
have h3 : ofFractionRing (algebraMap _ _ p) = algebraMap _ _ p := by
  apply RatFunc.ofFractionRing_algebraMap
have h4 : ofFractionRing (algebraMap _ _ q) = algebraMap _ _ q := by
  apply RatFunc.ofFractionRing_algebraMap
calc
  RatFunc.mk p q = ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) := h1
  _ = ofFractionRing (algebraMap _ _ p) / ofFractionRing (algebraMap _ _ q) := h2
  _ = algebraMap _ _ p / algebraMap _ _ q := by rw [h3, h4]
```

**lean_error:** tail step 2/11 ('have h2 : ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) = ofFractionRing (algebraMap _ _ p) / ofFractionRing (algebraMap _ _ q) := by'): <stdin>:1:140: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.3s, in=1446, out=611)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div']
rw [RatFunc.ofFractionRing_div]
rw [RatFunc.ofFractionRing_algebraMap, RatFunc.ofFractionRing_algebraMap]
```
