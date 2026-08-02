# Int.dvd_iff_dvd_of_dvd_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.dvd_iff_dvd_of_dvd_sub H, Int.dvd_neg]
```

**True premises at k:** `Int.dvd_iff_dvd_of_dvd_sub`, `Int.dvd_neg`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

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

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 0.2s, in=210, out=1531)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨k, hk⟩ := H
constructor
· intro hb
  obtain ⟨m, hm⟩ := hb
  have hc : c = a * (k - m) := by linarith
  exact ⟨k - m, by linarith⟩
· intro hc
  obtain ⟨m, hm⟩ := hc
  have hb : b = a * (k - m) := by linarith
  exact ⟨k - m, by linarith⟩
```

**lean_error:** tail step 3/10 ('· intro hb'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=211, out=653)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  have : a ∣ (b + c) - b := dvd_sub H h
  simpa using this
· intro h
  have : a ∣ (b + c) - c := dvd_sub H h
  simpa using this
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.0s, verify 0.1s, in=708, out=1381)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub H)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 59.3s, verify 0.1s, in=653, out=7905)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have H' : a ∣ b - (-c) := by
  have h : b + c = b - (-c) := by ring
  rw [h] at H
  exact H
have h : a ∣ b ↔ a ∣ c := Iff.trans (Int.dvd_iff_dvd_of_dvd_sub H') (Int.dvd_neg)
exact h
```

**lean_error:** tail step 1/6 ("have H' : a ∣ b - (-c) := by"): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.1s, in=637, out=1356)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Int.dvd_iff_dvd_of_dvd_sub H
rw [Int.dvd_neg]
```

**lean_error:** tail step 1/2 ('apply Int.dvd_iff_dvd_of_dvd_sub H'): tactic 'apply' failed, failed to unify

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.1s, in=1871, out=2127)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have H' : a ∣ b - (-c) := by
  simpa [sub_eq_add_neg] using H
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub (a:=a) (b:=b) (c:=-c) H')
```

**lean_error:** tail step 1/3 ("have H' : a ∣ b - (-c) := by"): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 38.8s, verify 0.1s, in=1857, out=5129)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have H' : a ∣ b - (-c) := by
  convert H using 1
  <;> ring
have h1 : a ∣ b ↔ a ∣ -c := Int.dvd_iff_dvd_of_dvd_sub H'
have h2 : a ∣ -c ↔ a ∣ c := Int.dvd_neg
have h3 : a ∣ b ↔ a ∣ c := h1.trans h2
exact h3
```

**lean_error:** tail step 1/7 ("have H' : a ∣ b - (-c) := by"): <stdin>:1:28: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=1784, out=632)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Int.dvd_iff_dvd_of_dvd_sub H
rw [Int.dvd_neg]
```

**lean_error:** tail step 1/2 ('apply Int.dvd_iff_dvd_of_dvd_sub H'): tactic 'apply' failed, failed to unify

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.3s, verify 0.1s, in=1743, out=2442)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have H' : a ∣ b - -c := by
  simpa [Int.sub_neg] using H
simpa [Int.dvd_neg] using (Int.dvd_iff_dvd_of_dvd_sub (a:=a) (b:=b) (c:=-c) H')
```

**lean_error:** tail step 1/3 ("have H' : a ∣ b - -c := by"): <stdin>:1:26: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 50.3s, verify 0.1s, in=2002, out=6770)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 19.5s, verify 0.1s, in=1786, out=2031)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.dvd_neg] at H
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/2 ('rw [Int.dvd_neg] at H'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
