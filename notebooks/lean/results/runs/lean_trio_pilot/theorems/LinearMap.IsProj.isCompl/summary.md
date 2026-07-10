# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | · | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1125, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact p
exact h
exact p
```

**lean_error:** tail step 1/3 ('exact p'): type mismatch

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1125, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.compl
```

**lean_error:** tail step 1/1 ('exact h.compl'): invalid field 'compl', the environment does not contain 'LinearMap.IsProj.compl'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1114, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply is_compl_of_proj 
exact h 
exact p 
exact (by apply_instance)
```

**lean_error:** tail step 1/4 ('apply is_compl_of_proj'): unknown identifier 'is_compl_of_proj'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.6s, verify 0.5s, in=1105, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsCompl.symm
apply h
exact p
```

**lean_error:** tail step 2/3 ('apply h'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 69.7s, verify 0.1s, in=1063, out=5022)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ker_codRestrict f p (le_of_eq (IsProj.image_eq h))],  
exact h.isCompl,  
exact h,  
exact p
```

**lean_error:** tail step 1/4 ('rw [ker_codRestrict f p (le_of_eq (IsProj.image_eq h))],'): <stdin>:1:55: expected end of input

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=1063, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1469, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact p,
apply LinearMap.isCompl_of_proj,
intros x,
exact LinearMap.IsProj.id x h,
```

**lean_error:** tail step 1/4 ('exact p,'): <stdin>:1:7: expected end of input

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1469, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj h.2
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.2'): application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=1458, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.8s, verify 0.3s, in=1449, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isCompl_of_proj
exact h
```

**lean_error:** tail step 2/2 ('exact h'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 22.7s, verify 0.5s, in=1407, out=1375)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isCompl_of_proj
  intro x
  simp only [LinearMap.codRestrict_apply, h.fixed]
```

**lean_error:** tail step 3/3 ('simp only [LinearMap.codRestrict_apply, h.fixed]'): invalid field 'fixed', the environment does not contain 'LinearMap.IsProj.fixed'

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1407, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.5s, in=2090, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intros
simp only [codRestrict_apply, Submodule.coe_mk]
exact h.id_apply _
exact p
```

**lean_error:** tail step 3/5 ('simp only [codRestrict_apply, Submodule.coe_mk]'): simp made no progress

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2090, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj h.f_is_idem
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.f_is_idem'): invalid field 'f_is_idem', the environment does not contain 'LinearMap.IsProj.f_is_idem'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=2079, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=2070, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 102.8s, verify 0.4s, in=2028, out=7994)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isCompl_of_proj
intro x hx
rw [codRestrict_apply]
exact h.apply_of_mem hx
```

**lean_error:** tail step 2/4 ('intro x hx'): tactic 'introN' failed, insufficient number of binders

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=2028, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj h.idem
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.idem'): invalid field 'idem', the environment does not contain 'LinearMap.IsProj.idem'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=2115, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
exact h.id
exact p
```

**lean_error:** tail step 2/3 ('exact h.id'): invalid field 'id', the environment does not contain 'LinearMap.IsProj.id'

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=2115, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj h.2
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.2'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=2104, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=2095, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
exact h
```

**lean_error:** tail step 2/2 ('exact h'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 9.2s, verify 0.2s, in=2056, out=556)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
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

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=2056, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'
