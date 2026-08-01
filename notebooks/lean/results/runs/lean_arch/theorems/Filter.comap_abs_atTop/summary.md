# Filter.comap_abs_atTop   (k=4, 5 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact hx.imp And.left And.right
```

**True premises at k:** `And.left`, `And.right`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=310, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases hx with (h|h)
case h => exact Or.inl (mem_Iic.mpr h)
case h => exact Or.inr (mem_Ici.mpr h)
```

**lean_error:** tail step 2/3 ('case h => exact Or.inl (mem_Iic.mpr h)'): Case tag 'h' not found.

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=280, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mem_union, mem_Iic, mem_Ici]
simp only [Prod.fst, Prod.snd, and_true, le_refl, or_true, and_self]
exact hx.symm
```

**lean_error:** tail step 3/3 ('exact hx.symm'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 25.6s, verify 0.3s, in=299, out=1508)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mem_union, Iic, Ici, Prod.fst, Prod.snd]
cases hx
case inl hx : x ≤ a ∧ x ≤ -b
  exact Or.inl (hx.1)
case inr hx : -a ≤ x ∧ b ≤ x
  exact Or.inr (hx.2)
```

**lean_error:** tail step 3/6 ('case inl hx : x ≤ a ∧ x ≤ -b'): No goals with tag inl unify with the term x ≤ a ∧
