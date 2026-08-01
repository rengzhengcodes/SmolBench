# Std.RBSet.ModifyWF.of_eq   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/RBMap/Alter.lean`  

**Ground-truth tail (from k):**
```lean
cases (t.1.zoom cut).1 <;> intro H <;> [trivial; exact H rfl]
```

**True premises at k:** `Std.RBNode.zoom`, `rfl`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=336, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intros h
exact OnRoot.mk (zoom cut t.val).fst h
```

**lean_error:** tail step 2/2 ('exact OnRoot.mk (zoom cut t.val).fst h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=308, out=47)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [OnRoot]
intro h
cases e : root? (zoom cut t.val).fst <;> simp [e]
case some.val x =>
  simp [h (e ▸ rfl)]
  done
done
```

**lean_error:** tail step 3/7 ('cases e : root? (zoom cut t.val).fst <;> simp [e]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=325, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h; apply OnRoot.some; exact h
```

**lean_error:** tail step 1/1 ('intro h; apply OnRoot.some; exact h'): <stdin>:1:7: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=996, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
intros h
exact h rfl
```

**lean_error:** tail step 2/2 ('exact h rfl'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.4s, in=968, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [OnRoot, root?]
intro h
exact h rfl
```

**lean_error:** tail step 3/3 ('exact h rfl'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=985, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply fun h => h (traverse_path _ _)
exact rfl
```

**lean_error:** tail step 1/2 ('apply fun h => h (traverse_path _ _)'): function expected at

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1821, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
intros h
exact h rfl
```

**lean_error:** tail step 2/2 ('exact h rfl'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.4s, in=1797, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [OnRoot, root?, Std.RBNode.zoom]
intro h
exact h rfl
```

**lean_error:** tail step 3/3 ('exact h rfl'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1810, out=71)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply H
exact rfl
```

**lean_error:** tail step 1/2 ('apply H'): unknown identifier 'H'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1846, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
intros h
exact h rfl
```

**lean_error:** tail step 2/2 ('exact h rfl'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=1914, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
intro h
simp [OnRoot, root?, zoom]
split <;> rename_i a y b path
· simp [*]
· simp [*]
· simp [*]
exact h rfl
```

**lean_error:** tail step 3/7 ('split <;> rename_i a y b path'): too many variable names provided

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1835, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply fun h => OnRoot.iff_some.mpr
exact h
```

**lean_error:** tail step 1/2 ('apply fun h => OnRoot.iff_some.mpr'): invalid field notation, type is not of the form (C ...) where C is a constant
