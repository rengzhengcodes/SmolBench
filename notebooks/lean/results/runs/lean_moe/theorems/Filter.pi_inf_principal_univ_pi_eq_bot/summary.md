# Filter.pi_inf_principal_univ_pi_eq_bot   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
filter_upwards [mem_pi_of_mem i hi] with x using mt fun h => h i trivial
```

**True premises at k:** `Filter.mem_pi_of_mem`, `mt`, `trivial`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 30.1s, verify 0.1s, in=349, out=7904)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Filter.mem_pi.2 ⟨i, hi⟩
```

**lean_error:** tail step 1/1 ('exact Filter.mem_pi.2 ⟨i, hi⟩'): application type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.8s, verify 0.7s, in=914, out=2135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hmem : eval i ⁻¹' ((s i)ᶜ) ∈ pi f := mem_pi_of_mem i hi
  refine mem_of_superset hmem ?_
  intro x hx
  intro hxmem
  have : x i ∈ s i := hxmem i (by trivial)
  exact hx this
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 3.0s, in=1097, out=1642)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine mem_of_superset (mem_pi_of_mem i hi) ?_
intro x hx
intro hxmem
exact hx (hxmem i (by trivial))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.5s, verify 0.5s, in=1093, out=2468)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hmem : eval i ⁻¹' (s i)ᶜ ∈ pi f := mem_pi_of_mem i hi
  refine mem_of_superset hmem ?_
  intro x hx
  have hx' : x i ∈ (s i)ᶜ := by
    simpa [Set.preimage, Set.mem_setOf_eq] using hx
  intro hxmem
  exact hx' (hxmem i (mem_univ i))
```

**lean_error:** tail step 4/7 ("have hx' : x i ∈ (s i)ᶜ := by"): <stdin>:1:29: unexpected end of input; expected '{'
