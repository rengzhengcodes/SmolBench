# Filter.map_pi_map_coprodᵢ_le   (k=3, 4 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨{ x : α i | m i x ∈ t }, H, fun x hx => hH hx⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 183.1s, verify 0.3s, in=421, out=8154)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi m i ⁻¹' t, H
rintro k hk
exact hH (λ j, m j (k j)) hk
```

**lean_error:** tail step 3/3 ('exact hH (λ j, m j (k j)) hk'): <stdin>:1:13: expected '↦', '=>'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 201.8s, verify 0.1s, in=421, out=9027)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use t
exact H
intros k hk
dsimp
apply hH
exact hk
```

**lean_error:** tail step 1/6 ('use t'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 243.2s, verify 0.2s, in=421, out=10809)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi (m i ⁻¹' t)
exact H
apply preimage_mono
exact hH
```

**lean_error:** tail step 2/4 ('exact H'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 244.4s, verify 0.2s, in=421, out=10859)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi m i ⁻¹' t
exact H
intros k hk
apply hH
exact hk
```

**lean_error:** tail step 2/5 ('exact H'): type mismatch

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.1s, verify 0.1s, in=421, out=285)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using H
```

**lean_error:** tail step 1/1 ('simpa using H'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.7s, verify 0.1s, in=421, out=327)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨_, H, preimage_mono hH⟩
```

**lean_error:** tail step 1/1 ('exact ⟨_, H, preimage_mono hH⟩'): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 37.5s, verify 0.1s, in=421, out=1440)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨_, H, λ k hk => hH (by simpa using hk)⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 1025.1s, verify 0.0s, in=421, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
