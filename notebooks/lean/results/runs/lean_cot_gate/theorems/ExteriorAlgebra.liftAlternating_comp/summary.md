# ExteriorAlgebra.liftAlternating_comp   (k=6, 7 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**True premises at k:** `AlternatingMap.curryLeft_compAlternatingMap`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✘ | ✓ ✓ ✓ ✘ |
| `hint:2` | ✓ ✘ ✘ ✓ | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |
| `hint:3` | ✘ ✘ ✓ ✓ | ✓ ✘ ✘ ✘ | ✘ ✘ ✓ ✓ |
| `noise:3` | ✘ ✘ ✓ ✘ | ✓ ✘ ✘ ✘ | ✘ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 79.7s, verify 0.4s, in=511, out=2942)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
funext
intro i
rw [← LinearMap.compAlternatingMap_curryLeft]
```

**lean_error:** tail step 2/3 ('intro i'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 96.3s, verify 0.1s, in=511, out=3599)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext i
apply AlternatingMap.ext
ext v
simp [curryLeft_apply, LinearMap.compAlternatingMap_apply, Function.comp_apply]
```

**lean_error:** tail step 1/4 ('ext i'): no applicable extensionality theorem found for

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 120.9s, verify 0.1s, in=511, out=4639)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply funext, intro i
apply AlternatingMap.ext, intro v
calc
  (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m v
  = (LinearMap.compAlternatingMap g (f (Nat.succ i))) (Fin.cons m v) :=
  rfl
  = g (f (Nat.succ i) (Fin.cons m v)) :=
  rfl
  = g ((AlternatingMap.curryLeft (f (Nat.succ i)) m) v) :=
  rfl
  = (LinearMap.compAlternatingMap g (AlternatingMap.curryLeft (f (Nat.succ i)) m)) v :=
  rfl
```

**lean_error:** tail step 1/12 ('apply funext, intro i'): <stdin>:1:12: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 153.3s, verify 0.1s, in=511, out=6088)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr_arg (liftAlternating · x)
apply funext
intro i
ext v
simp [AlternatingMap.curryLeft, LinearMap.compAlternatingMap]
rfl
```

**lean_error:** tail step 1/6 ('congr_arg (liftAlternating · x)'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.7s, verify 0.4s, in=511, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.4s, in=511, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=511, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [curryLeft_compLinearMap]
```

**lean_error:** tail step 1/1 ('simp_rw [curryLeft_compLinearMap]'): unknown identifier 'curryLeft_compLinearMap'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.5s, verify 0.1s, in=511, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [liftAlternating_map_compAlternatingMap, hx]
```

**lean_error:** tail step 1/1 ('simp [liftAlternating_map_compAlternatingMap, hx]'): unknown identifier 'liftAlternating_map_compAlternatingMap'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.6s, verify 0.4s, in=511, out=209)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.4s, verify 0.4s, in=511, out=298)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 13.3s, verify 0.4s, in=511, out=423)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr <;> funext i <;> simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.1s, verify 0.1s, in=511, out=737)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact congr_arg (fun f => liftAlternating f x) (funext fun i => hx (fun j => AlternatingMap.curryLeft (f j) m) i)
```

**lean_error:** tail step 1/1 ('exact congr_arg (fun f => liftAlternating f x) (funext fun i => hx (fun j => AlternatingMap.curryLeft (f j) m) i)'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 26.7s, verify 0.4s, in=925, out=975)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
ext i
apply AlternatingMap.curryLeft_compAlternatingMap
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 36.1s, verify 0.2s, in=925, out=1321)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 66.9s, verify 0.5s, in=925, out=2468)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply congr_arg (liftAlternating · x)
ext i
exact AlternatingMap.curryLeft_compAlternatingMap g (f (Nat.succ i)) m
```

