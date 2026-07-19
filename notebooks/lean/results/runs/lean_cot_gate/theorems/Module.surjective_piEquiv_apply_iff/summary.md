# Module.surjective_piEquiv_apply_iff   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [← LinearMap.range_eq_top, range_piEquiv]
```

**True premises at k:** `LinearMap.range_eq_top`, `Module.range_piEquiv`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 148.5s, verify 0.1s, in=309, out=6268)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [LinearMap.surjective_iff_range_eq_top]
rw [(piEquiv v).range_eq_span_range]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.surjective_iff_range_eq_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 161.6s, verify 0.1s, in=309, out=6902)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : (piEquiv ι R M v).range = span R (range v) := by
  apply le_antisymm
  · rintro x ⟨y, rfl⟩
    simp only [piEquiv_apply]
    apply Submodule.sum_mem
    intro i _
    apply Submodule.smul_mem
    exact Submodule.mem_span_self (v i)
  · apply span_le.mpr
    rintro x (mem_range.mp rfl)
    use Pi.single x 1
    simp [piEquiv_apply]
rw [h]
apply LinearMap.surjective_iff_range_eq
```

**lean_error:** tail step 1/14 ('have h : (piEquiv ι R M v).range = span R (range v) := by'): <stdin>:1:57: unexpected end of input; expected '{'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 188.8s, verify 0.1s, in=309, out=8227)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [linearMap.surjective_iff_range_eq_top]
rw [← linearMap.range_piEquiv_eq_span ι R M v]
rfl
```

**lean_error:** tail step 1/3 ('rw [linearMap.surjective_iff_range_eq_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 243.1s, verify 0.1s, in=309, out=10868)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← LinearMap.surjective_iff_hasFullRange]
have key : (piEquiv ι R M v).range = span R (range v) := by
  apply LinearMap.range_eq_span_image_basis (Pi.basisFun R ι)
  ext
  simp only [Pi.basisFun_apply, LinearMap.stdBasis, Function.comp_app]
  constructor
  · rintro ⟨i, rfl⟩
    use i
    rfl
  · rintro ⟨i, rfl⟩
    use i
    rfl
rw [key]
rfl
```

**lean_error:** tail step 1/14 ('rw [← LinearMap.surjective_iff_hasFullRange]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.8s, verify 0.1s, in=309, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.eq_top_iff']
```

**final state (truncated):**
```
ι : Type u_1
R : Type u_2
M : Type u_3
N : Type u_4
inst✝⁵ : Finite ι
inst✝⁴ : CommSemiring R
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=309, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [piEquiv_surjective_iff]
```

**lean_error:** tail step 1/1 ('simp [piEquiv_surjective_iff]'): unknown identifier 'piEquiv_surjective_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=309, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [piEquiv_surjective_iff, Submodule.span_eq_top]
```

**lean_error:** tail step 1/1 ('rw [piEquiv_surjective_iff, Submodule.span_eq_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.1s, verify 0.7s, in=309, out=116)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [piEquiv, Equiv.toFun_as_coe, Equiv.Perm.coe_mul, LinearEquiv.coe_comp, Function.comp,
  LinearEquiv.surjective_comp_iff, LinearEquiv.surjective_comp_left_iff,
  LinearEquiv.surjective_iff_range_eq, LinearEquiv.range_toEquiv, range_toSubmodule_eq_map,
  Submodule.map_top, Submodule.span_range_eq_map_dfinsupp, dfinsuppBasisFun_surjective,
  LinearEquiv.map_top]
```

**lean_error:** tail step 1/5 ('simp only [piEquiv, Equiv.toFun_as_coe, Equiv.Perm.coe_mul, LinearEquiv.coe_comp, Function.comp,'): <stdin>:1:96: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=309, out=124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.3s, verify 0.1s, in=309, out=152)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [piEquiv_surjective_iff]
```

