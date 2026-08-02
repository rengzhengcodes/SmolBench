# CategoryTheory.Limits.IsZero.iff_isSplitMono_eq_zero   (k=6, 7 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`  

**Ground-truth tail (from k):**
```lean
simp only [h, zero_comp]
```

**True premises at k:** `CategoryTheory.Limits.zero_comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | · | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=330, out=491)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [h]
```

**lean_error:** tail step 1/1 ('simpa [h]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 29.0s, verify 0.1s, in=279, out=3624)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h]
apply comp_zero
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=276, out=299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h]
simp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 10.4s, verify 0.1s, in=632, out=2537)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Category.assoc, h]
```

**final state (truncated):**
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
...
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.2s, verify 0.1s, in=593, out=3989)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h]
rw [zero_comp]
rfl
```

**lean_error:** tail step 1/3 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=588, out=782)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.8s, verify 0.1s, in=912, out=879)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h]
simp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.7s, verify 0.1s, in=872, out=7825)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h]
apply zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 83.3s, verify 0.1s, in=868, out=9005)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h, zero_comp]
rfl
```

**lean_error:** tail step 1/2 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.9s, verify 0.1s, in=899, out=2404)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [h, zero_comp] using (IsSplitMono.id f).symm
```

**lean_error:** tail step 1/1 ('simpa [h, zero_comp] using (IsSplitMono.id f).symm'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 57.3s, verify 0.1s, in=940, out=7622)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h]
exact zero_comp
```

**lean_error:** tail step 1/2 ('rw [h]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=883, out=370)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h, zero_comp]
```

**lean_error:** tail step 1/1 ('rw [h, zero_comp]'): tactic 'rewrite' failed, motive is not type correct
