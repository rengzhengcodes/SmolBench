# List.set_eq_take_cons_drop   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop _ h]
```

**True premises at k:** `List.set_eq_modifyNth`, `List.modifyNth_eq_take_cons_drop`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.7s, in=297, out=306)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [List.set, h]
```

**lean_error:** tail step 1/1 ('simp [List.set, h]'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 97.9s, verify 0.2s, in=241, out=14851)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply List.ext
intro i
have h_len_take : length (take n l) = n := by
  apply take_len_of_le
  <;> omega
have h_set : (set l n a) !! i = if i = n then some a else l !! i := by
  rw [List.set_nth]
split_ifs at h_set ⊢ <;>
  (try { contradiction }) <;>
  (try {
    have h₃ : i < n ∨ i = n ∨ n < i := by omega
    rcases h₃ with (h₃ | h₃ | h₃)
    <;>
    (try {
      simp_all [List.get?_append, List.get?_cons, List.get?_take_of_lt, List.get?_drop_add,
                List.get?_cons_of_pos, Nat.sub_add_cancel, Nat.add_sub_cancel,
                Nat.sub_eq_zero_iff_le, Nat.lt_succ_iff, Nat.le_of_lt_succ]
      <;>
      (try { omega }) <;>
      (try { aesop })
    })
  })
```

**lean_error:** tail step 3/22 ('have h_len_take : length (take n l) = n := by'): <stdin>:1:45: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 12.2s, verify 0.1s, in=242, out=1314)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction n generalizing l with
| zero =>
    cases l with
    | nil => contradiction
    | cons b l' => simp [List.set, List.take, List.drop]
| succ n ih =>
    cases l with
    | nil => contradiction
    | cons b l' =>
      simp_all [List.set, List.take, List.drop, List.length]
      <;> simp_all [List.cons_append]
```

**lean_error:** tail step 1/11 ('induction n generalizing l with'): <stdin>:1:31: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.0s, verify 0.1s, in=758, out=865)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [set_eq_modifyNth a] using (modifyNth_eq_take_cons_drop (fun _ => a) (n:=n) (l:=l) h)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 38.0s, verify 0.2s, in=726, out=5241)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [set_eq_modifyNth]
rw [modifyNth_eq_take_cons_drop h]
<;> rw [show (fun _ => a) (get l ⟨n, h⟩) = a by rfl]
<;> rfl
```

**lean_error:** tail step 2/4 ('rw [modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.5s, verify 0.1s, in=709, out=420)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [set_eq_modifyNth a n l]
rw [modifyNth_eq_take_cons_drop (fun _ => a) h]
simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.8s, verify 0.2s, in=1555, out=777)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth (a:=a) (n:=n) (l:=l)]
  simpa using (modifyNth_eq_take_cons_drop (f:=fun _ => a) (n:=n) (l:=l) h)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 30.3s, verify 0.1s, in=1532, out=4113)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop (fun _ => a) h]
<;> simp
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1501, out=618)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth a n l]
rw [modifyNth_eq_take_cons_drop (fun _ => a) h]
simp
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=1479, out=1011)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [modifyNth_eq_take_cons_drop (f:=fun _ => a) h] using (set_eq_modifyNth (a:=a) n l)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.2s, in=1666, out=1654)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth]
rw [modifyNth_eq_take_cons_drop h]
<;> dsimp
```

**lean_error:** tail step 2/3 ('rw [modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 48.8s, verify 0.2s, in=1512, out=5261)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [List.set_eq_modifyNth]
rw [List.modifyNth_eq_take_cons_drop h]
simp
```

**lean_error:** tail step 2/3 ('rw [List.modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