**lean_error:** tail step 3/3 ('exact AlternatingMap.curryLeft_compAlternatingMap g (f (Nat.succ i)) m'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 69.9s, verify 0.4s, in=925, out=2580)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
intro i
apply AlternatingMap.curryLeft_compAlternatingMap
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.4s, in=925, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=925, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('simp only [curryLeft_compAlternatingMap]'): unknown identifier 'curryLeft_compAlternatingMap'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.8s, verify 0.1s, in=925, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [liftAlternating_ι, AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('simp_rw [liftAlternating_ι, AlternatingMap.curryLeft_compAlternatingMap]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.1s, verify 0.2s, in=925, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [liftAlternating_ι_mul, liftAlternating_ι_mul, ← hx, AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [liftAlternating_ι_mul, liftAlternating_ι_mul, ← hx, AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.8s, verify 0.2s, in=925, out=151)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.0s, verify 0.2s, in=925, out=157)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.8s, verify 0.2s, in=925, out=183)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.6s, verify 0.4s, in=925, out=271)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 51.9s, verify 0.3s, in=1115, out=626)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply funext
intro i
apply AlternatingMap.curryLeft_compAlternatingMap
```

**lean_error:** tail step 1/3 ('apply funext'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 80.1s, verify 0.2s, in=1115, out=1963)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 137.7s, verify 0.4s, in=1115, out=3531)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
funext i
apply AlternatingMap.curryLeft_compAlternatingMap
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 152.7s, verify 0.4s, in=1115, out=4731)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
intro i
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.4s, verify 0.4s, in=1115, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.3s, verify 0.1s, in=1115, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [liftAlternating_ι_mul, curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('simp [liftAlternating_ι_mul, curryLeft_compAlternatingMap]'): unknown identifier 'curryLeft_compAlternatingMap'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.5s, verify 0.1s, in=1115, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [liftAlternating_ι, map_zero, map_zero', AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ("simp only [liftAlternating_ι, map_zero, map_zero', AlternatingMap.curryLeft_compAlternatingMap]"): unknown identifier 'map_zero''

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.6s, verify 0.1s, in=1115, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [liftAlternating_ι_apply, LinearMap.compAlternatingMap_apply, map_zero, ←
  AlternatingMap.curryLeft_compAlternatingMap, hx]
```

**lean_error:** tail step 1/2 ('simp_rw [liftAlternating_ι_apply, LinearMap.compAlternatingMap_apply, map_zero, ←'): <stdin>:1:81: unexpected end of input

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.1s, verify 0.2s, in=1115, out=157)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.3s, verify 0.2s, in=1115, out=173)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.1s, verify 0.4s, in=1115, out=220)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 14.0s, verify 0.4s, in=1115, out=259)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 34.7s, verify 0.2s, in=1139, out=1270)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 49.8s, verify 0.1s, in=1139, out=1828)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext i
apply AlternatingMap.curryLeft_compAlternatingMap
```

**lean_error:** tail step 1/2 ('ext i'): no applicable extensionality theorem found for

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 56.5s, verify 0.4s, in=1139, out=2072)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
ext i
apply AlternatingMap.curryLeft_compAlternatingMap
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 144.4s, verify 0.2s, in=1139, out=5645)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [AlternatingMap.curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.4s, in=1139, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.9s, verify 0.1s, in=1139, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [liftAlternating_ι_mul, AlternatingMap.compAlternatingMap_apply, hx]
```

**lean_error:** tail step 1/1 ('simp [liftAlternating_ι_mul, AlternatingMap.compAlternatingMap_apply, hx]'): unknown constant 'AlternatingMap.compAlternatingMap_apply'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.0s, verify 0.1s, in=1139, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [liftAlternating_ι, map_comp, AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('simp only [liftAlternating_ι, map_comp, AlternatingMap.curryLeft_compAlternatingMap]'): unknown identifier 'map_comp'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.4s, verify 0.1s, in=1139, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [liftAlternating_ι_apply, LinearMap.compAlternatingMap_apply, map_zero, ←
  AlternatingMap.curryLeft_compAlternatingMap, hx]
```

**lean_error:** tail step 1/2 ('simp_rw [liftAlternating_ι_apply, LinearMap.compAlternatingMap_apply, map_zero, ←'): <stdin>:1:81: unexpected end of input

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.5s, verify 0.2s, in=1139, out=179)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/1 ('rw [curryLeft_compAlternatingMap]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.1s, verify 0.4s, in=1139, out=221)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [AlternatingMap.curryLeft_compAlternatingMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.5s, verify 0.4s, in=1139, out=235)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [AlternatingMap.curryLeft_compAlternatingMap]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.0s, verify 0.4s, in=1139, out=279)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```
