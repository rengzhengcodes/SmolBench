# List.set_eq_take_cons_drop   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop _ h]
```

**True premises at k:** `List.set_eq_modifyNth`, `List.modifyNth_eq_take_cons_drop`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.7s, in=297, out=306)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.set, h]
```

**lean_error:** tail step 1/1 ('simp [List.set, h]'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=758, out=865)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [set_eq_modifyNth a] using (modifyNth_eq_take_cons_drop (fun _ => a) (n:=n) (l:=l) h)
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.8s, verify 0.2s, in=1555, out=777)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth (a:=a) (n:=n) (l:=l)]
  simpa using (modifyNth_eq_take_cons_drop (f:=fun _ => a) (n:=n) (l:=l) h)
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=1479, out=1011)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [modifyNth_eq_take_cons_drop (f:=fun _ => a) h] using (set_eq_modifyNth (a:=a) n l)
```
