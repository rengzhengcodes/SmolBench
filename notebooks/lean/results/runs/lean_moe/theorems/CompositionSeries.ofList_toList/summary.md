# CompositionSeries.ofList_toList   (k=3, 4 tactics total)

file: `Mathlib/Order/JordanHolder.lean`  

**Ground-truth tail (from k):**
```lean
simp [ofList, toList, -List.ofFn_succ]
```

**True premises at k:** `CompositionSeries.ofList`, `CompositionSeries.toList`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | · | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=377, out=882)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [ofList_toList]
```

**lean_error:** tail step 1/1 ('simpa [ofList_toList]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 140.9s, verify 0.1s, in=340, out=17608)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases s with
| cs_s hx_s
cases (ofList (toList s) ⋯ ⋯) with
| cs_L hx_L
have h_cs_L : cs_L = cs_s := by rfl
have h_hx : hx_L = hx_s := by
  apply ProofIrrelevant.proof_irrel
  <;> assumption
have h_eq : ⟨cs_L, hx_L⟩ = ⟨cs_s, hx_s⟩ := by
  exact ⟨h_cs_L, h_hx⟩
have h_len : ⟨cs_L, hx_L⟩.length = ⟨cs_s, hx_s⟩.length := by
  rw [h_eq]
have h_cast : Fin.cast _ (by simp [h_len]) { val := i, isLt := hi } = { val := i, isLt := hi } := by
  simp [h_len]
  <;> rfl
rw [h_eq]
rw [h_cast]
<;> rfl
```

**lean_error:** tail step 1/18 ('cases s with'): <stdin>:1:12: unexpected end of input; expected '|'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.6s, verify 0.7s, in=328, out=543)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ofList_toList]
```

**final state (truncated):**
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=810, out=1087)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [CompositionSeries.ofList, CompositionSeries.toList]
```

**lean_error:** tail step 1/1 ('simpa [CompositionSeries.ofList, CompositionSeries.toList]'): tactic 'assumption' failed

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 163.8s, verify 0.2s, in=776, out=20773)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_length : (toList s).length = s.length + 1 := by simp [toList]
have h_ofList_length : (ofList (toList s) ⋯ ⋯).length = (toList s).length - 1 := rfl
have h_sum : (ofList (toList s) ⋯ ⋯).length + 1 = (toList s).length := by
  have h₁ : 1 ≤ (toList s).length := by
    have h₂ : (toList s).length = s.length + 1 := h_length
    linarith
  omega
have h_i_lt_toList_length : i < (toList s).length := by
  have h₁ : i < (ofList (toList s) ⋯ ⋯).length + 1 := hi
  have h₂ : (ofList (toList s) ⋯ ⋯).length + 1 = (toList s).length := h_sum
  linarith
