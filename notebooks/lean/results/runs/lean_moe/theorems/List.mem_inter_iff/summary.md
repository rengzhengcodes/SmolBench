# List.mem_inter_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
cases l₁ <;> simp [List.inter_def, mem_filter]
```

**True premises at k:** `List.inter_def`, `List.mem_filter`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.1s, in=311, out=315)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using List.mem_inter
```

**lean_error:** tail step 1/1 ('simpa using List.mem_inter'): unknown constant 'List.mem_inter'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.8s, verify 0.7s, in=712, out=1522)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun a => a ∈ l₂) (as:=l₁))
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.3s, verify 0.1s, in=1610, out=718)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun y => y ∈ l₂) (as:=l₁))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.8s, verify 0.1s, in=1515, out=1350)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [List.inter_def] using (List.mem_filter (x:=x) (p:=fun a => a ∈ l₂) (as:=l₁))
```
