# Submodule.dualAnnihilator_map_linearEquiv_flip_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PerfectPairing.lean`  

**Ground-truth tail (from k):**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**True premises at k:** `Submodule.map_dualCoannihilator_linearEquiv_flip`, `LinearEquiv.flip_flip`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ · ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=341, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualAnnihilator_map]
```

**lean_error:** tail step 1/1 ('simp [dualAnnihilator_map]'): unknown identifier 'dualAnnihilator_map'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=341, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [dualAnnihilator_flip_symm e]
```

**lean_error:** tail step 1/1 ('simp [dualAnnihilator_flip_symm e]'): unknown identifier 'dualAnnihilator_flip_symm'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=341, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using dualAnnihilator_dualCoannihilator_map_symm_flip p
```

**lean_error:** tail step 1/1 ('simpa using dualAnnihilator_dualCoannihilator_map_symm_flip p'): unknown identifier 'dualAnnihilator_dualCoannihilator_map_symm_flip'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.9s, verify 0.1s, in=341, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← dualAnnihilator_flip (LinearEquiv.symm e) p, LinearEquiv.symm_symm, dualAnnihilator_flip]
```

**lean_error:** tail step 1/1 ('rw [← dualAnnihilator_flip (LinearEquiv.symm e) p, LinearEquiv.symm_symm, dualAnnihilator_flip]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.2s, in=901, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using map_dualCoannihilator_linearEquiv_flip e.flip p
```

**lean_error:** tail step 1/1 ('simpa using map_dualCoannihilator_linearEquiv_flip e.flip p'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=901, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← dualCoannihilator_map_linearEquiv_flip, flip_flip]
```

**lean_error:** tail step 1/1 ('rw [← dualCoannihilator_map_linearEquiv_flip, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=901, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Submodule.map_dualCoannihilator_linearEquiv_flip, e.flip_flip]
```

**lean_error:** tail step 1/1 ('simp [Submodule.map_dualCoannihilator_linearEquiv_flip, e.flip_flip]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.2s, in=901, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← dualCoannihilator_map_linearEquiv_flip, LinearEquiv.flip_flip]
```

**lean_error:** tail step 1/1 ('rw [← dualCoannihilator_map_linearEquiv_flip, LinearEquiv.flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=1830, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← dualCoannihilator_map_linearEquiv_flip]
```

**lean_error:** tail step 1/1 ('simp [← dualCoannihilator_map_linearEquiv_flip]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.1s, verify 0.2s, in=1830, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact map_dualCoannihilator_linearEquiv_flip p
```

**lean_error:** tail step 1/1 ('exact map_dualCoannihilator_linearEquiv_flip p'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.7s, verify 0.1s, in=1830, out=51)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (map_dualCoannihilator_linearEquiv_flip p).symm.trans
  (congr_arg (map e.flip) flip_flip.symm ▸ dualCoannihilator_map_linearEquiv_flip p)
```

**lean_error:** tail step 1/2 ('exact (map_dualCoannihilator_linearEquiv_flip p).symm.trans'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 72.1s, verify 0.1s, in=1830, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Submodule.map_dualCoannihilator_linearEquiv_flip, e.flip_flip]
```

**lean_error:** tail step 1/1 ('simp [Submodule.map_dualCoannihilator_linearEquiv_flip, e.flip_flip]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1849, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Submodule.map_dualCoannihilator_linearEquiv_flip]
```

**lean_error:** tail step 1/1 ('simp [Submodule.map_dualCoannihilator_linearEquiv_flip]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.2s, in=1849, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using map_dualCoannihilator_linearEquiv_flip e.flip p
```

**lean_error:** tail step 1/1 ('simpa using map_dualCoannihilator_linearEquiv_flip e.flip p'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.5s, verify 0.2s, in=1849, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearEquiv.flip_flip e, map_dualCoannihilator_linearEquiv_flip]
```

**final state (truncated):**
```
R : Type u_1
M : Type u_2
N : Type u_3
inst✝⁵ : CommRing R
inst✝⁴ : AddCommGroup M
inst✝³ : Module R M
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.2s, in=1849, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← dualCoannihilator_map_linearEquiv_flip, LinearEquiv.map_symm, flip_flip]
```

**lean_error:** tail step 1/1 ('rw [← dualCoannihilator_map_linearEquiv_flip, LinearEquiv.map_symm, flip_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
