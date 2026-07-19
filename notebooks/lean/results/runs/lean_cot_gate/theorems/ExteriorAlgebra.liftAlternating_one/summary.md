# ExteriorAlgebra.liftAlternating_one   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rw [foldl_one]
```

**True premises at k:** `CliffordAlgebra.foldl_one`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✓ ✓ ✓ | ✘ ✓ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 33.6s, verify 0.2s, in=437, out=1516)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 52.9s, verify 0.1s, in=437, out=2338)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 55.7s, verify 0.1s, in=437, out=2453)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 103.7s, verify 0.1s, in=437, out=4284)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=437, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.2s, verify 0.2s, in=437, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.6s, verify 0.5s, in=437, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.4s, verify 0.4s, in=437, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 4.7s, verify 0.1s, in=437, out=143)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 6.6s, verify 0.2s, in=437, out=200)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [*]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.7s, verify 0.1s, in=437, out=248)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, map_zero]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, map_zero]'): unknown constant 'AlternatingMap.curryLeft_apply'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.7s, verify 0.1s, in=437, out=249)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [foldl_zero]
```

**lean_error:** tail step 1/1 ('simp [foldl_zero]'): unknown identifier 'foldl_zero'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 66.4s, verify 0.2s, in=690, out=2883)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [foldl_one]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 92.1s, verify 0.2s, in=690, out=3990)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 112.8s, verify 0.2s, in=690, out=4784)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
rfl
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 123.7s, verify 0.2s, in=690, out=5191)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.2s, in=690, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.2s, in=690, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.2s, in=690, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.2s, verify 0.3s, in=690, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.9s, verify 0.2s, in=690, out=351)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.1s, verify 0.1s, in=690, out=357)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one, LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, Fin.val_zero]
```

**lean_error:** tail step 1/1 ('rw [CliffordAlgebra.foldl_one, LinearMap.mk₂_apply, AlternatingMap.curryLeft_apply, Fin.val_zero]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 14.8s, verify 0.2s, in=690, out=436)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 21.3s, verify 0.2s, in=690, out=652)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 145.4s, verify 0.2s, in=1199, out=4611)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 156.3s, verify 0.2s, in=1199, out=5230)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one, LinearMap.map_zero]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 170.8s, verify 0.2s, in=1199, out=4702)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 211.0s, verify 0.1s, in=1199, out=6400)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CliffordAlgebra.foldl_one]
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.4s, verify 0.2s, in=1199, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.6s, verify 0.2s, in=1199, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 4.8s, verify 0.2s, in=1199, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [liftAlternating]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 5.1s, verify 0.2s, in=1199, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [liftAlternating, foldl_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.6s, verify 0.2s, in=1199, out=190)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 18.5s, verify 0.2s, in=1199, out=308)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 18.7s, verify 0.2s, in=1199, out=358)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 19.4s, verify 0.2s, in=1199, out=351)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 28.5s, verify 0.2s, in=1223, out=1337)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 72.7s, verify 0.2s, in=1223, out=3134)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 111.9s, verify 0.2s, in=1223, out=4749)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
rw [LinearMap.map_zero (f 0)]
rfl
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 122.6s, verify 0.2s, in=1223, out=5152)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CliffordAlgebra.foldl_one
rfl
```

**lean_error:** tail step 1/2 ('apply CliffordAlgebra.foldl_one'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.3s, in=1223, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.4s, verify 0.2s, in=1223, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [liftAlternating, foldl_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.8s, verify 0.3s, in=1223, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 4.1s, verify 0.2s, in=1223, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.1s, verify 0.2s, in=1223, out=230)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.2s, verify 0.2s, in=1223, out=264)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [foldl_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 11.2s, verify 0.2s, in=1223, out=327)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CliffordAlgebra.foldl_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.8s, verify 0.2s, in=1223, out=401)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [foldl_one, map_zero]
```
