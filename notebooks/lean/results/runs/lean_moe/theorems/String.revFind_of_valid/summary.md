# String.revFind_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using revFindAux_of_valid p s.1.reverse []
```

**True premises at k:** `String.revFindAux_of_valid`, `List.reverse`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.1s, in=326, out=449)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [revFind]
```

**lean_error:** tail step 1/1 ('simpa [revFind]'): tactic 'assumption' failed

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.9s, verify 0.1s, in=908, out=2366)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [String.revFind, List.append_nil, List.reverse_reverse] using
    (revFindAux_of_valid (p) (List.reverse s.data) [])
```

**lean_error:** tail step 1/2 ('simpa [String.revFind, List.append_nil, List.reverse_reverse] using'): <stdin>:1:67: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=2699, out=1293)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [String.revFind, List.reverse] using
    (String.revFindAux_of_valid (p) (l := s.data.reverse) (r := []))
```

**lean_error:** tail step 1/2 ('simpa [String.revFind, List.reverse] using'): <stdin>:1:42: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 16.3s, verify 0.2s, in=2513, out=2469)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold revFind
  simpa [List.append_nil, List.reverse_reverse] using
    (revFindAux_of_valid (p) (List.reverse s.data) [])
```

**lean_error:** tail step 2/3 ('simpa [List.append_nil, List.reverse_reverse] using'): <stdin>:1:51: unexpected end of input
