# CategoryTheory.oppositeShiftFunctorAdd'_hom_app   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Opposite.lean`  

**Ground-truth tail (from k):**
```lean
simp only [shiftFunctorAdd'_eq_shiftFunctorAdd, oppositeShiftFunctorAdd_hom_app]
```

**True premises at k:** `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`, `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=395, out=858)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.3s, in=843, out=759)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using oppositeShiftFunctorAdd_hom_app
```

**lean_error:** tail step 1/1 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using oppositeShiftFunctorAdd_hom_app"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=1283, out=1416)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using
  (oppositeShiftFunctorAdd_hom_app (X:=X) (a:=a) (b:=b))
```

**lean_error:** tail step 1/2 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using"): <stdin>:1:49: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.2s, in=1257, out=1167)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using
  (oppositeShiftFunctorAdd_hom_app (C:=C) (A:=A) (a:=a) (b:=b) (X:=X))
```

**lean_error:** tail step 1/2 ("simpa [shiftFunctorAdd'_eq_shiftFunctorAdd] using"): <stdin>:1:49: unexpected end of input
