# String.contains_iff   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [contains, any_iff]
```

**True premises at k:** `String.contains`, `String.any_iff`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=264, out=906)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [String.contains]
```

**lean_error:** tail step 1/1 ('simpa [String.contains]'): tactic 'assumption' failed

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.6s, verify 0.2s, in=558, out=4252)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h
    have h' : any s (fun a => a == c) = true := by
      simpa [String.contains] using h
    rcases (String.any_iff s (fun a => a == c)).1 h' with ⟨a, ha, hac⟩
    have : a = c := by
      have : (a == c) = true := by
        simpa using hac
      simpa [decide_eq_true] using this
    simpa [this] using ha
  · intro hc
    have h' : any s (fun a => a == c) = true := by
      apply (String.any_iff s (fun a => a == c)).2
      exact ⟨c, hc, by simp⟩
    simpa [String.contains] using h'
```

**lean_error:** tail step 2/15 ('· intro h'): unsolved goals

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.2s, verify 0.1s, in=1167, out=2001)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [String.contains] using (String.any_iff s (fun a => a == c))
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.6s, verify 0.1s, in=1122, out=2354)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [String.contains] using (String.any_iff s (fun a => a == c))
```
