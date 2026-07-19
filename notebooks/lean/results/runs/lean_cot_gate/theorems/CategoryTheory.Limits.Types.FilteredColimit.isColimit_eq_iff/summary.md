# CategoryTheory.Limits.Types.FilteredColimit.isColimit_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xj).symm
```

**True premises at k:** `congrFun`, `CategoryTheory.Limits.IsColimit.comp_coconePointUniqueUpToIso_hom`, `CategoryTheory.Limits.Types.colimitCoconeIsColimit`, `Eq.symm`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · · · | ✘ · ✘ · |
| `hint:2` | ✓ ✓ ✓ ✓ | · ✘ · ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | X X X X X X X X | X X X X X X X X X X X X | X X X X X X X X |
| `noise:3` | X X X X X X X X | X X X X X X X X X X X X | X X X X X X X X |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 105.3s, verify 0.1s, in=383, out=4622)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact congr_fun (ht.fac (colimitCocone F) j) xj
```

**lean_error:** tail step 1/1 ('exact congr_fun (ht.fac (colimitCocone F) j) xj'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 112.2s, verify 0.2s, in=383, out=4933)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsColimit.fac (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom j]
```

**lean_error:** tail step 1/1 ('rw [IsColimit.fac (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).hom j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 201.8s, verify 0.2s, in=383, out=9067)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsColimit.fac (colimitCoconeIsColimit F) (t.ι.app j) xj]
```

**lean_error:** tail step 1/1 ('rw [← IsColimit.fac (colimitCoconeIsColimit F) (t.ι.app j) xj]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 258.6s, verify 0.2s, in=383, out=11514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsColimit.fac ht j]
```

**lean_error:** tail step 1/1 ('rw [← IsColimit.fac ht j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=383, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 0.9s, verify 1.2s, in=383, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 2.4s, verify 0.1s, in=383, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsColimit.coconePointUniqueUpToIso]
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.6s, verify 0.1s, in=383, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsColimit.coconePointUniqueUpToIso]
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.9s, verify 0.1s, in=383, out=370)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← IsColimit.coconePointUniqueUpToIso_inv_ι]
```

**lean_error:** tail step 1/1 ('simp [← IsColimit.coconePointUniqueUpToIso_inv_ι]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 12.4s, verify 0.1s, in=383, out=431)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.0s, verify 0.1s, in=383, out=445)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
convert (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).inv_app_apply
  (colimitCocone F).ι.app j xj
```

**lean_error:** tail step 1/2 ('convert (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).inv_app_apply'): invalid field 'inv_app_apply', the environment does not contain 'CategoryTheory.Iso.inv_app_apply'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 13.1s, verify 0.1s, in=383, out=458)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 131.4s, verify 0.1s, in=2542, out=5913)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 133.9s, verify 0.1s, in=2542, out=6034)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 211.1s, verify 0.1s, in=2542, out=9448)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 228.6s, verify 0.1s, in=2542, out=10174)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j) xj).symm
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.8s, verify 0.2s, in=2542, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=2542, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.3s, verify 0.2s, in=2542, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.1s, in=2542, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [IsColimit.colimit_cocone_equiv_colimit_coconeIsColimit]
```

**lean_error:** tail step 1/1 ('simp [IsColimit.colimit_cocone_equiv_colimit_coconeIsColimit]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.5s, verify 0.5s, in=2542, out=435)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
convert congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xi).symm
```

**lean_error:** tail step 2/2 ('(IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xi).symm'): <stdin>:1:2: unknown tactic

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 18.5s, verify 0.5s, in=2542, out=649)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
convert congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j).symm xi <;>
  simp [Equiv.symm_apply]
```

**lean_error:** tail step 2/3 ('(IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) j).symm xi <;>'): <stdin>:1:2: unknown tactic

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 20.0s, verify 0.3s, in=2542, out=705)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
convert Iff.rfl
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xi).symm
```

**lean_error:** tail step 2/3 ('exact (congrFun'): <stdin>:1:15: unexpected end of input; expected ')', ',' or ':'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 29.6s, verify 0.1s, in=2542, out=1067)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (congrFun
  (IsColimit.comp_coconePointUniqueUpToIso_hom ht (colimitCoconeIsColimit F) _) xi).symm
```

**lean_error:** tail step 1/2 ('exact (congrFun'): <stdin>:1:15: unexpected end of input; expected ')', ',' or ':'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **exception**  (gen 0.3s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **exception**  (gen 0.3s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **exception**  (gen 0.3s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **exception**  (gen 0.6s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **exception**  (gen 0.7s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **exception**  (gen 0.7s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://35.175.65.249:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 1.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **exception**  (gen 0.1s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **exception**  (gen 0.4s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **exception**  (gen 0.2s, verify 0.0s, in=0, out=0)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** HTTPError: 400 Bad Request for url http://18.218.93.110:8000/v1/chat/completions: {"error":{"message":"This model's maximum context length is 40960 tokens. However, you requested 32768 output tokens and your prompt contains at least 8193 input tokens, for a total of at least 40961 tokens. Please red
