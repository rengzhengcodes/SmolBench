# Polynomial.nodup_aroots_iff_of_splits   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Separable.lean`  

**Ground-truth tail (from k):**
```lean
rw [nodup_roots_iff_of_splits (map_ne_zero hf) h, separable_map]
```

**True premises at k:** `Polynomial.nodup_roots_iff_of_splits`, `Polynomial.map_ne_zero`, `Polynomial.separable_map`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=334, out=1282)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (Polynomial.nodup_aroots_iff (f:=f) (K:=K) hf h)
```

**lean_error:** tail step 1/1 ('simpa using (Polynomial.nodup_aroots_iff (f:=f) (K:=K) hf h)'): unknown constant 'Polynomial.nodup_aroots_iff'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=1204, out=1712)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hmap : (map (algebraMap F K) f) ≠ 0 := by
    exact map_ne_zero (f := algebraMap F K) hf
  simpa [aroots] using
    ((nodup_roots_iff_of_splits (f := map (algebraMap F K) f) hmap h).trans
      (separable_map (algebraMap F K)).symm)
```

**lean_error:** tail step 1/5 ('have hmap : (map (algebraMap F K) f) ≠ 0 := by'): <stdin>:1:46: unexpected end of input; expected '{'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.6s, verify 0.1s, in=3668, out=2473)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hfK : (map (algebraMap F K) f) ≠ 0 :=
    Polynomial.map_ne_zero (algebraMap F K) hf
  simpa [Polynomial.aroots] using
    ((Polynomial.nodup_roots_iff_of_splits (f:=map (algebraMap F K) f) hfK h).trans
      (by
        simpa using (Polynomial.separable_map (algebraMap F K) (p:=f))))
```

**lean_error:** tail step 1/6 ('have hfK : (map (algebraMap F K) f) ≠ 0 :='): <stdin>:1:42: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.5s, verify 2.0s, in=3349, out=4625)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h0 : (map (algebraMap F K) f) ≠ 0 := map_ne_zero hf
  have h' : (map (algebraMap F K) f).Splits (RingHom.id K) := by
    simpa using ((splits_map_iff (algebraMap F K) f).2 h)
  have hiff :=
    (nodup_roots_iff_of_splits (f := map (algebraMap F K) f) h0 h')
  simpa [aroots] using hiff.trans ((separable_map (algebraMap F K) (p := f)).symm)
```

**lean_error:** tail step 2/6 ("have h' : (map (algebraMap F K) f).Splits (RingHom.id K) := by"): <stdin>:1:62: unexpected end of input; expected '{'