have h_left : (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = (toList s).nthLe i h_i_lt_toList_length := by
  dsimp [ofList.series]
  <;> simp_all [h_sum, h_ofList_length, h_i_lt_toList_length]
  <;> aesop
have h_mid : (toList s).nthLe i h_i_lt_toList_length = s.series ⟨i, by
  have h₁ : i < s.length + 1 := by
    have h₂ : i < (toList s).length := h_i_lt_toList_length
    have h₃ : (toList s).length = s.length + 1 := h_length
    linarith
  exact h₁
⟩ := by
  have h₁ : toList s = List.ofFn s := rfl
  rw [h₁]
  have h₂ : (List.ofFn s).nthLe i h_i_lt_toList_length = s.series ⟨i, by
    have h₃ : i < s.length + 1 := by
      have h₄ : i < (toList s).length := h_i_lt_toList_length
      have h₅ : (toList s).length = s.length + 1 := h_length
      linarith
    exact h₃
  ⟩ := by
    have h₃ : i < (List.ofFn s).length := by
      simp_all [h₁]
      <;> omega
    have h₄ : (List.ofFn s).nthLe i h_i_lt_toList_length = (List.ofFn s).nthLe i h₃ := by
      apply List.nthLe_congr
      <;> simp_all [h₁]
      <;> omega
    rw [h₄]
    have h₅ : (List.ofFn s).nthLe i h₃ = s.series ⟨i, h₃⟩ := rfl
    rw [h₅]
    have h₆ : ⟨i, h₃⟩ = ⟨i, by
      have h₇ : i < s.length + 1 := by
        have h₈ : i < (toList s).length := h_i_lt_toList_length
        have h₉ : (toList s).length = s.length + 1 := h_length
        linarith
      exact h₇
    ⟩ := by
      apply Fin.ext
      <;> simp_all [h₃]
      <;> omega
    rw [h₆]
have h_right : s.series (Fin.cast _ ⟨i, hi⟩) = s.series ⟨i, by
  have h₁ : i < s.length + 1 := by
    have h₂ : i < (toList s).length := h_i_lt_toList_length
    have h₃ : (toList s).length = s.length + 1 := h_length
    linarith
  exact h₁
⟩ := by
  have h₁ : (ofList (toList s) ⋯ ⋯).length + 1 = s.length + 1 := by
    linarith
  have h₂ : Fin.cast h₁ ⟨i, hi⟩ = ⟨i, by
    have h₃ : i < s.length + 1 := by
      have h₄ : i < (toList s).length := h_i_lt_toList_length
      have h₅ : (toList s).length = s.length + 1 := h_length
      linarith
    exact h₃
  ⟩ := by
    apply Fin.ext
    <;> simp_all [h₁]
    <;> omega
  rw [h₂]
  <;> rfl
calc
  (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = (toList s).nthLe i h_i_lt_toList_length := h_left
  _ = s.series ⟨i, by
    have h₁ : i < s.length + 1 := by
      have h₂ : i < (toList s).length := h_i_lt_toList_length
      have h₃ : (toList s).length = s.length + 1 := h_length
      linarith
    exact h₁
  ⟩ := h_mid
  _ = s.series (Fin.cast _ ⟨i, hi⟩) := by
    rw [h_right]
    <;>
    (try simp_all) <;>
    (try aesop) <;>
    (try
      {
        ext i
        <;> simp_all [Fin.ext_iff]
        <;> omega
      })
```

**lean_error:** tail step 2/93 ('have h_ofList_length : (ofList (toList s) ⋯ ⋯).length = (toList s).length - 1 := rfl'): internal exception #7

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 10.9s, verify 0.1s, in=757, out=1176)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [CompositionSeries.ofList, CompositionSeries.toList, List.nthLe_ofFn]
```

**final state (truncated):**
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=1752, out=1677)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [CompositionSeries.ofList, CompositionSeries.toList] using rfl
```

**lean_error:** tail step 1/1 ('simpa [CompositionSeries.ofList, CompositionSeries.toList] using rfl'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 107.9s, verify 0.1s, in=1723, out=13094)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [show (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = (toList s).nthLe i hi by
  dsimp [CompositionSeries.series, CompositionSeries.ofList]
  <;> rfl
]
rw [show (toList s).nthLe i hi = s ⟨i, hi⟩ by
  rw [List.ofFn]
  have h₁ : i < s.length + 1 := by exact_mod_cast hi
  have h₂ : ⟨i, h₁⟩ : Fin (s.length + 1) := ⟨i, h₁⟩
  rw [List.nthLe_ofFn]
  <;> simp_all [Fin.val_mk, Fin.isLt_mk]
  <;> rfl
]
rw [show s.series (Fin.cast ⋯ { val := i, isLt := hi }) = s ⟨i, hi⟩ by
  dsimp [CompositionSeries.series]
  have h : Fin.cast ⋯ { val := i, isLt := hi } = { val := i, isLt := hi } := by
    apply Fin.ext
    <;> simp_all [Fin.val_mk, Fin.isLt_mk]
    <;> rfl
  rw [h]
  <;> rfl
]
```

**lean_error:** tail step 1/21 ('rw [show (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = (toList s).nthLe i hi by'): <stdin>:1:91: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 11.3s, verify 0.1s, in=1706, out=1216)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [CompositionSeries.ofList, CompositionSeries.toList, List.nthLe_ofFn]
```

**final state (truncated):**
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
...
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 6.7s, verify 0.2s, in=1670, out=1629)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [CompositionSeries.ofList, CompositionSeries.toList, List.nthLe_ofFn]
```

