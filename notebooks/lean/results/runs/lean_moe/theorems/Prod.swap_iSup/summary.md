# Prod.swap_iSup   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iSup, swap_sSup, ← range_comp, Function.comp]
```

**True premises at k:** `iSup`, `Prod.swap_sSup`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=356, out=507)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.2s, in=1186, out=738)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold iSup
  simpa [Set.range_comp, Function.comp] using (Prod.swap_sSup (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp, Function.comp] using (Prod.swap_sSup (s := Set.range f))'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.2s, in=2605, out=880)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold iSup
  simpa [Set.range_comp, Function.comp] using (swap_sSup (s := Set.range f))
```

**lean_error:** tail step 2/2 ('simpa [Set.range_comp, Function.comp] using (swap_sSup (s := Set.range f))'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 4.7s, in=2481, out=1140)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold iSup
  simpa [range_comp] using (swap_sSup (s := range f))
```

**lean_error:** tail step 2/2 ('simpa [range_comp] using (swap_sSup (s := range f))'): type mismatch
