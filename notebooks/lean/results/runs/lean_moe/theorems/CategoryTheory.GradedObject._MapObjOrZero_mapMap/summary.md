# CategoryTheory.GradedObject.ιMapObjOrZero_mapMap   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/GradedObject.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ιMapObjOrZero_eq_zero _ _ _ _ h, zero_comp, comp_zero]
```

**True premises at k:** `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`, `CategoryTheory.Limits.zero_comp`, `CategoryTheory.Limits.comp_zero`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=489, out=615)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ιMapObjOrZero, h]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.7s, verify 0.1s, in=1119, out=2132)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,
      ιMapObjOrZero_eq_zero (X:=Y) (p:=p) (i:=i) (j:=j) h]
```

**lean_error:** tail step 1/2 ('simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,'): <stdin>:1:58: unexpected end of input; expected ']'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 1.2s, in=1534, out=2852)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,
      ιMapObjOrZero_eq_zero (X:=Y) (p:=p) (i:=i) (j:=j) h]
```

**lean_error:** tail step 1/2 ('simp [ιMapObjOrZero_eq_zero (X:=X) (p:=p) (i:=i) (j:=j) h,'): <stdin>:1:58: unexpected end of input; expected ']'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 10.5s, verify 0.2s, in=1506, out=2104)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
...
```
