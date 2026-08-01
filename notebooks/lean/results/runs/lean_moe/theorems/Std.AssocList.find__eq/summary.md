# Std.AssocList.find?_eq   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/AssocList.lean`  

**Ground-truth tail (from k):**
```lean
simp [find?_eq_findEntry?]
```

**True premises at k:** `Std.AssocList.find?_eq_findEntry?`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=332, out=612)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=595, out=1472)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [findEntry?] using (find?_eq_findEntry? (a:=a) (l:=l))
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=800, out=923)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [findEntry?] using (find?_eq_findEntry? (a:=a) (l:=l))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=802, out=1697)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [find?_eq_findEntry?, findEntry?, toList]
```
