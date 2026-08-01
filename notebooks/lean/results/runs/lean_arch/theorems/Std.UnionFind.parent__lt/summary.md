# Std.UnionFind.parent'_lt   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/UnionFind/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← parentD_eq, parentD_lt, Fin.is_lt, Array.data_length]
```

**True premises at k:** `Std.UnionFind.parentD_eq`, `Std.UnionFind.parentD_lt`, `Fin.is_lt`, `Array.data_length`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.5s, in=228, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hlt := size_pos self
have hge := Array.get self.arr i
have hgt := lt_of_lt_of_le hge.parent hlt
exact hgt
```

**lean_error:** tail step 1/4 ('have hlt := size_pos self'): internal exception #7

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=202, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [size, Array.size_toArray]
exact (Array.get self.arr i).parent.2.isLt
```

**lean_error:** tail step 1/2 ('rw [size, Array.size_toArray]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=217, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold UnionFind.size
rw [Array.get]
unfold Fin.val
apply fin.is_lt
```

**lean_error:** tail step 3/4 ('unfold Fin.val'): tactic 'unfold' failed to unfold 'Fin.val' at

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=672, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [parentD_eq]
rw [←data_length]
exact parentD_lt _ i.1 i.2
```

**lean_error:** tail step 1/3 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=640, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Std.UnionFind.parentD_eq]
exact Std.UnionFind.parentD_lt self.arr i
```
```

**lean_error:** tail step 2/3 ('exact Std.UnionFind.parentD_lt self.arr i'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=661, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [parentD_eq]
exact Array.get_lt self.arr i
```

**lean_error:** tail step 1/2 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1860, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [parentD_eq]
exact i.2
```

**lean_error:** tail step 1/2 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1845, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Std.UnionFind.parentD_eq]
exact Std.UnionFind.parentD_lt self.arr i.val i.isLt
```

**lean_error:** tail step 2/2 ('exact Std.UnionFind.parentD_lt self.arr i.val i.isLt'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1849, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [parentD_eq]
cases' self.arr.get i with _ h
exact h
```

**lean_error:** tail step 1/3 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1885, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [parentD_eq]
rw [Array.data_length]
exact Fin.is_lt _
```

**lean_error:** tail step 1/3 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.5s, in=1989, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
conv =>
  lhs
  rw [← parentD_eq]
  rw [parentD_lt]
exact Fin.is_lt i
```

**lean_error:** tail step 1/5 ('conv =>'): <stdin>:1:7: unexpected end of input; expected '{'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1874, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [parentD_eq]
exact (i.is_lt)
```

**lean_error:** tail step 1/2 ('rw [parentD_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
