# Filter.map_sigma_mk_comap   (k=2, 3 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
apply image_sigmaMk_preimage_sigmaMap hf
```

**True premises at k:** `Set.image_sigmaMk_preimage_sigmaMap`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✘ ✘ | ✘ ✘ · ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ · ✘ ✘ | ✘ ✘ ✘ ✓ | ✓ ✘ ✓ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 61.1s, verify 0.1s, in=357, out=2515)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply set.ext
rintro ⟨y⟩
split
rintro ⟨s, hs, rfl⟩
use g a s
exact ⟨hs, rfl⟩
rintro ⟨b, s⟩ ⟨t, ht, h_eq⟩
injection h_eq with h_f h_g
have := hf h_f
subst b
use s
exact ⟨ht, h_g⟩
```

**lean_error:** tail step 1/12 ('apply set.ext'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 76.0s, verify 0.3s, in=357, out=3093)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.ext
intro p
split
· rintro ⟨b, rfl, h⟩
  use ⟨a, b⟩
  exact ⟨rfl, rfl, h⟩
· rintro ⟨c, d, rfl, hfc, hgd⟩
  have : c = a := hf.1 hfc
  subst this
  use d
  exact ⟨rfl, hgd⟩
```

**lean_error:** tail step 3/11 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 151.7s, verify 0.1s, in=357, out=6338)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext s,
cases s with | mk a' p' =>,
split,
rintro ⟨rfl, hp⟩,
exact ⟨rfl, hp⟩,
rintro ⟨h, hp⟩,
exact ⟨hf h, hp⟩
```

**lean_error:** tail step 1/7 ('ext s,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 156.4s, verify 0.3s, in=357, out=6537)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨b, z⟩
split
  rintro ⟨rfl, hz⟩
  exact ⟨rfl, hz⟩
rintro ⟨hfb, hgz⟩
have hba : b = a := hf hfb
subst hba
exact ⟨rfl, hgz⟩
```

**lean_error:** tail step 2/8 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=357, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_5.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.0s, verify 0.1s, in=357, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hf.eq_iff]
```

**final state (truncated):**
```
case h.e'_5.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.5s, in=357, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Sigma.mk_injective.comp (hf _) (hg _)]
```

**lean_error:** tail step 1/1 ('simp [Sigma.mk_injective.comp (hf _) (hg _)]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.8s, verify 0.1s, in=357, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Sigma.map, image_preimage_eq_inter_range, Sigma.range_mk, inter_eq_self_of_subset_left,
  subset_def, Sigma.exists, mem_preimage, mem_image, Sigma.mk.inj_iff, and_congr_right_iff,
  eq_comm, forall_eq_left, exists_eq_right, exists_prop]
```

**lean_error:** tail step 1/3 ('simp only [Sigma.map, image_preimage_eq_inter_range, Sigma.range_mk, inter_eq_self_of_subset_left,'): <stdin>:1:98: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.9s, verify 0.1s, in=357, out=232)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.image_preimageSigma
```

**lean_error:** tail step 1/1 ('apply Set.image_preimageSigma'): unknown constant 'Set.image_preimageSigma'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.1s, verify 0.1s, in=357, out=240)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Sigma.image_mk_eq_preimage_map hf
```

**lean_error:** tail step 1/1 ('exact Sigma.image_mk_eq_preimage_map hf'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 8.4s, verify 0.1s, in=357, out=250)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_5.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.5s, verify 0.1s, in=357, out=414)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Sigma.map_mk, Sigma.mk_preimage_mk]
```

**lean_error:** tail step 1/1 ('simp only [Sigma.map_mk, Sigma.mk_preimage_mk]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 8.1s, verify 0.1s, in=827, out=375)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
convert image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('convert image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:48: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 8.2s, verify 0.1s, in=827, out=383)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 10.3s, verify 0.1s, in=827, out=470)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.1s, in=827, out=644)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=827, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=827, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a id
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a id'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.7s, in=827, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.3s, verify 0.1s, in=827, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a _
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.1s, verify 0.1s, in=827, out=179)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a id
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a id'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=827, out=189)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.8s, verify 0.1s, in=827, out=202)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.3s, verify 0.1s, in=827, out=297)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
convert Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('convert Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:56: expected token

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 18.9s, verify 0.1s, in=1567, out=456)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g a
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 19.2s, verify 0.1s, in=1567, out=387)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply image_sigmaMk_preimage_sigmaMap
```

**final state (truncated):**
```
case h.e'_5.h.hf
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 20.3s, verify 0.1s, in=1567, out=516)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 27.5s, verify 0.1s, in=1567, out=737)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=1567, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.5s, verify 0.1s, in=1567, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.6s, verify 0.1s, in=1567, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.7s, verify 0.1s, in=1567, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a _
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 11.8s, verify 0.1s, in=1567, out=165)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id _)
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.3s, verify 0.1s, in=1567, out=208)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.5s, verify 0.1s, in=1567, out=201)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a _
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.7s, verify 0.1s, in=1567, out=216)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 10.0s, verify 0.1s, in=1592, out=460)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 14.6s, verify 0.1s, in=1592, out=659)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 16.9s, verify 0.1s, in=1592, out=760)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:50: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 19.7s, verify 0.1s, in=1592, out=877)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
`apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝`
```

**lean_error:** tail step 1/1 ('`apply Set.image_sigmaMk_preimage_sigmaMap hf g a x✝`'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1592, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.0s, verify 0.1s, in=1592, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a _
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=1592, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a id
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a id'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.2s, verify 0.1s, in=1592, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a id
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a id'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.3s, verify 0.1s, in=1592, out=161)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:50: expected token

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=1592, out=206)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('exact image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:46: expected end of input

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.0s, verify 0.1s, in=1592, out=233)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:54: expected token

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.4s, verify 0.1s, in=1592, out=283)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
convert (image_sigmaMk_preimage_sigmaMap_subset f g a id).antisymm <|
  Set.image_sigmaMk_preimage_sigmaMap hf g a
```

**lean_error:** tail step 1/2 ('convert (image_sigmaMk_preimage_sigmaMap_subset f g a id).antisymm <|'): <stdin>:1:69: unexpected end of input
