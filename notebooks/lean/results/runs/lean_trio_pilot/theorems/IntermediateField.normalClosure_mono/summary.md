# IntermediateField.normalClosure_mono   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/NormalClosure.lean`  

**Ground-truth tail (from k):**
```lean
exact iSup_mono (fun f ↦ map_mono f h)
```

**True premises at k:** `iSup_mono`, `IntermediateField.map_mono`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | X | X | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | X | X | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | X | X | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | X | X | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=322, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' supr_le_supr_of_subset _
intro f
exact map_mono h
```

**lean_error:** tail step 1/3 ("refine' supr_le_supr_of_subset _"): unknown identifier 'supr_le_supr_of_subset'

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.7s, verify 0.9s, in=322, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h'): application type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 0.9s, verify 300.1s, in=311, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sup_le_sup
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **exception**  (gen 1.1s, verify 300.1s, in=302, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sup_le_sup
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 159.8s, verify 0.3s, in=289, out=9222)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply iSup_mono
intro f
obtain ⟨σ, hσ⟩ := (Normal.exists_alg_equiv f)
use σ.toRingHom.restrict K'
rw [hσ]
apply image_subset_image σ.toRingHom h
```

**lean_error:** tail step 3/6 ('obtain ⟨σ, hσ⟩ := (Normal.exists_alg_equiv f)'): rcases tactic failed: x✝ : ?m.135207 is not an inductive datatype

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=289, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.2s, in=663, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' iSup_mono fun f => _
refine' IntermediateField.map_mono f h
```

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 2.8s, verify 0.1s, in=663, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun ϕ => map_mono ϕ h
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 301.1s, verify 300.1s, in=652, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
exact λ f, map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **exception**  (gen 901.5s, verify 300.1s, in=643, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
exact λ f, map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 38.4s, verify 0.1s, in=630, out=1918)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono (map_mono h)
```

**lean_error:** tail step 1/1 ('apply iSup_mono (map_mono h)'): application type mismatch

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=630, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=3415, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono h
```

**lean_error:** tail step 3/3 ('apply IntermediateField.map_mono h'): application type mismatch

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=3415, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun ϕ => map_mono ϕ h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 601.2s, verify 300.1s, in=3404, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **exception**  (gen 601.4s, verify 300.1s, in=3395, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 49.0s, verify 0.3s, in=3385, out=2435)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.0s, verify 1.0s, in=3385, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h'): application type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.3s, in=3444, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono h
```

**lean_error:** tail step 3/3 ('apply IntermediateField.map_mono h'): application type mismatch

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=3444, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **exception**  (gen 901.4s, verify 300.1s, in=3433, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply IntermediateField.map_mono
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **exception**  (gen 301.2s, verify 300.1s, in=3424, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono
exact h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 113.6s, verify 0.2s, in=3414, out=6093)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=3414, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch
