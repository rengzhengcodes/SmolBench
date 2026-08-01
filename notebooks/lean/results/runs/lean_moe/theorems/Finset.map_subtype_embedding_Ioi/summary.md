# Finset.map_subtype_embedding_Ioi   (k=1, 2 tactics total)

file: `Mathlib/Order/LocallyFinite.lean`  

**Ground-truth tail (from k):**
```lean
exact Finset.subtype_map_of_mem fun x hx => hp (mem_Ioi.1 hx).le a.prop
```

**True premises at k:** `Finset.subtype_map_of_mem`, `Finset.mem_Ioi`, `LT.lt.le`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.5s, verify 0.4s, in=361, out=2850)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · intro hx
    rcases Finset.mem_map.1 hx with ⟨y, hy, rfl⟩
    simpa using hy
  · intro hx
    have hpx : p x := hp (le_of_lt hx) a.property
    refine Finset.mem_map.2 ?_
    refine ⟨⟨x, hpx⟩, ?_, rfl⟩
    simpa using hx
```

**lean_error:** tail step 3/10 ('· intro hx'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.9s, verify 2.7s, in=886, out=1640)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
intro x hx
have hx' : (a : α) < x := (Finset.mem_Ioi).1 hx
have hle : (a : α) ≤ x := le_of_lt hx'
exact hp hle a.property
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.6s, verify 0.4s, in=2019, out=1998)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.subtype_map_of_mem
  intro x hx
  have hlt : (a : α) < x := (Finset.mem_Ioi).1 hx
  exact hp (le_of_lt hlt) a.property
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.4s, verify 0.1s, in=1906, out=2543)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [subtype_Ioi_eq] using
  (Finset.subtype_map_of_mem (p:=p) (s:=Ioi (a : α)) (by
    intro x hx
    have hx' : (a : α) < x := (Finset.mem_Ioi).1 hx
    have hax : (a : α) ≤ x := (le_of_lt hx')
    exact hp hax a.property))
```

**lean_error:** tail step 1/6 ('simpa [subtype_Ioi_eq] using'): <stdin>:1:28: unexpected end of input
