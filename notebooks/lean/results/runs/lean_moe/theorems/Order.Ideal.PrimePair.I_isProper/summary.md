# Order.Ideal.PrimePair.I_isProper   (k=2, 3 tactics total)

file: `Mathlib/Order/PrimeIdeal.lean`  

**Ground-truth tail (from k):**
```lean
rwa [← IF.compl_I_eq_F] at h
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.2s, in=276, out=1352)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro hw
  exact (Set.disjoint_left.mp IF.disjoint) h hw
```

**lean_error:** tail step 2/2 ('exact (Set.disjoint_left.mp IF.disjoint) h hw'): invalid field 'disjoint', the environment does not contain 'Order.Ideal.PrimePair.disjoint'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 98.0s, verify 0.1s, in=220, out=14422)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₂ : w ↑IF.F := h
have h₃ : w ∉ IF.I := by
  intro h₄
  have h₅ : w ↑IF.F := h₂
  have h₆ : w ↑IF.I := h₄
  have h₇ : w ↑IF.F ∩ ↑IF.I := Set.mem_inter h₅ h₆
  have h₈ : ↑IF.F ∩ ↑IF.I = ∅ := IF.disjoint
  rw [h₈] at h₇
  exact Set.not_mem_empty w h₇
exact h₃
```

**lean_error:** tail step 1/10 ('have h₂ : w ↑IF.F := h'): function expected at

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.2s, in=220, out=556)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h'
exact IF.disjoint h h'
```

**lean_error:** tail step 2/2 ("exact IF.disjoint h h'"): invalid field 'disjoint', the environment does not contain 'Order.Ideal.PrimePair.disjoint'
