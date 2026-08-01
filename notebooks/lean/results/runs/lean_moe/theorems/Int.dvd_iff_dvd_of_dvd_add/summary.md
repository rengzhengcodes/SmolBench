# Int.dvd_iff_dvd_of_dvd_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.dvd_iff_dvd_of_dvd_sub H, Int.dvd_neg]
```

**True premises at k:** `Int.dvd_iff_dvd_of_dvd_sub`, `Int.dvd_neg`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.8s, verify 0.3s, in=268, out=2578)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases H with ⟨k, hk⟩
constructor
· intro hb
  rcases hb with ⟨m, hm⟩
  refine ⟨k - m, ?_⟩
  have : c = a * k - a * m := by
    linear_combination hk - hm
  simpa [mul_sub] using this
· intro hc
  rcases hc with ⟨m, hm⟩
  refine ⟨k - m, ?_⟩
  have : b = a * k - a * m := by
    linear_combination hk - hm
  simpa [mul_sub] using this
```

**lean_error:** tail step 3/14 ('· intro hb'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.0s, verify 0.1s, in=708, out=1381)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub H)
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.1s, in=1871, out=2127)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have H' : a ∣ b - (-c) := by
  simpa [sub_eq_add_neg] using H
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub (a:=a) (b:=b) (c:=-c) H')
```

**lean_error:** tail step 1/3 ("have H' : a ∣ b - (-c) := by"): <stdin>:1:28: unexpected end of input; expected '{'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.3s, verify 0.1s, in=1743, out=2442)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have H' : a ∣ b - -c := by
  simpa [Int.sub_neg] using H
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub (a:=a) (b:=b) (c:=-c) H')
```

**lean_error:** tail step 1/3 ("have H' : a ∣ b - -c := by"): <stdin>:1:26: unexpected end of input; expected '{'
