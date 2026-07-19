# PiTensorProduct.map_range_eq_span_tprod   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Set.mem_range, comp_apply, map_tprod, Set.mem_setOf_eq]
```

**True premises at k:** `Set.mem_range`, `Function.comp_apply`, `PiTensorProduct.map_tprod`, `Set.mem_setOf_eq`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✘ ✓ ✓ ✘ |
| `hint:3` | ✓ ✘ ✘ ✘ | ✓ ✘ ✓ ✓ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✓ ✘ ✘ | ✓ ✓ ✘ ✘ | ✓ ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 97.3s, verify 0.1s, in=617, out=4136)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
refl
```

**lean_error:** tail step 1/2 ('ext x'): applyExtTheorem only applies to equations, not

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 112.4s, verify 0.2s, in=617, out=4744)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  · rintro ⟨m, rfl⟩
    use m
    exact map_tprod f m
  · rintro ⟨m, rfl⟩
    use m
    exact (map_tprod f m).symm
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 116.7s, verify 0.1s, in=617, out=4913)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
split
rintro ⟨y, rfl⟩
use y
rfl
rintro ⟨y, rfl⟩
use y
rfl
```

**lean_error:** tail step 1/8 ('ext x'): applyExtTheorem only applies to equations, not

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 188.7s, verify 0.2s, in=617, out=8132)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, map_tprod, eq_comm, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, map_tprod, eq_comm, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=617, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.9s, verify 0.1s, in=617, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_range]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=617, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, mem_range_tprod]
```

**lean_error:** tail step 1/1 ('simp only [Set.mem_range, Set.mem_setOf_eq, Function.comp_apply, mem_range_tprod]'): unknown identifier 'mem_range_tprod'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.1s, in=617, out=38)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Set.mem_range, exists_prop, Function.comp_apply, tprod_mem_tprod_range, exists_and_left,
  Classical.and_iff_right_iff_imp]
```

**lean_error:** tail step 1/2 ('simp only [Set.mem_range, exists_prop, Function.comp_apply, tprod_mem_tprod_range, exists_and_left,'): <stdin>:1:99: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.1s, verify 0.1s, in=617, out=287)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.7s, verify 0.1s, in=617, out=307)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.2s, verify 1.1s, in=617, out=357)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.4s, verify 0.1s, in=617, out=364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 32.0s, verify 0.2s, in=1248, out=1397)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 90.8s, verify 0.2s, in=1248, out=3868)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 126.0s, verify 0.2s, in=1248, out=5311)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]
rw [Set.mem_setOf_eq]
split
. intro h
  cases h with x hx
  use x
  exact hx
. intro h
  cases h with x hx
  use x
  exact hx
```

**lean_error:** tail step 1/11 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 129.2s, verify 0.2s, in=1248, out=5461)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
apply exists_congr (λ y => Iff.rfl)
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=1248, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=1248, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Set.mem_range, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=1248, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_setOf_eq, Set.mem_range, PiTensorProduct.map_tprod]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=1248, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, mem_setOf_eq, map_tprod]
```

**lean_error:** tail step 1/1 ('simp only [Set.mem_range, Function.comp_apply, mem_setOf_eq, map_tprod]'): unknown identifier 'mem_setOf_eq'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.9s, verify 0.2s, in=1248, out=411)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 15.4s, verify 0.1s, in=1248, out=461)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 17.0s, verify 0.1s, in=1248, out=504)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 18.6s, verify 0.2s, in=1248, out=557)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 124.6s, verify 0.1s, in=1462, out=2133)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 138.4s, verify 0.2s, in=1462, out=3842)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 145.1s, verify 0.2s, in=1462, out=2284)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 181.4s, verify 0.2s, in=1462, out=6394)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
exact Iff.rfl
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=1462, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Function.comp_apply, PiTensorProduct.map_tprod]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=1462, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,
  PiTensorProduct.map_tprod]
```

**lean_error:** tail step 1/2 ('simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,'): <stdin>:1:77: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 5.4s, verify 0.1s, in=1462, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Set.mem_range, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 5.5s, verify 0.1s, in=1462, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, Set.mem_setOf_eq, PiTensorProduct.map_tprod]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 24.1s, verify 0.2s, in=1462, out=390)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 25.6s, verify 0.2s, in=1462, out=520)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 25.9s, verify 0.2s, in=1462, out=467)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 27.2s, verify 0.2s, in=1462, out=585)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 46.8s, verify 0.2s, in=1487, out=2018)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 73.2s, verify 0.1s, in=1487, out=3119)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 122.2s, verify 0.2s, in=1487, out=5145)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 164.1s, verify 0.2s, in=1487, out=6975)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
refl
```

**lean_error:** tail step 1/2 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1487, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Set.mem_range, Set.mem_setOf_eq]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.4s, verify 0.1s, in=1487, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Function.comp, Set.mem_setOf_eq, Set.mem_range, PiTensorProduct.map_tprod]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1487, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, exists_prop, PiTensorProduct.map_tprod,
  Set.mem_setOf_eq]
```

**lean_error:** tail step 1/2 ('simp only [Set.mem_range, Function.comp_apply, exists_prop, PiTensorProduct.map_tprod,'): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=1487, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,
  PiTensorProduct.map_tprod]
```

**lean_error:** tail step 1/2 ('simp only [Function.comp_apply, exists_prop, Set.mem_range, Set.mem_setOf_eq,'): <stdin>:1:77: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.3s, verify 0.1s, in=1487, out=364)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.6s, verify 0.2s, in=1487, out=389)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

**lean_error:** tail step 1/1 ('rw [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.0s, verify 0.1s, in=1487, out=449)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 16.2s, verify 0.1s, in=1487, out=476)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Set.mem_range, Function.comp_apply, PiTensorProduct.map_tprod, Set.mem_setOf_eq]
```
