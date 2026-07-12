# IntermediateField.normalClosure_mono   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/NormalClosure.lean`  

**Ground-truth tail (from k):**
```lean
exact iSup_mono (fun f ↦ map_mono f h)
```

**True premises at k:** `iSup_mono`, `IntermediateField.map_mono`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✓ | ✓ | ✓ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 163.0s, verify 0.1s, in=289, out=8900)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_le,
intros f,
obtain ⟨g, hg⟩ := IsNormal.exists_auto L K f,
transitivity map (g.restrict K') K,
{ apply map_congr, exact hg },
apply map_mono,
exact h
```

**lean_error:** tail step 1/7 ('apply supr_le,'): <stdin>:1:13: expected end of input

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 14.7s, verify 0.1s, in=289, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h'): application type mismatch

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 9.4s, verify 0.1s, in=289, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=289, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 68.9s, verify 0.2s, in=630, out=3417)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **success**  (gen 15.0s, verify 0.1s, in=630, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 9.6s, verify 1.1s, in=630, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `hint:2` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 10.2s, verify 0.1s, in=630, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 107.8s, verify 0.3s, in=3385, out=5579)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
exact map_mono f h
```

### `hint:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 14.9s, verify 0.1s, in=3385, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 9.3s, verify 0.1s, in=3385, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:3` · qwen3-lean-real · rollout 0 → **success**  (gen 10.4s, verify 0.1s, in=3385, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 78.5s, verify 0.3s, in=3414, out=397)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 15.1s, verify 1.2s, in=3414, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 9.1s, verify 0.1s, in=3414, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 10.5s, verify 0.2s, in=3414, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun _ => map_mono h'): application type mismatch
