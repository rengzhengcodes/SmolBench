# Filter.map_pi_map_coprodᵢ_le   (k=3, 4 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨{ x : α i | m i x ∈ t }, H, fun x hx => hH hx⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=421, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, λ x hx => hH hx⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, λ x hx => hH hx⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=421, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, fun x hx => hH hx⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, fun x hx => hH hx⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=421, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, subset.trans hH (preimage_mono (Pi_eval_subset _ _))⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, subset.trans hH (preimage_mono (Pi_eval_subset _ _))⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 5.6s, verify 0.4s, in=421, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, fun x hx => hH hx⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, fun x hx => hH hx⟩'): application type mismatch
