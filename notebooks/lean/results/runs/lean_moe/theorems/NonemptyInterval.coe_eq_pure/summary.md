# NonemptyInterval.coe_eq_pure   (k=0, 1 tactics total)

file: `Mathlib/Order/Interval.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Interval.coe_inj, coe_pure_interval]
```

**True premises at k:** `Interval.coe_inj`, `NonemptyInterval.coe_pure_interval`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.6s, verify 0.2s, in=322, out=3262)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  cases s
  ext
  simpa using h
· intro h
  simpa [h]
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=661, out=1073)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.2s, verify 0.1s, in=2332, out=1184)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.9s, verify 0.1s, in=2180, out=1118)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [NonemptyInterval.coe_pure_interval] using (Interval.coe_inj (s:=s) (t:=pure a))
```
