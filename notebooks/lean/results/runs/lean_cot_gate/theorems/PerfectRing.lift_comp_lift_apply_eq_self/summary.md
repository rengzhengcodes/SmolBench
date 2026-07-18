# PerfectRing.lift_comp_lift_apply_eq_self   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

**True premises at k:** `PerfectRing.lift_comp_lift_apply`, `PerfectRing.lift_self_apply`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✓ ✘ ✓ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=404, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=404, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← lift_comp_lift, lift_id]
```

**lean_error:** tail step 1/1 ('rw [← lift_comp_lift, lift_id]'): failed to synthesize

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=404, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using map_lift_of_char (lift i j p) x
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=404, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [lift_frobenius, frobenius_iterate_apply, IsPRadical.lift_left]
```

**lean_error:** tail step 1/1 ('simp only [lift_frobenius, frobenius_iterate_apply, IsPRadical.lift_left]'): unknown identifier 'lift_frobenius'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=723, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=723, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [lift_comp_lift_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=723, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=723, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1215, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=1215, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=1215, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=1215, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [lift_comp_lift_apply, lift_self_apply]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1238, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=1238, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [lift_comp_lift_apply]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=1238, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [lift_comp_lift_apply, lift_self_apply]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=1238, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [lift_comp_lift_apply, lift_self_apply]
```
