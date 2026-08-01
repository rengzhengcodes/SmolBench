# Filter.map_pi_map_coprodᵢ_le   (k=3, 4 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨{ x : α i | m i x ∈ t }, H, fun x hx => hH hx⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=437, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t,
split,
assumption,
fun x hx => hH hx
```

**lean_error:** tail step 1/4 ('use t,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.4s, in=405, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨m i ⁻¹' t, H, _⟩
rw [← preimage_comp]
exact hH
```

**lean_error:** tail step 3/3 ('exact hH'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=426, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨t, H, _⟩
simp only [preimage, Set.image_subset_iff]
intro x hx
simp [hH hx]
```

**lean_error:** tail step 1/4 ("refine' ⟨t, H, _⟩"): application type mismatch
