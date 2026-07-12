# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 80.9s, verify 0.2s, in=1063, out=5288)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply h.isCompl
exact h
exact p
```

**lean_error:** tail step 1/3 ('apply h.isCompl'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1063, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1063, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.compl
```

**lean_error:** tail step 1/1 ('exact h.compl'): invalid field 'compl', the environment does not contain 'LinearMap.IsProj.compl'

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 70.6s, verify 0.1s, in=1063, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.compl
```

**lean_error:** tail step 1/1 ('exact h.compl'): invalid field 'compl', the environment does not contain 'LinearMap.IsProj.compl'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 35.1s, verify 0.2s, in=1407, out=1972)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 75.7s, verify 0.1s, in=1407, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1407, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:2` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1407, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.5s, in=2028, out=455)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intro x
simp only [LinearMap.codRestrict_apply, h.apply_of_mem]
```

**lean_error:** tail step 3/3 ('simp only [LinearMap.codRestrict_apply, h.apply_of_mem]'): invalid field 'apply_of_mem', the environment does not contain 'LinearMap.IsProj.apply_of_mem'

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2028, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2028, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 70.7s, verify 0.1s, in=2028, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 86.4s, verify 0.5s, in=2056, out=5798)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intros x
simp [LinearMap.codRestrict_apply]
obtain ⟨y, rfl⟩ := f.mem_range.mp (h.range_eq ▸ x.property)
rw [← h.idem_apply]
simp
```

**lean_error:** tail step 3/6 ('simp [LinearMap.codRestrict_apply]'): simp made no progress

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=2056, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2056, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2056, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'
