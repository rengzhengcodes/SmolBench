# Submodule.dualAnnihilator_map_linearEquiv_flip_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PerfectPairing.lean`  

**Ground-truth tail (from k):**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**True premises at k:** `Submodule.map_dualCoannihilator_linearEquiv_flip`, `LinearEquiv.flip_flip`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=371, out=111)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext φ,
  constructor,
  · intro hx,
    apply mem_map,
    exists dualAnnihilator_φ,
    constructor,
    · exact mem_dualAnnihilator _ hx,
    · apply e.map_dualAnnihilator_φ,
  · intro hφ,
    apply mem_dualAnnihilator,
    intro ψ,
    apply mem_map,
    exists e.symm ψ,
    constructor,
    · exact (mem_map _ _ _).mp hφ ψ,
    · apply LinearEquiv.symm_apply_apply,
```

**lean_error:** tail step 1/16 ('ext φ,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.2s, in=343, out=172)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dualAnnihilator, Submodule.map_comp, LinearEquiv.coe_comp, LinearEquiv.coe_coe, Function.comp_def, LinearEquiv.flip_apply, LinearEquiv.symm_apply_apply, Submodule.dualAnnihilator_coannihilator]
simp only [Submodule.map_id', LinearEquiv.refl_toFun]
rw [← Submodule.dualCoannihilator_coannihilator, Submodule.dualLCotensor_dualAnnihilator_eq, Submodule.dualLCotensor_comp_dualAnnihilator, ← LinearMap.comp_def, LinearEquiv.comp_coe, LinearEquiv.symm_trans, LinearEquiv.dualMapOfEquiv_symm, LinearEquiv.refl_toFun, LinearMap.id_comp]
rfl
```

**lean_error:** tail step 1/4 ('rw [dualAnnihilator, Submodule.map_comp, LinearEquiv.coe_comp, LinearEquiv.coe_coe, Function.comp_def, LinearEquiv.flip_apply, LinearEquiv.symm_apply_apply, Submodule.dualAnnihilator_coannihilator]'): tactic 'rewrite' failed, did not find instance of the pattern in the target express

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=360, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearEquiv.ext
simp [dualAnnihilator, LinearEquiv.symm_apply, LinearEquiv.flip_apply, map_coe, dualCoannihilator]
```

**lean_error:** tail step 1/2 ('apply LinearEquiv.ext'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=931, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Submodule.map_dualCoannihilator_linearEquiv_flip]
rw [LinearEquiv.flip_flip this]
```

**lean_error:** tail step 1/2 ('rw [Submodule.map_dualCoannihilator_linearEquiv_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=903, out=44)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Submodule.map_dualCoannihilator_linearEquiv_flip, LinearEquiv.flip_flip, ← LinearEquiv.symm_symm e, LinearEquiv.symm_map_submodule]
```

**lean_error:** tail step 1/1 ('rw [← Submodule.map_dualCoannihilator_linearEquiv_flip, LinearEquiv.flip_flip, ← LinearEquiv.symm_symm e, LinearEquiv.symm_map_submodule]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=920, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [dualAnnihilator, map_dualCoannihilator_linearEquiv_flip, flip_flip]
exact rfl
```

**lean_error:** tail step 1/2 ('rw [dualAnnihilator, map_dualCoannihilator_linearEquiv_flip, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1852, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**lean_error:** tail step 1/1 ('rw [map_dualCoannihilator_linearEquiv_flip, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1813, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Submodule.map_dualCoannihilator_linearEquiv_flip, LinearEquiv.flip_flip]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=1841, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [dualAnnihilator, map_dualCoannihilator_linearEquiv_flip, flip_flip]
exact map_comp
```

**lean_error:** tail step 1/2 ('rw [dualAnnihilator, map_dualCoannihilator_linearEquiv_flip, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=1876, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**lean_error:** tail step 1/1 ('rw [map_dualCoannihilator_linearEquiv_flip, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1955, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Submodule.map_dualCoannihilator_linearEquiv_flip, LinearEquiv.flip_flip]
rfl
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=1865, out=82)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [dualAnnihilator, map_map, LinearEquiv.coe_symm, LinearEquiv.flip, dualCoannihilator, map_map]
erw [map_dualCoannihilator_linearEquiv_flip, flip_flip]
simp only [map_comp, LinearEquiv.coe_flip, LinearEquiv.coe_symm, LinearEquiv.flip_flip]
```

**lean_error:** tail step 1/3 ('rw [dualAnnihilator, map_map, LinearEquiv.coe_symm, LinearEquiv.flip, dualCoannihilator, map_map]'): tactic 'rewrite' failed, equality or iff proof expected
