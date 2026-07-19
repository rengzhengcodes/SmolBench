# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=1125, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact p
exact h
exact q
```

**lean_error:** tail step 1/3 ('exact p'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=1125, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact p
exact h
exact IsCompl.symm h.compl_isCompl
```

**lean_error:** tail step 1/3 ('exact p'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1125, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
focus
  exact p
focus
  exact h
exact IsCompl.symm h.compl
```

**lean_error:** tail step 1/5 ('focus'): <stdin>:1:5: unexpected end of input; expected '{'

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1125, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
focus
  apply IsCompl.ker_codRestrict
  exact h.compl
focus
  exact h
focus
  exact h.compl
```

**lean_error:** tail step 1/7 ('focus'): <stdin>:1:5: unexpected end of input; expected '{'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1125, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.compl
```

**lean_error:** tail step 1/1 ('exact h.compl'): invalid field 'compl', the environment does not contain 'LinearMap.IsProj.compl'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.8s, verify 0.1s, in=1125, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.2
```

**lean_error:** tail step 1/1 ('exact h.2'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=1125, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.1
```

**lean_error:** tail step 1/1 ('exact h.1'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=1125, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.is_compl_ker_cod_restrict
```

**lean_error:** tail step 1/1 ('exact h.is_compl_ker_cod_restrict'): invalid field 'is_compl_ker_cod_restrict', the environment does not contain 'LinearMap.IsProj.is_compl_ker_cod_restrict'

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=1469, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact p
exact h
exact id rfl
```

**lean_error:** tail step 1/3 ('exact p'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1469, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact p,
apply LinearMap.isCompl_of_proj,
intros x,
exact LinearMap.IsProj.id h x
```

**lean_error:** tail step 1/4 ('exact p,'): <stdin>:1:7: expected end of input

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=1469, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact p,
apply LinearMap.isCompl_of_proj,
intro x,
rw [codRestrict_apply],
exact h.id x,
```

**lean_error:** tail step 1/5 ('exact p,'): <stdin>:1:7: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=1469, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.ker_codRestrict f p,
apply LinearMap.isCompl_of_proj,
intros x,
exact LinearMap.IsProj.id h x,
```

**lean_error:** tail step 1/4 ('exact LinearMap.ker_codRestrict f p,'): <stdin>:1:35: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1469, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj h.idem
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.idem'): invalid field 'idem', the environment does not contain 'LinearMap.IsProj.idem'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=1469, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj h.idem
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj h.idem'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1469, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.isCompl_of_proj h.isProj_on
```

**lean_error:** tail step 1/1 ('exact LinearMap.isCompl_of_proj h.isProj_on'): invalid field 'isProj_on', the environment does not contain 'LinearMap.IsProj.isProj_on'

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1469, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact LinearMap.isCompl_of_proj h.isProj_on
```

**lean_error:** tail step 1/1 ('exact LinearMap.isCompl_of_proj h.isProj_on'): invalid field 'isProj_on', the environment does not contain 'LinearMap.IsProj.isProj_on'