**final state (truncated):**
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
...
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 204.0s, verify 0.2s, in=1896, out=27229)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [toList]
   rw [List.length_ofFn]
   <;> simp [Fintype.card_fin]
   <;>
   (try omega) <;>
   (try
     {
       exact_mod_cast Nat.succ_pos_iff.mpr (by linarith [s.length])
     })
   ```

2. `h_toList_ne_empty`:
   ```lean
   intro h
   rw [h] at h_length
   simp [List.length_nil] at h_length
   <;> omega
   ```

3. `h_ofList_length`:
   ```lean
   dsimp [CompositionSeries.ofList]
   rw [List.length_sub_one]
   <;>
   (try simp_all [List.length])
   <;>
   (try omega)
   ```

4. `h_ofList_length_plus_one`:
   ```lean
   have h₁ : (toList s) ≠ [] := h_toList_ne_empty
   have h₂ : (ofList (toList s)).length = (toList s).length - 1 := h_ofList_length
   have h₃ : (toList s).length ≥ 1 := by
     have h₄ : (toList s).length = s.length + 1 := h_length
     have h₅ : s.length + 1 ≥ 1 := by omega
     omega
   have h₄ : (ofList (toList s)).length + 1 = (toList s).length := by
     omega
   exact h₄
   ```

5. `h_i_lt_toList_length`:
   ```lean
   have h₁ : i < (ofList (toList s)).length + 1 := hi
   have h₂ : (ofList (toList s)).length + 1 = (toList s).length := h_ofList_length_plus_one
   linarith
   ```

6. `h_i_lt_s_length_plus_one`:
   ```lean
   have h₁ : (toList s).length = s.length + 1 := h_length
   linarith
   ```

7. `h_left`: This is the most complicated. We will use the definition of `ofList.series` and then simplify using the fact that the proof in the `nthLe` is irrelevant. We will also use that `(toList s) ≠ []` and `i < (toList s).length`.
   ```lean
   have h₁ : i < (toList s).length := h_i_lt_toList_length
   have h₂ : (toList s) ≠ [] := h_toList_ne_empty
   have h₃ : (ofList (toList s)).series { val := i, isLt := hi } = (toList s).nthLe i := by
     dsimp [CompositionSeries.ofList] at *
     <;>
     (try
       {
         -- We need to show that the proof in the nthLe is valid.
         -- Since we are in Prop, we can use any proof of i < (toList s).length.
         have h₄ : i < (toList s).length := h_i_lt_toList_length
         -- Simplify the expression using the fact that the proof is irrelevant.
         simp_all [List.length, Fin.ext_iff, Nat.lt_succ_iff]
         <;>
         (try omega)
         <;>
         (try
           {
             -- Use the fact that toList s is nonempty to get the length_pos_of_ne_nil proof.
             have h₅ : 0 < (toList s).length := by
               have h₆ : (toList s).length = s.length + 1 := h_length
               have h₇ : s.length + 1 ≥ 1 := by omega
               omega
             -- Use this to simplify the proof in the definition.
             simp_all [List.length_pos_of_ne_nil]
             <;>
             (try omega)
           })
       })
     <;>
     (try
       {
         -- If all else fails, use the fact that the proofs are equal in Prop.
         apply Eq.symm
         apply Eq.symm
         <;>
         (try
           {
             simp_all [List.length, Fin.ext_iff, Nat.lt_succ_iff]
             <;>
             (try omega)
           })
       })
   exact h₃
   ```

8. `h_right`:
   ```lean
   have h₁ : (toList s).length = s.length + 1 := h_length
   have h₂ : (ofList (toList s)).length + 1 = (toList s).length := h_ofList_length_plus_one
   have h₃ : (ofList (toList s)).length + 1 = s.length + 1 := by
     linarith
   have h₄ : Fin.cast _ _ { val := i, isLt := hi } = ⟨i, by
     have h₅ : i < s.length + 1 := h_i_lt_s_length_plus_one
     exact h₅
   ⟩ := by
     apply Fin.ext
     <;> simp_all [Fin.val_mk]
     <;>
     (try
       {
         -- We need to show that the cast is actually the identity.
         -- Since the domain and codomain are the same, the cast is the identity.
         have h₅ : (ofList (toList s)).length + 1 = s.length + 1 := by linarith
         have h₆ : Fin.cast _ _ = fun x => x := by
           ext x
           simp [h₅]
           <;> aesop
         simp [h₆]
       })
     <;>
     (try
       {
         -- Use proof irrelevance for the proof component.
         apply Fin.ext
         <;> simp_all [Fin.val_mk]
         <;>
         (try
           {
             -- The proof components are in Prop, so they are equal.
             exact by
               have h₅ : i < s.length + 1 := h_i_lt_s_length_plus_one
               exact h₅
           })
       })
   rw [h₄]
   <;> rfl
   ```

9. `h_nthLe_eq_series`:
   ```lean
   have h₂ : toList s = List.ofFn s := rfl
   rw [h₂]
   -- Now, we need to show that the i-th element of List.ofFn s.series is s.series i.
   -- This is true by definition of List.ofFn.
   have h₃ : (List.ofFn s.series).nthLe i = s.series i := by
     have h₄ : i < s.length + 1 := h_i_lt_s_length_plus_one
     have h₅ : (List.ofFn s.series).nthLe i = s.series i := by
       apply List.nthLe_ofFn
       <;> simp_all [Fin.ext_iff]
       <;>
       (try omega)
     exact h₅
   rw [h₃]
   ```

10. `h_final`:
    ```lean
    rw [h_left]
    rw [h_right]
    rw [h_nthLe_eq_series]
    <;>
    (try simp_all)
    <;>
    (try omega)
    ```

Finally, `exact h_final`.

However, note that in `h_right`, we are constructing an equality between `Fin.cast _ _ { val := i, isLt := hi }` and `⟨i, by ...⟩`, and then rewriting. This is valid because the `Fin.cast` is actually the identity when the bounds are equal, and we are using proof irrelevance for the proof component.

Given the complexity and the fact that this is a very detailed proof, I will now provide the actual tactic block that we would use after `rintro ⟨i, hi⟩`. Since the problem is to provide the remaining tactics, and we are in a state where we have `i` and `hi`, we will write the tactics as follows.

Note: In practice, we might use `simp_all` and `omega` more aggressively, but for clarity, we will follow the structure above.

However, after checking the actual Mathlib definitions and theorems, there might be a simpler way. For instance, we might use the fact that `toList (ofList l) = l` when `l` is nonempty and a chain, but that is not directly helpful here.

Given the time, I will provide a proof that uses the `have` statements as above, but with the sorries replaced by the tactics described. Since the output should be only the tactic lines, I will write them in sequence.

But note: the problem says "Output only the tactic lines, nothing else." and we are to produce the remaining tactics.

Therefore, the final answer is the following sequence of tactics (to be applied after `rintro ⟨i, hi⟩`):
```

**lean_error:** tail step 2/171 ('rw [List.length_ofFn]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.2s, in=1711, out=512)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CompositionSeries.ofList, CompositionSeries.toList, List.ofFn, List.nthLe]
 rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch
