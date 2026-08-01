# Std.RBSet.mem_toList_insert   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [mem_toList] using RBNode.mem_insert ht₂ ht₁
```

**True premises at k:** `Std.RBSet.mem_toList`, `Std.RBNode.mem_insert`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.1s, verify 0.7s, in=386, out=3391)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [RBSet.mem_toList] using (RBSet.mem_insert (t:=t) (a:=v) (b:=v'))
```

**lean_error:** tail step 1/1 ("simpa [RBSet.mem_toList] using (RBSet.mem_insert (t:=t) (a:=v) (b:=v'))"): unknown constant 'Std.RBSet.mem_insert'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.9s, in=1214, out=2134)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using
    (RBNode.mem_insert (t:=t.1) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using'): <stdin>:1:57: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.7s, in=2763, out=2067)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using
  (Std.RBNode.mem_insert (t:=t.1) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [RBSet.mem_toList, RBSet.find?, RBSet.insert] using'): <stdin>:1:57: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.4s, in=2601, out=1362)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Std.RBSet.mem_toList] using
  (Std.RBNode.mem_insert (t:=t.val) (v:=v) (v':=v') ht₂ ht₁)
```

**lean_error:** tail step 1/2 ('simpa [Std.RBSet.mem_toList] using'): <stdin>:1:34: unexpected end of input
