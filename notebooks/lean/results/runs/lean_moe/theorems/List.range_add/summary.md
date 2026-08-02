# List.range_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [range_eq_range', Nat.add_comm] using (range'_append_1 0 a b).symm
```

**True premises at k:** `List.range_eq_range'`, `Nat.add_comm`, `List.range'_append_1`, `Eq.symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=265, out=900)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using List.range_add_eq_append_range' a b
```

**lean_error:** tail step 1/1 ("simpa using List.range_add_eq_append_range' a b"): unknown constant 'List.range_add_eq_append_range''

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 16.7s, verify 0.1s, in=209, out=2028)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.range_add, List.range']
```

**final state (truncated):**
```
a b : Nat
⊢ map (fun x => a + x) (range b) = range' a b
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.1s, in=210, out=781)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction b with
| zero => simp
| succ b ih => simp_all [Nat.add_succ, List.range_succ', List.append_assoc]
```

**lean_error:** tail step 1/3 ('induction b with'): <stdin>:1:16: unexpected end of input; expected '|'

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

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.6s, verify 0.2s, in=1082, out=11270)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.range_eq_range']
rw [List.range'_append_1]
rw [Eq.symm]
rw [Nat.add_comm]
```

**lean_error:** tail step 2/4 ("rw [List.range'_append_1]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 113.4s, verify 0.3s, in=1072, out=12112)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range']
rw [Nat.add_comm]
rw [← range'_append_1 0 a b]
simp
```

**final state (truncated):**
```
a b : Nat
⊢ range' 0 a = range a
```

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

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 102.2s, verify 0.2s, in=4239, out=13683)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [List.range_eq_range']
rw [List.range_eq_range']
have h : map (fun x => a + x) (range b) = range' a b := by
  rw [Eq.symm range'_eq_map_range]
rw [h]
have h₂ : range' 0 a ++ range' a b = range' 0 (a + b) := by
  simp_all [List.range'_append_1, add_zero, add_comm]
  <;> rfl
rw [Eq.symm h₂]
```

**lean_error:** tail step 3/9 ("have h : map (fun x => a + x) (range b) = range' a b := by"): <stdin>:1:58: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 7.1s, verify 0.2s, in=4220, out=617)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [range_eq_range', range_eq_range']
rw [← range'_append_1, Nat.add_comm]
simp
```

**final state (truncated):**
```
a b : Nat
⊢ range' 0 b ++ range' b a = range' 0 a ++ range' a b
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.1s, verify 0.1s, in=3899, out=1802)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [range_eq_range']
simpa [Nat.add_comm] using (range'_append_1 0 a b).symm
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 51.9s, verify 0.1s, in=4721, out=6922)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem List.range_add {a b : Nat} : range (a + b) = range a ++ range' a b := by
  rw [← range'_eq_map_range]
  have h : range (a + b) = range' 0 (a + b) := by
    rw [List.range_eq_range']
    <;>
    simp [add_zero]
  
  have h' : range a ++ map (fun x => x + a) (range b) = range' 0 (a + b) := by
    have h2 : range a = range' 0 a := by
      rw [List.range_eq_range']
    have h3 : map (fun x => x + a) (range b) = range' a b := by
      rw [range'_eq_map_range]
    calc
      range a ++ map (fun x => x + a) (range b) = range' 0 a ++ range' a b := by rw [h2, h3]
      _ = range' 0 a ++ range' (0 + a) b := by
        have h4 : range' a b = range' (0 + a) b := by
          simp [add_zero]
        rw [h4]
      _ = range' 0 (b + a) := by
        rw [range'_append_1]
      _ = range' 0 (a + b) := by
        have h5 : b + a = a + b := by
          rw [add_comm]
        rw [h5]
        <;>
        simp [add_assoc]
  
  have h'' : range (a + b) = range a ++ map (fun x => x + a) (range b) := by
    calc
      range (a + b) = range' 0 (a + b) := h
      _ = range a ++ map (fun x => x + a) (range b) := by
        rw [h'.symm]
        <;>
        simp [add_assoc]
  
  exact h''
```

**lean_error:** tail step 1/33 ("theorem List.range_add {a b : Nat} : range (a + b) = range a ++ range' a b := by"): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 303.1s, verify 0.0s, in=4169, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail
