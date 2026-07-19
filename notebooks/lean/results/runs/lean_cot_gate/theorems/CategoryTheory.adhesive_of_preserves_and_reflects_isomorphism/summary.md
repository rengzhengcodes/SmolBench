# CategoryTheory.adhesive_of_preserves_and_reflects_isomorphism   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Adhesive.lean`  

**Ground-truth tail (from k):**
```lean
exact adhesive_of_preserves_and_reflects F
```

**True premises at k:** `CategoryTheory.adhesive_of_preserves_and_reflects`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 117.6s, verify 0.1s, in=366, out=5243)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Adhesive.of_reflects_pullbacks_of_preserves_pushouts F inst✝⁶ inst✝² this✝ inst✝⁴ inst✝³ inst✝¹
```

**lean_error:** tail step 1/1 ('apply Adhesive.of_reflects_pullbacks_of_preserves_pushouts F inst✝⁶ inst✝² this✝ inst✝⁴ inst✝³ inst✝¹'): <stdin>:1:65: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 138.0s, verify 0.1s, in=366, out=6133)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply_instance
```

**lean_error:** tail step 1/1 ('apply_instance'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 146.8s, verify 0.1s, in=366, out=6498)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 157.5s, verify 0.1s, in=366, out=6923)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply_instance
```

**lean_error:** tail step 1/1 ('apply_instance'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=366, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=366, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=366, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=366, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): failed to synthesize instance

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.3s, verify 0.1s, in=366, out=224)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact adhesive_of_reflects_colimits_of_shape_and_preserves_limits_of_shape F _ _
```

**lean_error:** tail step 1/1 ('exact adhesive_of_reflects_colimits_of_shape_and_preserves_limits_of_shape F _ _'): unknown identifier 'adhesive_of_reflects_colimits_of_shape_and_preserves_limits_of_shape'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.0s, verify 0.1s, in=366, out=286)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply adhesiveOfReflective
```

**lean_error:** tail step 1/1 ('apply adhesiveOfReflective'): unknown identifier 'adhesiveOfReflective'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.8s, verify 0.1s, in=366, out=360)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact adhesive_of_reflects_colimits_of_shape_of_reflects_limits_of_shape F
```

**lean_error:** tail step 1/1 ('exact adhesive_of_reflects_colimits_of_shape_of_reflects_limits_of_shape F'): unknown identifier 'adhesive_of_reflects_colimits_of_shape_of_reflects_limits_of_shape'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.2s, verify 0.1s, in=366, out=414)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact adhesive_of_has_pullbacks_of_reflects_pullbacks_of_reflects_isomorphisms F this✝ inst✝
```

**lean_error:** tail step 1/1 ('exact adhesive_of_has_pullbacks_of_reflects_pullbacks_of_reflects_isomorphisms F this✝ inst✝'): <stdin>:1:85: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 17.2s, verify 0.1s, in=1025, out=694)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 29.0s, verify 0.1s, in=1025, out=1160)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 35.1s, verify 0.1s, in=1025, out=1393)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 51.6s, verify 0.1s, in=1025, out=2187)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=1025, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.6s, verify 0.1s, in=1025, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=1025, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects
```

**lean_error:** tail step 1/1 ('apply adhesive_of_preserves_and_reflects'): failed to synthesize

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.8s, verify 0.1s, in=1025, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1025, out=199)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.2s, verify 0.1s, in=1025, out=233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.6s, verify 0.1s, in=1025, out=267)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.8s, verify 0.1s, in=1025, out=280)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 40.2s, verify 0.1s, in=2918, out=943)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 44.8s, verify 0.1s, in=2918, out=866)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 46.4s, verify 0.1s, in=2918, out=754)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 131.3s, verify 0.1s, in=2918, out=4726)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.1s, verify 0.1s, in=2918, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.1s, verify 0.1s, in=2918, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=2918, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.3s, verify 0.1s, in=2918, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 14.1s, verify 0.1s, in=2918, out=249)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 15.1s, verify 0.1s, in=2918, out=289)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.3s, verify 0.1s, in=2918, out=257)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.7s, verify 0.1s, in=2918, out=322)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 24.3s, verify 0.1s, in=2945, out=970)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 27.9s, verify 0.1s, in=2945, out=1114)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 42.4s, verify 0.1s, in=2945, out=1740)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F inst✝⁵ inst✝⁴ inst✝³ inst✝² inst✝ inst✝¹ inst✝
```

**lean_error:** tail step 1/1 ('apply adhesive_of_preserves_and_reflects F inst✝⁵ inst✝⁴ inst✝³ inst✝² inst✝ inst✝¹ inst✝'): <stdin>:1:47: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 60.1s, verify 0.1s, in=2945, out=2615)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.7s, verify 0.1s, in=2945, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.9s, verify 0.1s, in=2945, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.9s, verify 0.1s, in=2945, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.0s, verify 0.1s, in=2945, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.7s, verify 0.1s, in=2945, out=238)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.4s, verify 0.1s, in=2945, out=266)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.5s, verify 0.1s, in=2945, out=266)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply adhesive_of_preserves_and_reflects F
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.6s, verify 0.1s, in=2945, out=274)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact adhesive_of_preserves_and_reflects F
```