**lean_error:** tail step 1/1 ('simp [piEquiv_surjective_iff]'): unknown identifier 'piEquiv_surjective_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.7s, verify 0.1s, in=309, out=537)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [linearMap_eq_top_iff_range_eq_top, LinearMap.range_eq_top]
```

**lean_error:** tail step 1/1 ('simp only [linearMap_eq_top_iff_range_eq_top, LinearMap.range_eq_top]'): unknown identifier 'linearMap_eq_top_iff_range_eq_top'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 22.9s, verify 0.1s, in=309, out=831)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.surjective_iff_range_eq_top, Submodule.range_coe_eq_span_range]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.surjective_iff_range_eq_top, Submodule.range_coe_eq_span_range]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 23.8s, verify 0.1s, in=659, out=1057)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 47.8s, verify 0.1s, in=659, out=2019)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.range_eq_top
rw Module.range_piEquiv
```

**lean_error:** tail step 1/2 ('apply LinearMap.range_eq_top'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 75.8s, verify 0.1s, in=659, out=3279)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_top, Module.range_piEquiv]
refl
```

**lean_error:** tail step 1/2 ('rw [range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 105.5s, verify 0.1s, in=659, out=4488)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=659, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [range_piEquiv, LinearMap.range_eq_top]
```

**lean_error:** tail step 1/1 ('simp [range_piEquiv, LinearMap.range_eq_top]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=659, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.1s, in=659, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=659, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.9s, verify 0.1s, in=659, out=276)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.1s, verify 0.1s, in=659, out=283)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [range_piEquiv, range_eq_top]
```

**lean_error:** tail step 1/1 ('simp only [range_piEquiv, range_eq_top]'): unknown identifier 'range_eq_top'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.5s, verify 0.4s, in=659, out=297)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.3s, verify 0.1s, in=659, out=358)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [← range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 52.3s, verify 0.1s, in=1224, out=1169)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 114.8s, verify 0.1s, in=1224, out=2840)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 167.4s, verify 0.1s, in=1224, out=4955)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Module.range_piEquiv]
apply LinearMap.range_eq_top
```

**lean_error:** tail step 1/2 ('rw [Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 168.8s, verify 0.1s, in=1224, out=6800)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Module.range_piEquiv, LinearMap.range_eq_top]
rfl
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1224, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=1224, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=1224, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=1224, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.range_eq_top, Module.range_piEquiv]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.6s, verify 1.0s, in=1224, out=277)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [← range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.5s, verify 0.1s, in=1224, out=258)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Module.range_piEquiv, LinearMap.range_eq_top]
```

**lean_error:** tail step 1/1 ('simp_rw [Module.range_piEquiv, LinearMap.range_eq_top]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.4s, verify 0.1s, in=1224, out=246)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.0s, verify 0.1s, in=1224, out=249)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 9.7s, verify 0.5s, in=1248, out=460)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have : LinearMap.range (piEquiv ι R M v) = span R (range v) := range_piEquiv v
rw [LinearMap.range_eq_top]
rw [this]
refl
```

**lean_error:** tail step 1/4 ('have : LinearMap.range (piEquiv ι R M v) = span R (range v) := range_piEquiv v'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 59.6s, verify 0.1s, in=1248, out=2570)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 66.3s, verify 0.1s, in=1248, out=2868)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 137.2s, verify 0.1s, in=1248, out=5793)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw LinearMap.range_eq_top
rw Module.range_piEquiv
rfl
```

**lean_error:** tail step 1/3 ('rw LinearMap.range_eq_top'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.5s, in=1248, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1248, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=1248, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.range_eq_top, Module.range_piEquiv]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=1248, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.4s, verify 0.1s, in=1248, out=219)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.0s, verify 0.1s, in=1248, out=246)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← range_eq_top, range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [← range_eq_top, range_piEquiv]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.9s, verify 0.1s, in=1248, out=306)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearMap.range_eq_top, Module.range_piEquiv]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.6s, verify 0.1s, in=1248, out=370)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.range_eq_top, Module.range_piEquiv]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.range_eq_top, Module.range_piEquiv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
