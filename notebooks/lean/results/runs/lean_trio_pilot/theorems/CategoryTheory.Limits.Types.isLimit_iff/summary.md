# CategoryTheory.Limits.Types.isLimit_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨x, fun c j ↦ funext fun y ↦ (hx c y).1 j,
  fun c f hf ↦ funext fun y ↦ (hx c y).2 (f y) (fun j ↦ congr_fun (hf j) y)⟩
```

**True premises at k:** `funext`, `funext`, `congr_fun`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | X | ✘ | ✘ | ✘ | X | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | X | ✘ |
| `hint:3` | X | ✘ | ✘ | ✘ | X | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | X | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **exception**  (gen 4.4s, verify 300.1s, in=398, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' IsLimit.mk _ _
intros c' y
use x c' y
exact hx c' y
intros u hu v hv
apply hx c' y
intros j
rw [← hu j, ← hv j]
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=398, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact
  { lift := x
    fac := fun s => (hx s).1
    uniq := fun s m w => (hx s (m (𝟙 _))).2 (fun j => w j) }
```

**lean_error:** tail step 1/4 ('exact'): <stdin>:1:5: unexpected end of input

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=387, out=352)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isLimitOfIsEquivSection
exact h
```

**lean_error:** tail step 1/2 ('apply isLimitOfIsEquivSection'): unknown identifier 'isLimitOfIsEquivSection'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=378, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isLimitOfSectionsUnique
exact h
```

**lean_error:** tail step 1/2 ('apply isLimitOfSectionsUnique'): unknown identifier 'isLimitOfSectionsUnique'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 952.7s, verify 300.1s, in=374, out=7256)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsLimit.mk
· intro c₁
  use ⟨x c₁, fun y j => (hx c₁ y).1 j⟩
· intro c₁ m
  apply ConeMorphism.ext
  ext y
  exact (hx c₁ y).2 (m y) (fun j => ConeMorphism.w m j)
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=374, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨_, hx⟩
```

**lean_error:** tail step 1/1 ('exact ⟨_, hx⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.8s, verify 0.1s, in=1565, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact hx _ _ fun j ↦ hs j
exact fun x hx ↦ hx _ x fun j ↦ hs j
```

**lean_error:** tail step 1/2 ('exact hx _ _ fun j ↦ hs j'): function expected at

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=1565, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨x, fun c y ↦ (hx c y).2 fun j ↦ congr_fun (c.w j) ⟨⟩⟩
```

**lean_error:** tail step 1/1 ('exact ⟨x, fun c y ↦ (hx c y).2 fun j ↦ congr_fun (c.w j) ⟨⟩⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1554, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact funext (fun j ↦ hx j)
exact funext (fun j ↦ hx j)
exact congr_fun
```

**lean_error:** tail step 1/3 ('exact funext (fun j ↦ hx j)'): type mismatch

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 8.3s, verify 0.1s, in=1545, out=345)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply funext; intro; apply funext; intro; apply congr_fun
exact hx c_1 y
exact hx c_1 y
```

**lean_error:** tail step 1/3 ('apply funext; intro; apply funext; intro; apply congr_fun'): <stdin>:1:12: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 652.5s, verify 300.1s, in=1539, out=6747)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
funext
intro y
apply (hx d y).2
intro j
exact congr_fun (f.2 j) y
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1539, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `hint:3` · llama-31-405b-base · rollout 0 → **exception**  (gen 304.5s, verify 300.1s, in=5171, out=79)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact hx c ⟨s, hs⟩
exact fun s hs ↦ x c ⟨s, hs⟩
exact fun y ↦ hx c y
exact hx c y
exact fun x hx ↦ (hx c y).symm
exact fun c ↦ fun y ↦ x c y
exact fun c ↦ fun y ↦ hx c y
done
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 3.2s, verify 0.1s, in=5171, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩
```

**lean_error:** tail step 1/1 ("exact ⟨x, fun c y ↦ (hx c y).1, fun c y y' h ↦ (hx c y).2 _ h⟩"): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=5160, out=59)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨fun j => x c j (hx c (sectionOfCone c (c.pt) (sectionOfCone_pt c)).val), 
  fun y hy => funext (fun j => congr_fun (hy j) ⟨⟩)⟩
```

**lean_error:** tail step 1/2 ('exact ⟨fun j => x c j (hx c (sectionOfCone c (c.pt) (sectionOfCone_pt c)).val),'): <stdin>:1:79: unexpected end of input; expected '⟩'

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=5151, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨fun j => (x c) j, fun c' h => hx c' ⟨h⟩⟩
```

**lean_error:** tail step 1/1 ("exact ⟨fun j => (x c) j, fun c' h => hx c' ⟨h⟩⟩"): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 50.6s, verify 300.1s, in=5145, out=2485)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsLimit.mk _
intro s
refine ⟨x s, fun j ↦ funext fun y ↦ (hx s y).1 j y⟩
intro f hf
ext y
apply (hx s y).2
intro j
exact congr_fun (hf j) y
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=5145, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=5198, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact hx c ⟨s⟩ hs
exact hx c y fun j => congr_fun (c.fac ⟨s⟩ j) ⟨⟩
```

**lean_error:** tail step 1/2 ('exact hx c ⟨s⟩ hs'): invalid constructor ⟨...⟩, expected type must be an inductive type 

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 2.7s, verify 0.4s, in=5198, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨x, fun c' y ↦ (hx c' y).2⟩
```

**lean_error:** tail step 1/1 ("exact ⟨x, fun c' y ↦ (hx c' y).2⟩"): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=5187, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact funext (fun j ↦ hx c_1 y j)
exact funext (fun j ↦ hx c_1 y j)
exact congr_fun h
```

**lean_error:** tail step 1/3 ('exact funext (fun j ↦ hx c_1 y j)'): type mismatch

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=5178, out=250)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨λ _ s, x _ s, hx⟩
```

**lean_error:** tail step 1/1 ('exact ⟨λ _ s, x _ s, hx⟩'): <stdin>:1:12: expected '↦', '=>'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 350.8s, verify 301.8s, in=5175, out=6434)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
funext y,
apply hx.2 c₁ y
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=5175, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun ⟨⟩ ⟨⟩ ↦ funext fun j ↦ hx _ j, fun ⟨⟩ ↦ funext fun j ↦ hx _ j⟩'): invalid constructor ⟨...⟩, insufficient number of arguments, constructs 'CategoryTheory.Limits.IsLimit.mk' has #3 explicit fields, but only #2 provided
