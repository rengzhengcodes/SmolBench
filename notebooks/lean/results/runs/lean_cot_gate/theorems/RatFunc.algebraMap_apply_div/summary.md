# RatFunc.algebraMap_apply_div   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
convert coe_div (algebraMap F[X] (RatFunc F) p) (algebraMap F[X] (RatFunc F) q) <;>
  rw [← mk_one, coe_def, coeAlgHom, mk_eq_div, liftAlgHom_apply_div, map_one, div_one,
    Algebra.ofId_apply]
```

**True premises at k:** `RatFunc.coe_div`, `algebraMap`, `RatFunc`, `algebraMap`, `RatFunc`, `RatFunc.mk_one`, `RatFunc.coe_def`, `RatFunc.coeAlgHom`, `RatFunc.mk_eq_div`, `RatFunc.liftAlgHom_apply_div`, `map_one`, `div_one`, `Algebra.ofId_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · · · ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ ✘ ✘ ✘ | · ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✓ | · · ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 123.8s, verify 0.1s, in=349, out=4880)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_div]
rw [algebra_map_comp]
rw [algebra_map_comp]
```

**lean_error:** tail step 1/3 ('rw [map_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 131.7s, verify 0.1s, in=349, out=5191)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RingHom.map_div, ← Algebra.algebra_map_comp F[X] (RatFunc F) (LaurentSeries F), ← Algebra.algebra_map_comp F[X] (RatFunc F) (LaurentSeries F)]
```

**lean_error:** tail step 1/1 ('rw [RingHom.map_div, ← Algebra.algebra_map_comp F[X] (RatFunc F) (LaurentSeries F), ← Algebra.algebra_map_comp F[X] (RatFunc F) (LaurentSeries F)]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 162.4s, verify 0.1s, in=349, out=6444)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_div, ← Function.comp_apply, ← Function.comp_apply, comp_algebraMap, comp_algebraMap]
```

**lean_error:** tail step 1/1 ('rw [map_div, ← Function.comp_apply, ← Function.comp_apply, comp_algebraMap, comp_algebraMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 212.2s, verify 0.7s, in=349, out=8823)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [div_eq_mul_inv]
rw [algebra_map_mul, algebra_map_inv]
rw [← algebra_map_comp F[X] (RatFunc F) (LaurentSeries F)]
rw [← algebra_map_comp F[X] (RatFunc F) (LaurentSeries F)]
```

**lean_error:** tail step 2/4 ('rw [algebra_map_mul, algebra_map_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=349, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=349, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RingHom.map_div, map_algebraMap]
```

**lean_error:** tail step 1/1 ('rw [RingHom.map_div, map_algebraMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=349, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [RatFunc.algebraMap_div, ← map_algebraMap]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.algebraMap_div, ← map_algebraMap]'): unknown constant 'RatFunc.algebraMap_div'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=349, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [RatFunc.algebraMap_div, RatFunc.algebraMap_eq, RatFunc.algebraMap_eq]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.algebraMap_div, RatFunc.algebraMap_eq, RatFunc.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.0s, verify 0.1s, in=349, out=260)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply map_div
```

**lean_error:** tail step 1/1 ('apply map_div'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 10.2s, verify 0.1s, in=349, out=297)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.7s, verify 0.1s, in=349, out=423)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Algebra.algebraMap_div, Algebra.algebraMap_eq, Algebra.algebraMap_eq]
```

**lean_error:** tail step 1/1 ('rw [Algebra.algebraMap_div, Algebra.algebraMap_eq, Algebra.algebraMap_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.8s, verify 0.1s, in=349, out=442)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_div, RingHom.comp_apply, RingHom.comp_apply]
```

