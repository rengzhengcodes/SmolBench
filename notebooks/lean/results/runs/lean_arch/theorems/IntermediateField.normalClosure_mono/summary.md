# IntermediateField.normalClosure_mono   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/NormalClosure.lean`  

**Ground-truth tail (from k):**
```lean
exact iSup_mono (fun f ↦ map_mono f h)
```

**True premises at k:** `iSup_mono`, `IntermediateField.map_mono`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | X X |
| `hint:2` | ✓ | ✓ | X X |
| `hint:3` | ✓ | ✓ | X X |
| `noise:3` | ✘ | ✘ | X X |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=322, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
suffices : ∀ f, ∃ g, map f K ≤ map g K'
intro f
use map (embeddings.restrictNormal f h)
simp
exact le_rfl
apply supr_le_supr this
```

**lean_error:** tail step 1/6 ("suffices : ∀ f, ∃ g, map f K ≤ map g K'"): <stdin>:1:9: expected term

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 1.6s, in=294, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply le_iSup (f := f)
exact map_mono h
```

**lean_error:** tail step 3/4 ('apply le_iSup (f := f)'): failed to synthesize instance

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 1.0s, verify 300.1s, in=311, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sup_le_sup
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 1.2s, verify 300.1s, in=311, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sup_le_sup
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 3.3s, verify 0.3s, in=663, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' iSup_mono fun f => _
refine' IntermediateField.map_mono f h
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=633, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => IntermediateField.map_mono f h
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 601.3s, verify 300.1s, in=652, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 301.3s, verify 300.1s, in=652, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
exact λ f, map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.9s, verify 0.3s, in=3415, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine' iSup_mono fun f => _
refine' IntermediateField.map_mono f h
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=3386, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => IntermediateField.map_mono f h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 301.1s, verify 300.1s, in=3404, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 601.5s, verify 300.1s, in=3404, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 1.3s, in=3444, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono h
```

**lean_error:** tail step 3/3 ('apply IntermediateField.map_mono h'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.4s, in=3731, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => IntermediateField.map_mono (AlgHom.restrictNormalHom F f) h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => IntermediateField.map_mono (AlgHom.restrictNormalHom F f) h'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 901.5s, verify 300.1s, in=3433, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 901.7s, verify 300.4s, in=3433, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono h
```

**lean_error:** DojoTacticTimeoutError: 
