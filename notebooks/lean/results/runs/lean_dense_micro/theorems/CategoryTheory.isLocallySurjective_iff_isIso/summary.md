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

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.4s, in=383, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.0s, verify 0.3s, in=383, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h; exact h
· intro h; exact h.1
```

**lean_error:** tail step 2/3 ('· intro h; exact h'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.5s, verify 0.3s, in=383, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
. exact (config := .matchPrefix) IsIso.of_iso_mk
. exact (config := .matchPrefix) IsIso.iso_mk_of_iso
```

**lean_error:** tail step 2/3 ('. exact (config := .matchPrefix) IsIso.of_iso_mk'): <stdin>:1:16: expected ')', ',' or ':'

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.9s, verify 1.9s, in=383, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  exact IsIso.mk (IsIso.hom_inv_id h) (IsIso.inv_hom_id h)
· intro h
  exact IsIso.mk (IsIso.hom_inv_id h) (IsIso.inv_hom_id h)
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 3.4s, verify 0.3s, in=383, out=4)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

**lean_error:** tail step 1/1 ('aesop_cat'): tactic 'aesop' failed, failed to prove the goal after exhaustive search.

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.2s, in=383, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isIso_iff_isIso]
```

**lean_error:** tail step 1/1 ('rw [isIso_iff_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 3.9s, verify 0.2s, in=383, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isIso_iff_isIso]
```

**lean_error:** tail step 1/1 ('rw [isIso_iff_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 4.1s, verify 0.2s, in=383, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isIso_iff_isIso_of_epi_mono]
```

**lean_error:** tail step 1/1 ('rw [isIso_iff_isIso_of_epi_mono]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1375, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=1375, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J _) (map_isIso _ _)
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J _) (map_isIso _ _)'): function expected at

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1375, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/2 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.8s, verify 0.2s, in=1375, out=72)

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

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=1375, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): type class instance expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 3.1s, verify 0.1s, in=1375, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
infer_instance
```

**lean_error:** tail step 1/1 ('infer_instance'): type class instance expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 4.3s, verify 0.3s, in=1375, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 4.8s, verify 0.1s, in=1375, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf _ _) (sheafToPresheaf _ _).map_isIso
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ (sheafToPresheaf _ _) (sheafToPresheaf _ _).map_isIso'): function expected at
