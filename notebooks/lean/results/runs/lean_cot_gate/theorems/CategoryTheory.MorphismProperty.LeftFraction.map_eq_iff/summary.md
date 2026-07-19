# CategoryTheory.MorphismProperty.LeftFraction.map_eq_iff   (k=7, 8 tactics total)

file: `Mathlib/CategoryTheory/Localization/CalculusOfFractions.lean`  

**Ground-truth tail (from k):**
```lean
exact Quot.sound h
```

**True premises at k:** `Quot.sound`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ · · ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ · ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | · ✓ ✓ ✓ | ✓ ✓ · ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 34.4s, verify 0.2s, in=307, out=1961)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Quotient.sound h
```

**lean_error:** tail step 1/1 ('exact Quotient.sound h'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 42.5s, verify 0.1s, in=307, out=2313)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (quotient.sound h)
```

**lean_error:** tail step 1/1 ('exact (quotient.sound h)'): unknown identifier 'quotient.sound'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 43.0s, verify 0.1s, in=307, out=2335)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LeftFractionRel.to_hom_eq h
```

**lean_error:** tail step 1/1 ('exact LeftFractionRel.to_hom_eq h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 93.9s, verify 0.1s, in=307, out=4348)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Quot.sound h
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=307, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

**lean_error:** tail step 1/1 ('simp [h]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=307, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Hom.eq_of_eq_mk _ _ h
```

**lean_error:** tail step 1/1 ('exact Hom.eq_of_eq_mk _ _ h'): unknown identifier 'Hom.eq_of_eq_mk'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=307, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact mk_eq_of_rel φ ψ h
```

**lean_error:** tail step 1/1 ('exact mk_eq_of_rel φ ψ h'): unknown identifier 'mk_eq_of_rel'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=307, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← mk_eq_of_eq_mk φ ψ, h]
```

**lean_error:** tail step 1/1 ('rw [← mk_eq_of_eq_mk φ ψ, h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.0s, verify 0.1s, in=307, out=131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact mk_eq_of_leftFractionRel h
```

**lean_error:** tail step 1/1 ('exact mk_eq_of_leftFractionRel h'): unknown identifier 'mk_eq_of_leftFractionRel'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.1s, verify 0.2s, in=307, out=158)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [mk'_eq_iff_eq]
```

**lean_error:** tail step 1/1 ("rwa [mk'_eq_iff_eq]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.4s, verify 0.1s, in=307, out=167)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Localization.Hom.eq
apply h
```

**lean_error:** tail step 1/2 ('apply Localization.Hom.eq'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=307, out=158)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 4.9s, verify 0.1s, in=987, out=246)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=987, out=277)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 6.0s, verify 0.1s, in=987, out=307)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 6.2s, verify 0.1s, in=987, out=321)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=987, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.0s, verify 0.1s, in=987, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound
```

**final state (truncated):**
```
case mpr.e_f.a
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=987, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound
```

**final state (truncated):**
```
case mpr.e_f.a
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=987, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=987, out=141)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.7s, verify 0.1s, in=987, out=148)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.6s, verify 0.1s, in=987, out=209)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.0s, verify 0.1s, in=987, out=220)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 9.2s, verify 0.1s, in=2937, out=203)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 10.8s, verify 3.8s, in=2937, out=297)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 18.6s, verify 1.4s, in=2937, out=801)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound
```

**final state (truncated):**
```
case mpr.e_f.a
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 19.9s, verify 0.1s, in=2937, out=721)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Quot.sound h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.0s, verify 0.1s, in=2937, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=2937, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.1s, verify 0.1s, in=2937, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=2937, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.9s, verify 0.1s, in=2937, out=154)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.6s, verify 0.1s, in=2937, out=194)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 11.7s, verify 0.1s, in=2937, out=188)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.8s, verify 0.1s, in=2937, out=193)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 4.7s, verify 0.2s, in=2961, out=243)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 5.1s, verify 0.1s, in=2961, out=247)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 6.3s, verify 0.2s, in=2961, out=324)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound
exact h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 6.6s, verify 0.1s, in=2961, out=337)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.1s, verify 0.1s, in=2961, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound
```

**final state (truncated):**
```
case mpr.e_f.a
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=2961, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=2961, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=2961, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.9s, verify 0.1s, in=2961, out=135)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.5s, verify 0.1s, in=2961, out=142)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 6.3s, verify 0.1s, in=2961, out=162)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Quot.sound
```

**final state (truncated):**
```
case mpr.e_f.a
C : Type u_1
D : Type u_2
inst✝³ : Category.{u_3, u_1} C
inst✝² : Category.{u_4, u_2} D
L : C ⥤ D
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.2s, verify 0.1s, in=2961, out=224)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Quot.sound h
```
