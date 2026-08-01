# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1125, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact p
exact h
exact p
```

**lean_error:** tail step 1/3 ('exact p'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1084, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsCompl_idem h.2
exact ker (codRestrict p f (by simp [h.1]))
exact p
simp only [codRestrict_apply, IsProj.comp_id h, id_eq]
exact IsCompl_idem h.2
exact ker (codRestrict p f ?_)
simp [h.1]
```

**lean_error:** tail step 1/7 ('exact IsCompl_idem h.2'): unknown identifier 'IsCompl_idem'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.5s, in=1114, out=443)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsCompl.of_eq 
exact ker_codRestrict 
exact h 
exact p 
exact f
```

**lean_error:** tail step 2/5 ('exact ker_codRestrict'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=1469, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact p,
exact h,
apply LinearMap.isCompl_of_proj,
intros,
rw [LinearMap.codRestrict_apply],
exact h x,
```

**lean_error:** tail step 1/6 ('exact p,'): <stdin>:1:7: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1422, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_of_proj]
exact h.idem
exact h.proj
exact p
```

**lean_error:** tail step 1/4 ('rw [isCompl_of_proj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=1458, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.6s, in=2090, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intros
rw [codRestrict_apply]
exact h.id x
exact p
```

**lean_error:** tail step 3/5 ('rw [codRestrict_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=2040, out=62)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsCompl.symm, isCompl_of_proj]
· intro x
  simp only [codRestrict_apply,Subtype.coe_mk]
  exact h.2 ⟨x, h.1 x⟩
exact p
exact LinearMap.codRestrictRange f p h.1
```

**lean_error:** tail step 1/6 ('rw [IsCompl.symm, isCompl_of_proj]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=2079, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=2115, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
exact h.id
exact p
```

**lean_error:** tail step 2/3 ('exact h.id'): invalid field 'id', the environment does not contain 'LinearMap.IsProj.id'

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2140, out=41)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact LinearMap.isCompl_of_proj h.idem
exact p
exact h.ker_eq_comap_neg
exact p
exact LinearMap.codRestrictRange _ _ h.map_eq_id
```

**lean_error:** tail step 1/5 ('exact LinearMap.isCompl_of_proj h.idem'): invalid field 'idem', the environment does not contain 'LinearMap.IsProj.idem'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=2104, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
exact p
```

**lean_error:** tail step 2/3 ('exact h'): type mismatch