**lean_error:** tail step 1/1 ('rw [map_div, RingHom.comp_apply, RingHom.comp_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 72.6s, verify 0.2s, in=2296, out=2944)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact RatFunc.liftAlgHom_apply_div p q
```

**lean_error:** tail step 1/1 ('exact RatFunc.liftAlgHom_apply_div p q'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 96.8s, verify 0.1s, in=2296, out=3830)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.liftAlgHom_apply_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.liftAlgHom_apply_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 105.0s, verify 0.1s, in=2296, out=4131)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply RatFunc.liftAlgHom_apply_div p q
```

**lean_error:** tail step 1/1 ('apply RatFunc.liftAlgHom_apply_div p q'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 149.3s, verify 0.1s, in=2296, out=5859)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply RatFunc.liftAlgHom_apply_div p q
```

**lean_error:** tail step 1/1 ('apply RatFunc.liftAlgHom_apply_div p q'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.9s, verify 0.1s, in=2296, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [RatFunc.mk_eq_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.1s, verify 0.1s, in=2296, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [RatFunc.mk_eq_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.9s, verify 0.1s, in=2296, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, RatFunc.mk_eq_div, RatFunc.coe_def]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.1s, in=2296, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.coeAlgHom, liftAlgHom_apply_div, ofId_apply,
  RatFunc.coe_def]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.mk_eq_div, RatFunc.coeAlgHom, liftAlgHom_apply_div, ofId_apply,'): <stdin>:1:82: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.8s, verify 0.1s, in=2296, out=321)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.coe_div]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.coe_div]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.5s, verify 0.1s, in=2296, out=465)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.coe_div]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.coe_div]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 22.2s, verify 0.1s, in=2296, out=664)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [RatFunc.coe_div, coe_def, algebraMap, RatFunc, algebraMap, RatFunc.mk_one, coeAlgHom,
  RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div, map_one, div_one, Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.coe_div, coe_def, algebraMap, RatFunc, algebraMap, RatFunc.mk_one, coeAlgHom,'): <stdin>:1:96: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 25.4s, verify 0.1s, in=2296, out=743)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← mk_eq_div p 1, ← mk_eq_div q 1, coeAlgHom_apply, coeAlgHom_apply, map_one, map_one,
  div_one, div_one]
```

**lean_error:** tail step 1/2 ('rw [← mk_eq_div p 1, ← mk_eq_div q 1, coeAlgHom_apply, coeAlgHom_apply, map_one, map_one,'): <stdin>:1:89: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 96.6s, verify 0.1s, in=5027, out=1902)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply RatFunc.liftAlgHom_apply_div
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 147.7s, verify 0.2s, in=5027, out=2968)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply RatFunc.coe_div
```

**lean_error:** tail step 1/1 ('apply RatFunc.coe_div'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 238.6s, verify 0.1s, in=5027, out=7435)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div]
apply liftAlgHom_apply_div
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.mk_eq_div]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 292.8s, verify 0.1s, in=5027, out=9180)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_div], rw [coeAlgHom], rw [liftAlgHom_apply_div], simp [Algebra.ofId_apply]
```

**lean_error:** tail step 1/1 ('rw [mk_eq_div], rw [coeAlgHom], rw [liftAlgHom_apply_div], simp [Algebra.ofId_apply]'): <stdin>:1:14: expected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 3.1s, verify 0.1s, in=5027, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [RatFunc.mk_eq_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=5027, out=48)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.coeAlgHom, RatFunc.coe_def, coeAlgHom_apply, RatFunc.mk_eq_div,
  RatFunc.liftAlgHom_apply_div, Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.coeAlgHom, RatFunc.coe_def, coeAlgHom_apply, RatFunc.mk_eq_div,'): <stdin>:1:82: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.8s, verify 0.1s, in=5027, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, coeAlgHom_apply_div, RatFunc.coeAlgHom, RatFunc.coe_def,
  coeAlgHom_apply_div, map_div₀]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.mk_eq_div, coeAlgHom_apply_div, RatFunc.coeAlgHom, RatFunc.coe_def,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.9s, verify 0.1s, in=5027, out=106)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.coe_def, RatFunc.coeAlgHom, coeAlgHom, liftAlgHom,
  RatFunc.liftMonoidWithZeroHom_apply_div, RatFunc.algebraMap_apply, Algebra.ofId_apply,
  Polynomial.algebraMap_apply, RatFunc.algebraMap_apply, Algebra.ofId_apply,
  Polynomial.algebraMap_apply, RatFunc.algebraMap_apply, Algebra.ofId_apply,
  Polynomial.algebraMap_apply]
