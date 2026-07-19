# Filter.map_pi_map_coprodᵢ_le   (k=3, 4 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨{ x : α i | m i x ∈ t }, H, fun x hx => hH hx⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.8s, verify 0.1s, in=437, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t,
simp [H, hH, preimage_preimage]
```

**lean_error:** tail step 1/2 ('use t,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.4s, in=437, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t,
split,
assumption,
fun x hx => hH hx
```

**lean_error:** tail step 1/4 ('use t,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=437, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t,
split,
assumption,
simp [eval, Set.preimage],
exact hH,
```

**lean_error:** tail step 1/5 ('use t,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=437, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t,
simp only [mem_filter, Function.comp_apply],
exact H,
simp only [preimage_comp, eval],
exact hH,
```

**lean_error:** tail step 1/5 ('use t,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=437, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, hH⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, hH⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=437, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨t, H, fun k hk => hH hk⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t, H, fun k hk => hH hk⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=437, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨m i ⁻¹' t, H, fun k hk => hH ⟨k, hk⟩⟩
```

**lean_error:** tail step 1/1 ("exact ⟨m i ⁻¹' t, H, fun k hk => hH ⟨k, hk⟩⟩"): invalid constructor ⟨...⟩, expected type must be an inductive type 

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=437, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨m i ⁻¹' t, H, fun k hk => hH ⟨k, rfl⟩ hk⟩
```

**lean_error:** tail step 1/1 ("exact ⟨m i ⁻¹' t, H, fun k hk => hH ⟨k, rfl⟩ hk⟩"): invalid constructor ⟨...⟩, expected type must be an inductive type 
