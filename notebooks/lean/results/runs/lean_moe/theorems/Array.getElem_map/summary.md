# Array.getElem_map   (k=4, 5 tactics total)

file: `.lake/packages/std/Std/Data/Array/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp_all
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=332, out=248)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [eq] using h
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=277, out=615)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h2 : i < size as := by
  rw [eq] at h
  exact h
exact h2
```

**lean_error:** tail step 1/4 ('have h2 : i < size as := by'): <stdin>:1:27: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.7s, verify 0.2s, in=278, out=530)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [eq] at h
exact h
```
