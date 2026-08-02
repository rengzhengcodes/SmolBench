# Filter.map_pi_map_coprodᵢ_le   (k=3, 4 tactics total)

file: `Mathlib/Order/Filter/Pi.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨{ x : α i | m i x ∈ t }, H, fun x hx => hH hx⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.7s, verify 2.9s, in=503, out=3279)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨m i ⁻¹' t, H, ?_⟩
intro k hk
have hmt : m i (k i) ∈ t := by
  simpa [Set.preimage, eval] using hk
have hfun : (fun j => m j (k j)) ∈ eval i ⁻¹' t := by
  simpa [eval] using hmt
have : (fun j => m j (k j)) ∈ s := hH hfun
simpa [eval] using this
```

**lean_error:** tail step 3/8 ('have hmt : m i (k i) ∈ t := by'): <stdin>:1:30: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.7s, verify 0.3s, in=435, out=11857)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨m i ⁻¹' t, H, _⟩
intro x hx
have h₃ : m i (x i) ∈ t := by
  have h₄ : eval i x ∈ m i ⁻¹' t := hx
  have h₅ : eval i x = x i := rfl
  rw [h₅] at h₄
  exact h₄
let y : (∀ j : ι, α j) := fun j => m j (x j)
have h₆ : y i ∈ t := by simp [y]; exact h₃
have h₇ : y ∈ eval i ⁻¹' t := by
  have h₈ : eval i y = y i := rfl
  rw [h₈]
  exact h₆
have h₈ : y ∈ s := hH h₇
have h₉ : y = (fun k i => m i (k i)) x := by
  funext j
  simp [y]
  <;> aesop
rw [h₉] at h₈
exact h₈
```

**lean_error:** tail step 3/20 ('have h₃ : m i (x i) ∈ t := by'): <stdin>:1:29: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 28.4s, verify 0.2s, in=424, out=3272)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨t₁, ht₁_mem, ht₁_subset⟩ := h i
exact ⟨t₁, ht₁_mem, ht₁_subset⟩
```

**lean_error:** tail step 2/2 ('exact ⟨t₁, ht₁_mem, ht₁_subset⟩'): application type mismatch
