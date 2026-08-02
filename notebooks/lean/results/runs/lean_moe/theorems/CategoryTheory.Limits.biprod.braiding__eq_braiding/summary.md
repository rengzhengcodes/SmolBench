# CategoryTheory.Limits.biprod.braiding'_eq_braiding   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
aesop_cat
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=345, out=172)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 47.8s, verify 0.1s, in=298, out=6769)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.3s, in=291, out=545)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
<;> simp [braiding', braiding]
```

**lean_error:** tail step 2/2 ("<;> simp [braiding', braiding]"): <stdin>:1:0: expected tactic
