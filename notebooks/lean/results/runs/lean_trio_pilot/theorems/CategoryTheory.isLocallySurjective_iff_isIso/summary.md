# CategoryTheory.isLocallySurjective_iff_isIso   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/Surjective.lean`  

**Ground-truth tail (from k):**
```lean
exact
  ⟨fun h => @isIso_of_reflects_iso _ _ _ _ _ _ (imageSheafι f) (sheafToPresheaf J _) h _, fun h =>
    @Functor.map_isIso _ _ _ _ _ _ (sheafToPresheaf J _) _ h⟩
```

**True premises at k:** `CategoryTheory.isIso_of_reflects_iso`, `CategoryTheory.GrothendieckTopology.imageSheafι`, `CategoryTheory.sheafToPresheaf`, `CategoryTheory.Functor.map_isIso`, `CategoryTheory.sheafToPresheaf`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.4s, in=383, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=383, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=372, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
exact (IsIso.of_iso)
exact (IsIso.iso)
```

**lean_error:** tail step 2/3 ('exact (IsIso.of_iso)'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=363, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Propext
split
intro
apply IsIso.of_iso
intro
apply IsIso.iso
```

**lean_error:** tail step 1/6 ('apply Propext'): unknown identifier 'Propext'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 85.6s, verify 0.1s, in=356, out=4231)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Sheaf.is_iso_iff_is_iso_val
```

**lean_error:** tail step 1/1 ('apply Sheaf.is_iso_iff_is_iso_val'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=356, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=1375, out=72)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)
exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)
constructor
intro h
apply CategoryTheory.Functor.map_isIso
constructor
intro h
apply isIso_of_reflects_iso
exact h
```

**lean_error:** tail step 1/9 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)'): type mismatch

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=1375, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.5s, in=1364, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 3.1s, verify 0.7s, in=1355, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 87.5s, verify 0.2s, in=1344, out=4356)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
· intro h
  apply isIso_of_reflects_iso _ sheafToPresheaf
  exact h
· intro h
  exact sheafToPresheaf.map_isIso h
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 10.3s, verify 0.6s, in=1344, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=1955, out=68)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
exact imageSheafι f
exact Functor.map_isIso (sheafToPresheaf J (Type w)) _
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/4 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 7.7s, verify 0.8s, in=1955, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J _)
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J _)'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.5s, in=1944, out=42)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 2.1s, verify 0.5s, in=1935, out=38)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact Functor.map_isIso sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 125.2s, verify 0.1s, in=1929, out=6251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isIso_iff_of_reflects_iso
```

**lean_error:** tail step 1/1 ('apply isIso_iff_of_reflects_iso'): unknown identifier 'isIso_iff_of_reflects_iso'

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 10.9s, verify 0.9s, in=1929, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι, sheafToPresheaf_map, isIso_of_reflects_iso]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι, sheafToPresheaf_map, isIso_of_reflects_iso]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.4s, in=1981, out=47)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
exact imageSheafι f
exact Functor.map_isIso (sheafToPresheaf J (Type w)) _
```

**lean_error:** tail step 1/3 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=1981, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J _)
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J _)'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.5s, in=1970, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 2.6s, verify 0.4s, in=1961, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
exact CategoryTheory.isIso_of_reflects_iso _ (sheafToPresheaf) _
exact CategoryTheory.Functor.map_isIso _
```

**lean_error:** tail step 2/3 ('exact CategoryTheory.isIso_of_reflects_iso _ (sheafToPresheaf) _'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 48.2s, verify 0.2s, in=1953, out=2405)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
. apply isIso_of_reflects_iso (sheafToPresheaf J (Type w)) (imageSheafι f)
. apply Functor.map_isIso (sheafToPresheaf J (Type w)) (imageSheafι f)
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 9.9s, verify 0.1s, in=1953, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
