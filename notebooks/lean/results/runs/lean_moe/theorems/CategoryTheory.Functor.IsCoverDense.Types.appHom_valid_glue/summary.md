# CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`  

**Ground-truth tail (from k):**
```lean
apply appHom_restrict
```

**True premises at k:** `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | · |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 12.1s, verify 0.2s, in=536, out=1811)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [appHom]
```

**final state (truncated):**
```
case h
C : Type u_1
inst✝⁵ : Category.{u_6, u_1} C
D : Type u_2
inst✝⁴ : Category.{u_5, u_2} D
E : Type u_3
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.1s, in=884, out=1347)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))"): <stdin>:1:57: expected token

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=2142, out=1013)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (ℱ:=ℱ) (G:=G) (X:=X) (Y:=Y) f a✝)
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (ℱ:=ℱ) (G:=G) (X:=X) (Y:=Y) f a✝)"): <stdin>:1:76: expected token

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=2036, out=1333)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))
```

**lean_error:** tail step 1/1 ("simpa using (appHom_restrict (α:=α) (ℱ':=ℱ') (f:=f) (x:=a✝))"): <stdin>:1:57: expected token
