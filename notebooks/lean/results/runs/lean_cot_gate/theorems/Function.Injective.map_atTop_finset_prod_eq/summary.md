# Function.Injective.map_atTop_finset_prod_eq   (k=12, 13 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨_, (image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

**True premises at k:** `Finset.image_subset_iff_subset_preimage`, `rfl`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 74.8s, verify 0.1s, in=361, out=2946)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi Finset.preimage t g hg
split
· exact (Finset.image_subset_iff hg s t).mp ht
· rfl
```

**lean_error:** tail step 1/4 ('existsi Finset.preimage t g hg'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 89.9s, verify 0.1s, in=361, out=3454)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro x hx
  rw Finset.mem_preimage
  exact ht (Finset.mem_image_of_mem g hx)
· rfl
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 108.8s, verify 0.1s, in=361, out=4159)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use Finset.preimage t g hg
split
· exact (Finset.image_subset_iff hg).mp ht
· rfl
```

**lean_error:** tail step 1/4 ('use Finset.preimage t g hg'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 127.4s, verify 0.1s, in=361, out=4793)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi Finset.preimage t g this
split
exact Finset.image_subset_iff.mp ht
rfl
```

**lean_error:** tail step 1/4 ('existsi Finset.preimage t g this'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=361, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨_, subset_preimage_image g s, Finset.prod_preimage _ _ hg⟩
```

**lean_error:** tail step 1/1 ('exact ⟨_, subset_preimage_image g s, Finset.prod_preimage _ _ hg⟩'): internal exception #7

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=361, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨s, Subset.rfl, Finset.prod_image' (fun x _ y _ h => hg h)⟩
```

**lean_error:** tail step 1/1 ("exact ⟨s, Subset.rfl, Finset.prod_image' (fun x _ y _ h => hg h)⟩"): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=361, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g (hg.injOn _), fun x hx => ⟨g x, ⟨ht hx, rfl⟩⟩, Finset.prod_preimage' _ _ _⟩
```

**lean_error:** tail step 1/1 ("exact ⟨Finset.preimage t g (hg.injOn _), fun x hx => ⟨g x, ⟨ht hx, rfl⟩⟩, Finset.prod_preimage' _ _ _⟩"): invalid constructor ⟨...⟩, expected type must be an inductive type 

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=361, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g this, fun x hx => mem_preimage.2 (ht <| mem_image_of_mem _ hx),
  Finset.prod_preimage_of_image_eq _ this (fun x _ => hf x)⟩
```

**lean_error:** tail step 1/2 ('exact ⟨Finset.preimage t g this, fun x hx => mem_preimage.2 (ht <| mem_image_of_mem _ hx),'): <stdin>:1:90: unexpected end of input; expected '⟩'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 59.9s, verify 0.1s, in=1092, out=2392)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (Finset.image_subset_iff_subset_preimage hg.injOn).mpr ht
```

**lean_error:** tail step 1/1 ('exact (Finset.image_subset_iff_subset_preimage hg.injOn).mpr ht'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 77.7s, verify 0.1s, in=1092, out=3052)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn _), split, exact Finset.image_subset_iff_subset_preimage.mp ht, rfl
```

**lean_error:** tail step 1/1 ('use Finset.preimage t g (hg.injOn _), split, exact Finset.image_subset_iff_subset_preimage.mp ht, rfl'): too many arguments supplied to `use`

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 105.8s, verify 0.1s, in=1092, out=4054)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g (hg.injOn _), Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Finset.preimage t g (hg.injOn _), Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 118.3s, verify 0.1s, in=1092, out=4480)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.image_subset_iff_subset_preimage.mp
exact ht
```

**lean_error:** tail step 1/2 ('apply Finset.image_subset_iff_subset_preimage.mp'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=1092, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Finset.image_subset_iff_subset_preimage hg.injOn]
```

**lean_error:** tail step 1/1 ('simp [Finset.image_subset_iff_subset_preimage hg.injOn]'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1092, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Finset.image_subset_iff_subset_preimage, subset_preimage, ht, subset_refl]
```

**lean_error:** tail step 1/1 ('simp only [Finset.image_subset_iff_subset_preimage, subset_preimage, ht, subset_refl]'): unknown identifier 'subset_preimage'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1092, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Finset.image_subset_iff_subset_preimage (hg.injOn _), Finset.subset_preimage]
```

**lean_error:** tail step 1/1 ('simp [Finset.image_subset_iff_subset_preimage (hg.injOn _), Finset.subset_preimage]'): unknown constant 'Finset.subset_preimage'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1092, out=72)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Finset.prod_preimage _ _ (hg.injOn _), Finset.prod_image (hg.injOn _),
  image_subset_iff_subset_preimage (hg.injOn _), Finset.prod_image (hg.injOn _), and_iff_left rfl,
  eq_self_iff_true, forall_const]
```

