# Set.chainHeight_eq_iSup_Iic   (k=2, 3 tactics total)

file: `Mathlib/Order/Height.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ? | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.9s, verify 0.5s, in=380, out=3001)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Set.preimage, ofDual, toDual_ofDual, Iic, Ici] using rfl
```

**lean_error:** tail step 1/1 ('simpa [Set.preimage, ofDual, toDual_ofDual, Iic, Ici] using rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **given_up**  (gen 194.3s, verify 0.5s, in=333, out=26757)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : (⨆ i ∈ ⇑ofDual ⁻¹' s, chainHeight (⇑ofDual ⁻¹' s ∩ Ici i)) = (⨆ i ∈ s, chainHeight ({x : α | x ∈ s ∧ x ≤ i})) := by sorry
have h₂ : (⨆ i ∈ s, chainHeight (⇑ofDual ⁻¹' (s ∩ Iic i))) = (⨆ i ∈ s, chainHeight ({x : α | x ∈ s ∧ x ≤ i})) := by sorry
have h₃ : (⨆ i ∈ ⇑ofDual ⁻¹' s, chainHeight (⇑ofDual ⁻¹' s ∩ Ici i)) = (⨆ i ∈ s, chainHeight (⇑ofDual ⁻¹' (s ∩ Iic i))) := by sorry
exact h₃
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=323, out=893)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
iSup_congr (fun i hi => ?_)
```

**lean_error:** tail step 1/1 ('iSup_congr (fun i hi => ?_)'): <stdin>:1:1: unknown tactic
