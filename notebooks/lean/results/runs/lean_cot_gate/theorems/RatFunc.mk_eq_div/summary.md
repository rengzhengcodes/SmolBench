# RatFunc.mk_eq_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**True premises at k:** `RatFunc.mk_eq_div'`, `RatFunc.ofFractionRing_div`, `RatFunc.ofFractionRing_algebraMap`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ |
| `hint:2` | · ✓ · · | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ · | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |
| `noise:3` | ✓ ✓ · ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 29.7s, verify 0.1s, in=266, out=1039)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.mk_eq_div]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 120.5s, verify 0.1s, in=266, out=4782)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 150.2s, verify 0.1s, in=266, out=6109)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Localization.algebraMap_eq_mk, Localization.algebraMap_eq_mk]
rw [div_eq_mul_inv]
rw [RatFunc.inv_mk]
rw [RatFunc.mul_mk]
simp only [Polynomial.mul_one, one_mul]
```

**lean_error:** tail step 1/5 ('rw [Localization.algebraMap_eq_mk, Localization.algebraMap_eq_mk]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 194.3s, verify 0.1s, in=266, out=8085)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [div_eq_mul_inv, RatFunc.algebraMap_def, RatFunc.inv_def, RatFunc.mul_def, one_mul, mul_one]
```

**lean_error:** tail step 1/1 ('rw [div_eq_mul_inv, RatFunc.algebraMap_def, RatFunc.inv_def, RatFunc.mul_def, one_mul, mul_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=266, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mk_eq_div]
```

**lean_error:** tail step 1/1 ('rw [mk_eq_div]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=266, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [div_eq_mul_inv]
```

**lean_error:** tail step 1/1 ('simp [div_eq_mul_inv]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=266, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div, div_eq_mul_inv, div_eq_mul_inv, map_mul, map_inv]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.mk_eq_div, div_eq_mul_inv, div_eq_mul_inv, map_mul, map_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=266, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← mk_one, mk_mul_mk, div_eq_mul_inv, ← mk_inv, mk_mul_mk, one_mul, mul_one]
```

**lean_error:** tail step 1/1 ('rw [← mk_one, mk_mul_mk, div_eq_mul_inv, ← mk_inv, mk_mul_mk, one_mul, mul_one]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.2s, verify 0.1s, in=266, out=145)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [RatFunc.mk_eq_div]
```

**lean_error:** tail step 1/1 ('simp [RatFunc.mk_eq_div]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.6s, verify 0.1s, in=266, out=184)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact RatFunc.div_eq_mk p q
```

**lean_error:** tail step 1/1 ('exact RatFunc.div_eq_mk p q'): unknown constant 'RatFunc.div_eq_mk'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 7.3s, verify 0.1s, in=266, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.mk]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.1s, verify 0.1s, in=266, out=374)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.inv_def, RatFunc.div_def]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.mk_eq_div, RatFunc.inv_def, RatFunc.div_def]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 39.7s, verify 0.1s, in=782, out=1571)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ (algebraMap K[X] (RatFunc K)) p / { toFractionRing := (algebraMap K[X] (FractionRing K[X])) q } =
    (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 128.0s, verify 0.3s, in=782, out=5135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div']
rw [← ofFractionRing_algebraMap, ← ofFractionRing_algebraMap]
rw [ofFractionRing_div]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 130.2s, verify 0.1s, in=782, out=5230)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ (algebraMap K[X] (RatFunc K)) p / { toFractionRing := (algebraMap K[X] (FractionRing K[X])) q } =
    (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 166.3s, verify 0.3s, in=782, out=6802)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div']
rw [← ofFractionRing_algebraMap]
rw [ofFractionRing_div]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) p } /
      { toFractionRing := (algebraMap K[X] (FractionRing K[X])) q } =
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=782, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.1s, verify 0.1s, in=782, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.2s, verify 0.1s, in=782, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.4s, verify 0.1s, in=782, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 6.4s, verify 0.1s, in=782, out=176)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.1s, verify 0.1s, in=782, out=195)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.2s, verify 0.1s, in=782, out=236)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.8s, verify 0.1s, in=782, out=256)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 64.5s, verify 0.1s, in=1385, out=1367)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 69.8s, verify 0.1s, in=1385, out=1567)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 78.0s, verify 0.1s, in=1385, out=1139)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 128.4s, verify 0.1s, in=1385, out=3575)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ (algebraMap K[X] (RatFunc K)) p / { toFractionRing := (algebraMap K[X] (FractionRing K[X])) q } =
    (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=1385, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 1.1s, in=1385, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.8s, verify 0.5s, in=1385, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.3s, verify 0.1s, in=1385, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 14.2s, verify 0.1s, in=1385, out=292)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 14.3s, verify 0.1s, in=1385, out=259)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap,
  RatFunc.ofFractionRing_algebraMap]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap,"): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 15.9s, verify 0.1s, in=1385, out=336)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 18.3s, verify 0.7s, in=1385, out=441)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 30.1s, verify 0.1s, in=1409, out=1202)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 50.1s, verify 0.1s, in=1409, out=1957)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 52.0s, verify 0.1s, in=1409, out=2039)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

**final state (truncated):**
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ (algebraMap K[X] (RatFunc K)) p / { toFractionRing := (algebraMap K[X] (FractionRing K[X])) q } =
    (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 95.9s, verify 0.2s, in=1409, out=3829)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=1409, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=1409, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.1s, in=1409, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.3s, verify 0.1s, in=1409, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 6.7s, verify 0.1s, in=1409, out=184)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=1409, out=211)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.3s, verify 0.1s, in=1409, out=239)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [mk_eq_div', ofFractionRing_div, ofFractionRing_algebraMap, ofFractionRing_algebraMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.9s, verify 0.1s, in=1409, out=259)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap,
  RatFunc.ofFractionRing_algebraMap]
```

**lean_error:** tail step 1/2 ("rw [RatFunc.mk_eq_div', RatFunc.ofFractionRing_div, RatFunc.ofFractionRing_algebraMap,"): <stdin>:1:86: unexpected end of input; expected ']'
