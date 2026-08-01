# LinearEquiv.coord_self   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Span.lean`  

**Ground-truth tail (from k):**
```lean
rw [← toSpanNonzeroSingleton_one R M x h, LinearEquiv.symm_apply_apply]
```

**True premises at k:** `LinearEquiv.toSpanNonzeroSingleton_one`, `LinearEquiv.symm_apply_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=338, out=5)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact coord_self h
```

**lean_error:** tail step 1/1 ('exact coord_self h'): function expected at

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=310, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [coord]
simp only [Basis.repr_self_apply, one_smul]
simp only [Subtype.coe_mk]
```

**lean_error:** tail step 2/3 ('simp only [Basis.repr_self_apply, one_smul]'): unknown identifier 'Basis.repr_self_apply'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=327, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply coord_apply_eq_one
```

**lean_error:** tail step 1/1 ('apply coord_apply_eq_one'): unknown identifier 'coord_apply_eq_one'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=680, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton R M x h)]
rw [LinearEquiv.toSpanNonzeroSingleton_one]
```

**lean_error:** tail step 1/2 ('rw [←LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton R M x h)]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=648, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coord]
simp only [LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]
```

**lean_error:** tail step 2/2 ('simp only [LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=669, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearEquiv.toSpanNonzeroSingleton_one
simp
```

**lean_error:** tail step 1/2 ('apply LinearEquiv.toSpanNonzeroSingleton_one'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=937, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearEquiv.toSpanNonzeroSingleton_one]
rw [←LinearEquiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('rw [LinearEquiv.toSpanNonzeroSingleton_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=903, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coord]
simp only [LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]
```

**lean_error:** tail step 2/2 ('simp only [LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 20.3s, verify 0.2s, in=926, out=1257)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearEquiv.symm_apply_apply
```

**lean_error:** tail step 1/1 ('apply LinearEquiv.symm_apply_apply'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=961, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearEquiv.toSpanNonzeroSingleton_one R M x h]
apply LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton R M x h)
```

**lean_error:** tail step 1/2 ('rw [LinearEquiv.toSpanNonzeroSingleton_one R M x h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=960, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coord]
simp only [LinearEquiv.coe_toSpanNonzeroSingleton, LinearEquiv.toSpanNonzeroSingleton_one,
    LinearEquiv.symm_apply_apply]
rfl
```

**lean_error:** tail step 2/4 ('simp only [LinearEquiv.coe_toSpanNonzeroSingleton, LinearEquiv.toSpanNonzeroSingleton_one,'): <stdin>:1:90: unexpected end of input; expected ']'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=950, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact LinearEquiv.symm_apply_apply _ _
```

**lean_error:** tail step 1/1 ('exact LinearEquiv.symm_apply_apply _ _'): typeclass instance problem is stuck, it is often due to metavariables
