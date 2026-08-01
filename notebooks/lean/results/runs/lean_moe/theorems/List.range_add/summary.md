# List.range_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [range_eq_range', Nat.add_comm] using (range'_append_1 0 a b).symm
```

**True premises at k:** `List.range_eq_range'`, `Nat.add_comm`, `List.range'_append_1`, `Eq.symm`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=265, out=900)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using List.range_add_eq_append_range' a b
```

**lean_error:** tail step 1/1 ("simpa using List.range_add_eq_append_range' a b"): unknown constant 'List.range_add_eq_append_range''

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.0s, verify 0.2s, in=1117, out=1805)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range']
rw [range'_append_1]
rw [Nat.add_comm]
rfl
```

**lean_error:** tail step 2/4 ("rw [range'_append_1]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.2s, verify 0.6s, in=4228, out=2269)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.range_eq_range' (a + b)]
rw [List.range_eq_range' a]
rw [Nat.add_comm a b] at *
symm
exact List.range'_append_1 0 a b
```

**lean_error:** tail step 4/5 ('symm'): no applicable symmetry lemma found for 

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.1s, verify 0.1s, in=3899, out=1802)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [range_eq_range']
simpa [Nat.add_comm] using (range'_append_1 0 a b).symm
```