```

**lean_error:** tail step 1/5 ('simp only [RatFunc.mk_eq_div, RatFunc.coe_def, RatFunc.coeAlgHom, coeAlgHom, liftAlgHom,'): <stdin>:1:88: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 21.4s, verify 0.1s, in=5027, out=285)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [RatFunc.coe_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 26.1s, verify 0.2s, in=5027, out=439)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply RatFunc.coe_div
```

**lean_error:** tail step 1/1 ('apply RatFunc.coe_div'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 29.7s, verify 0.1s, in=5027, out=606)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.coe_div, algebraMap, RatFunc, algebraMap, RatFunc.coe_def, RatFunc.coeAlgHom,
  RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div, map_one, div_one, Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.coe_div, algebraMap, RatFunc, algebraMap, RatFunc.coe_def, RatFunc.coeAlgHom,'): <stdin>:1:96: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 31.8s, verify 0.2s, in=5027, out=697)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply RatFunc.coe_div
```

**lean_error:** tail step 1/1 ('apply RatFunc.coe_div'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 46.6s, verify 0.1s, in=5051, out=1908)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.liftAlgHom_apply_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.liftAlgHom_apply_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 61.5s, verify 0.2s, in=5051, out=2508)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.liftAlgHom_apply_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.liftAlgHom_apply_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 69.6s, verify 0.1s, in=5051, out=2828)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.liftAlgHom_apply_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.liftAlgHom_apply_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 181.2s, verify 0.1s, in=5051, out=7301)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply RatFunc.liftAlgHom_apply_div
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.2s, verify 0.1s, in=5051, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [RatFunc.mk_eq_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.0s, verify 0.1s, in=5051, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, RatFunc.mk_eq_div, RatFunc.coe_div]
```

**final state (truncated):**
```
K F : Type u
inst✝ : Field F
p q : F[X]
f g : RatFunc F
⊢ (algebraMap (RatFunc F) (LaurentSeries F)) ((algebraMap F[X] (RatFunc F)) p / (algebraMap F[X] (RatFunc F)) q) =
    (ofPowerSeries ℤ F) ↑p / (ofPowerSeries ℤ F) ↑q
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.3s, verify 0.1s, in=5051, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, map_div₀,
  Algebra.ofId_apply]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.mk_eq_div, RatFunc.coeAlgHom, RatFunc.liftAlgHom_apply_div, map_div₀,'): <stdin>:1:88: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=5051, out=48)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [RatFunc.coeAlgHom, RatFunc.coe_def, RatFunc.liftAlgHom_apply_div,
  RatFunc.algebraMap_apply, ofId_apply, RatFunc.mk_eq_div]
```

**lean_error:** tail step 1/2 ('simp only [RatFunc.coeAlgHom, RatFunc.coe_def, RatFunc.liftAlgHom_apply_div,'): <stdin>:1:76: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.0s, verify 0.1s, in=5051, out=235)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.coe_div]
```

**lean_error:** tail step 1/1 ('rw [RatFunc.coe_div]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=5051, out=397)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.mk_one, RatFunc.coe_div]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.mk_eq_div, RatFunc.mk_one, RatFunc.coe_div]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.0s, verify 0.1s, in=5051, out=399)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [RatFunc.coe_div]
```

**lean_error:** tail step 1/1 ('simp_rw [RatFunc.coe_div]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.7s, verify 0.1s, in=5051, out=419)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.mk_eq_div, RatFunc.liftAlgHom_apply_div]'): simp made no progress
