# OrderEmbedding.birkhoffSet_apply   (k=1, 2 tactics total)

file: `Mathlib/Order/Birkhoff.lean`  

**Ground-truth tail (from k):**
```lean
convert rfl
```

**True premises at k:** `rfl`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=261, out=111)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 5.7s, verify 0.1s, in=261, out=224)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 6.5s, verify 0.1s, in=261, out=236)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refl
```

**lean_error:** tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 30.5s, verify 0.1s, in=261, out=1287)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=261, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=261, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=261, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=261, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=261, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.1s, in=261, out=63)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 3.1s, verify 0.1s, in=261, out=67)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 3.2s, verify 0.1s, in=261, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 5.2s, verify 0.1s, in=567, out=206)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 5.8s, verify 0.1s, in=567, out=230)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 7.6s, verify 0.1s, in=567, out=299)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 7.7s, verify 0.1s, in=567, out=304)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=567, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=567, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=567, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=567, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 3.4s, verify 0.1s, in=567, out=75)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 3.7s, verify 0.1s, in=567, out=85)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.0s, verify 0.1s, in=567, out=94)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.2s, verify 0.1s, in=567, out=96)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 8.9s, verify 0.1s, in=1052, out=216)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 9.0s, verify 0.1s, in=1052, out=242)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 9.4s, verify 0.1s, in=1052, out=194)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 9.5s, verify 0.1s, in=1052, out=168)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.1s, in=1052, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=1052, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=1052, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=1052, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=1052, out=76)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 5.7s, verify 0.1s, in=1052, out=85)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 6.2s, verify 0.1s, in=1052, out=99)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.3s, verify 0.1s, in=1052, out=80)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 3.5s, verify 0.1s, in=1076, out=134)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 4.5s, verify 0.1s, in=1076, out=171)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 8.1s, verify 0.1s, in=1076, out=321)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 9.6s, verify 0.1s, in=1076, out=384)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.6s, verify 0.1s, in=1076, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1076, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=1076, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=1076, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 3.3s, verify 0.1s, in=1076, out=73)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.1s, verify 0.1s, in=1076, out=96)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.2s, verify 0.1s, in=1076, out=97)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 4.7s, verify 0.1s, in=1076, out=117)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```
