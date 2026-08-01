# Filter.limsSup_principal   (k=1, 2 tactics total)

file: `Mathlib/Order/LiminfLimsup.lean`  

**Ground-truth tail (from k):**
```lean
exact csInf_upper_bounds_eq_csSup h hs
```

**True premises at k:** `csInf_upper_bounds_eq_csSup`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.6s, verify 0.2s, in=338, out=2539)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases hs with ⟨y, hy⟩
have hb : BddBelow {a | ∀ x ∈ s, x ≤ a} :=
  ⟨y, by
    intro a ha
    exact ha y hy⟩
apply le_antisymm
·
  have hmem : ∀ x ∈ s, x ≤ sSup s :=
    by
      intro x hx
      exact le_csSup h hx
  exact csInf_le hb hmem
·
  apply le_csInf hb
  intro a ha
  exact csSup_le h ha
```

**lean_error:** tail step 2/16 ('have hb : BddBelow {a | ∀ x ∈ s, x ≤ a} :='): <stdin>:1:42: unexpected end of input

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=602, out=515)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=946, out=622)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.7s, verify 0.1s, in=922, out=803)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [upperBounds] using (csInf_upper_bounds_eq_csSup (s:=s) h hs)
```