**lean_error:** tail step 1/3 ('simp only [Finset.prod_preimage _ _ (hg.injOn _), Finset.prod_image (hg.injOn _),'): <stdin>:1:81: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 147.7s, verify 0.2s, in=2095, out=3180)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn _)
split
apply Finset.image_subset_iff_subset_preimage.1
exact ht
rfl
```

**lean_error:** tail step 2/5 ('split'): tactic 'split' failed

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 154.2s, verify 0.3s, in=2095, out=2766)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn _)
split
apply Finset.image_subset_iff_subset_preimage.2 ht
rfl
```

**lean_error:** tail step 2/4 ('split'): tactic 'split' failed

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 161.0s, verify 0.1s, in=2095, out=3125)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn (Set.injOn_preimage_t t g hg))
split
apply image_subset_iff_subset_preimage.mp hg ht
rfl
```

**lean_error:** tail step 1/4 ('use Finset.preimage t g (hg.injOn (Set.injOn_preimage_t t g hg))'): unknown constant 'Set.injOn_preimage_t'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 200.3s, verify 0.1s, in=2095, out=4448)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn _), exact ⟨Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩
```

**lean_error:** tail step 1/1 ('use Finset.preimage t g (hg.injOn _), exact ⟨Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩'): unknown identifier 'exact'

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=2095, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Finset.prod_preimage]
```

**lean_error:** tail step 1/1 ('simp only [Finset.prod_preimage]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=2095, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Finset.image_subset_iff_subset_preimage, hg.injOn]
```

**lean_error:** tail step 1/1 ('simp [Finset.image_subset_iff_subset_preimage, hg.injOn]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=2095, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Finset.prod_image (hg.injOn _), Finset.image_preimage]
```

**lean_error:** tail step 1/1 ('simp only [Finset.prod_image (hg.injOn _), Finset.image_preimage]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 4.8s, verify 0.1s, in=2095, out=69)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Finset.image_subset_iff_subset_preimage, hg.injOn, Finset.preimage_image,
  subset_iff, mem_preimage, Finset.mem_image, and_imp, exists_imp, forall_apply_eq_imp_eq,
  hg.eq_iff, SetLike.le_def, Finset.mem_coe]
```

**lean_error:** tail step 1/3 ('simp only [Finset.image_subset_iff_subset_preimage, hg.injOn, Finset.preimage_image,'): <stdin>:1:84: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 85.9s, verify 0.1s, in=2122, out=3301)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g (hg.injOn _), image_subset_iff_subset_preimage.mp ht, rfl⟩
```

**lean_error:** tail step 1/1 ("refine' ⟨Finset.preimage t g (hg.injOn _), image_subset_iff_subset_preimage.mp ht, rfl⟩"): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 115.4s, verify 0.2s, in=2122, out=4339)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
use Finset.preimage t g (hg.injOn _)
exact ⟨Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩
```

**lean_error:** tail step 2/2 ('exact ⟨Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 126.2s, verify 0.1s, in=2122, out=4711)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g (hg.injOn _), Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩
```

**lean_error:** tail step 1/1 ("refine' ⟨Finset.preimage t g (hg.injOn _), Finset.image_subset_iff_subset_preimage.mp ht, rfl⟩"): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 164.8s, verify 0.1s, in=2122, out=6224)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact image_subset_iff_subset_preimage.mp hg.injOn ht
rfl
```

**lean_error:** tail step 1/2 ('exact image_subset_iff_subset_preimage.mp hg.injOn ht'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=2122, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Finset.image_subset_iff_subset_preimage, hg.injOn, @rfl]
```

**lean_error:** tail step 1/1 ('simp [Finset.image_subset_iff_subset_preimage, hg.injOn, @rfl]'): invalid `simp` theorem, equation is equivalent to

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=2122, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Finset.image_subset_iff_subset_preimage hg.injOn, Finset.subset_iff]
```

**lean_error:** tail step 1/1 ('simp [Finset.image_subset_iff_subset_preimage hg.injOn, Finset.subset_iff]'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=2122, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Finset.image_subset_iff_subset_preimage, injOn_univ, subset_univ, iff_true]
```

**lean_error:** tail step 1/1 ('simp only [Finset.image_subset_iff_subset_preimage, injOn_univ, subset_univ, iff_true]'): unknown identifier 'injOn_univ'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=2122, out=51)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Finset.image_subset_iff_subset_preimage, subset_iff, Finset.mem_preimage, exists_imp,
  Finset.mem_image, and_imp, forall_and, Function.Injective.injOn, mem_range]
```

**lean_error:** tail step 1/2 ('simp only [Finset.image_subset_iff_subset_preimage, subset_iff, Finset.mem_preimage, exists_imp,'): <stdin>:1:96: unexpected end of input; expected ']'
