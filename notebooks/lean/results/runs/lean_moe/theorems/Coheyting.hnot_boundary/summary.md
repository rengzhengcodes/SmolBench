# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=278, out=689)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.0s, verify 1.3s, in=751, out=850)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Coheyting.boundary, hnot_inf_distrib]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.3s, verify 3.3s, in=1245, out=949)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold Coheyting.boundary
  rw [hnot_inf_distrib]
  simpa using sup_hnot_self (￢ a)
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.7s, verify 0.3s, in=1203, out=1373)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Coheyting.boundary, hnot_inf_distrib] using sup_hnot_self (￢ a)
```
