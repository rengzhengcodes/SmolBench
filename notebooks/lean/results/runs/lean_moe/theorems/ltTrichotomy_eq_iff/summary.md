# ltTrichotomy_eq_iff   (k=3, 4 tactics total)

file: `Mathlib/Order/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, false_or, h, h.not_lt, h.ne']
```

**True premises at k:** `ltTrichotomy_gt`, `false_and`, `true_and`, `false_or`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | · |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.4s, verify 1.3s, in=394, out=1736)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hx : ¬ x < y := by
    intro hx
    exact lt_asymm hx h
  have hxy : x ≠ y := by
    intro h_eq
    have : y < y := by simpa [h_eq] using h
    exact lt_irrefl _ this
  simp [ltTrichotomy, hx, hxy, h]
```

**lean_error:** tail step 1/8 ('have hx : ¬ x < y := by'): <stdin>:1:23: unexpected end of input; expected '{'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 8.2s, verify 0.1s, in=996, out=1454)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt h, false_and, true_and, false_or, or_false, h, h.not_lt, h.ne]
```

**final state (truncated):**
```
case refine_3
ι : Type u_1
α : Type u
β : Type v
γ : Type w
π : ι → Type u_2
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.8s, verify 0.2s, in=1766, out=1130)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [ltTrichotomy_gt, false_and, true_and, or_false, false_or, h, h.not_lt, h.ne]
simp
```

**lean_error:** tail step 2/2 ('simp'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 3.4s, in=1685, out=1628)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [ltTrichotomy_gt h]
```

**lean_error:** tail step 1/1 ('simpa [ltTrichotomy_gt h]'): tactic 'assumption' failed
