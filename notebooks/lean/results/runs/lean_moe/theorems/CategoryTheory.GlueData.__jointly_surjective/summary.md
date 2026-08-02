# CategoryTheory.GlueData.ι_jointly_surjective   (k=5, 6 tactics total)

file: `Mathlib/CategoryTheory/GlueData.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨i, y, eq⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.3s, verify 0.1s, in=549, out=469)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, by simpa using eq⟩
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 14.3s, verify 0.2s, in=513, out=1649)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨i, y, _⟩
<;> rw [eq]
<;> simp [Category.id_apply]
```

**lean_error:** tail step 2/3 ('<;> rw [eq]'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.1s, verify 0.4s, in=500, out=427)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨i, y, _⟩
rw [eq]
simp
```
