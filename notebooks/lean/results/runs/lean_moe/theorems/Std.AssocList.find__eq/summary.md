# Std.AssocList.find?_eq   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/AssocList.lean`  

**Ground-truth tail (from k):**
```lean
simp [find?_eq_findEntry?]
```

**True premises at k:** `Std.AssocList.find?_eq_findEntry?`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=332, out=612)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 117.7s, verify 0.1s, in=277, out=16020)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Option.map_congr
<;> rfl
<;> apply List.find?_congr
<;> constructor <;> intro h <;> rw [eq_comm] at * <;> exact h
<;> rfl
```

**lean_error:** tail step 1/5 ('apply Option.map_congr'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=276, out=529)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil => simp
| cons k v t ih => simp_all [AssocList.find?, AssocList.toList, List.find?]
```

**lean_error:** tail step 1/3 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=595, out=1472)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [findEntry?] using (find?_eq_findEntry? (a:=a) (l:=l))
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 30.6s, verify 0.2s, in=540, out=4083)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Std.AssocList.find?_eq_findEntry?]
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.7s, verify 0.2s, in=548, out=595)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
simp [AssocList.findEntry?, List.find?]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=800, out=923)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [findEntry?] using (find?_eq_findEntry? (a:=a) (l:=l))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 28.4s, verify 0.2s, in=745, out=3823)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Std.AssocList.find?_eq_findEntry?]
<;> rw [Std.AssocList.findEntry?]
<;> rfl
```

**lean_error:** tail step 2/3 ('<;> rw [Std.AssocList.findEntry?]'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.3s, in=756, out=576)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
<;> simp [AssocList.findEntry?, List.find?]
```

**lean_error:** tail step 2/2 ('<;> simp [AssocList.findEntry?, List.find?]'): <stdin>:1:0: expected tactic

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=802, out=1697)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [find?_eq_findEntry?, findEntry?, toList]
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 35.6s, verify 0.2s, in=804, out=4821)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Std.AssocList.find?_eq_findEntry?, AssocList.findEntry?]
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.4s, verify 0.2s, in=778, out=792)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [find?_eq_findEntry?]
simp
congr
```
