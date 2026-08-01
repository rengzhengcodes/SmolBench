# CategoryTheory.Limits.Types.isLimit_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨x, fun c j ↦ funext fun y ↦ (hx c y).1 j,
  fun c f hf ↦ funext fun y ↦ (hx c y).2 (f y) (fun j ↦ congr_fun (hf j) y)⟩
```

**True premises at k:** `funext`, `funext`, `congr_fun`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | X X | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | X X | ✘ | ✘ |
| `noise:3` | X ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **exception**  (gen 3.1s, verify 300.1s, in=398, out=56)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' IsLimit.mk _ _
intros c' y
use x c' y
exact hx c' y
intros u hu v hv huv
apply hx c' u
intro j
rw [← hu j, ← hv j, huv]
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · llama-31-405b-base · rollout 0 → **exception**  (gen 3.5s, verify 300.1s, in=398, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' IsLimit.mk _ _
intros c' y
use x c' y
constructor
· intro j
  exact (hx c' y).1 j
· intro y'
  exact hx c' y y'
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=372, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsLimit.mkConeMorphism]
intro s
use x s s.pt
constructor
· intro j
  erw [hx]
· intro m hm
  exact (hx s s.pt).2 m hm
```

**lean_error:** tail step 1/8 ('rw [IsLimit.mkConeMorphism]'): failed to rewrite using equation theorems for 'CategoryTheory.Limits.IsLimit.mkConeMorphism'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 51.1s, verify 0.1s, in=387, out=3186)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isLimitCone.mk
exact x
intros c1 y j
apply (hx c1 y).1
intros c1 y y1 h
apply (hx c1 y).2
exact h
```

**lean_error:** tail step 1/7 ('apply isLimitCone.mk'): unknown identifier 'isLimitCone.mk'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=1565, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact hx _ _ .2 .1,
exact fun y hy ↦ hx _ y .2 .2 _ hy,
exact fun y ↦ hx _ y .2 .1,
exact hx _ _ .2 .2 _ this
```

**lean_error:** tail step 1/4 ('exact hx _ _ .2 .1,'): <stdin>:1:14: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1538, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact x cs ⟨⟩
funext s
exact hx cs s.2 s.1 j ⟨⟩
```

**lean_error:** tail step 1/3 ('exact x cs ⟨⟩'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 1.1s, in=1554, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact funext (fun j ↦ hx j)
exact funext (fun j ↦ hx j)
exact congr_fun
```

**lean_error:** tail step 1/3 ('exact funext (fun j ↦ hx j)'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **exception**  (gen 603.4s, verify 300.1s, in=5171, out=116)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact congrFun (hx c_1 (x c_1 y)) j,
exact hx c_1 y,
exact congrFun (hx c_1 (x c_1 y)) j,
exact hx c_1 y,
exact funext fun j => congrFun (hx c_1 (x c_1 y)) j,
exact funext fun j => hx c_1 y,
exact funext fun j => congrFun (hx c_1 (x c_1 y)) j,
exact funext fun j => hx c_1 y
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · llama-31-405b-base · rollout 0 → **exception**  (gen 303.6s, verify 300.1s, in=5171, out=131)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact hx c ⟨s, hs⟩
exact fun s hs ↦ x c ⟨s, hs⟩
exact fun y ↦ hx c y
exact fun y hy ↦ hx c y
exact fun y ↦ funext fun j ↦ congr_fun (hx c y).1 j
exact fun y hy ↦ funext fun j ↦ congr_fun (hx c y).2 j hy j
exact fun y hy ↦ funext fun j ↦ congr_fun (hx c y).2 j hy j
exact fun y hy ↦ hy ⟨⟩
exact fun y hy ↦ hy ⟨⟩
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 2.0s, in=5141, out=36)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsLimit.mk fun s => ⟨x s ⟨⟩, funext fun j => hx s ⟨⟩ j, fun y hy => hx s y funext hy⟩
```

**lean_error:** tail step 1/1 ('exact IsLimit.mk fun s => ⟨x s ⟨⟩, funext fun j => hx s ⟨⟩ j, fun y hy => hx s y funext hy⟩'): invalid constructor ⟨...⟩, expected type must be an inductive type 

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=5160, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact hx _ _ j
```

**lean_error:** tail step 1/1 ('exact hx _ _ j'): function expected at

### `noise:3` · llama-31-405b-base · rollout 0 → **exception**  (gen 303.3s, verify 300.1s, in=5198, out=59)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact hx c ⟨s, hs⟩
exact hx c s.1
apply funext
intro j
exact (hx c s.1).2 j
exact hx c s.1
apply funext
intro j
exact (hx c s.1).2 j
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=5198, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact congrFun (hx c y).2
exact funext fun _ => (hx c y).1 _
```

**lean_error:** tail step 1/2 ('exact congrFun (hx c y).2'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=5586, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact x c ⟨⟩
funext s
exact hx c s.2 s.1 j
```

**lean_error:** tail step 1/3 ('exact x c ⟨⟩'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.3s, in=5187, out=55)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact hx c_1 y
```

**lean_error:** tail step 1/1 ('exact hx c_1 y'): type mismatch
