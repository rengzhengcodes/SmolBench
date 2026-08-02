# CategoryTheory.Limits.biproduct.lift_desc   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc, comp_dite,
  dite_comp]
```

**True premises at k:** `CategoryTheory.Limits.biproduct.lift_eq`, `CategoryTheory.Limits.biproduct.desc_eq`, `CategoryTheory.Preadditive.comp_sum`, `CategoryTheory.Preadditive.sum_comp`, `CategoryTheory.Limits.biproduct.ι_π_assoc`, `CategoryTheory.comp_dite`, `CategoryTheory.dite_comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=363, out=403)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using Biproduct.lift_desc (g:=g) (h:=h)
```

**lean_error:** tail step 1/1 ('simpa using Biproduct.lift_desc (g:=g) (h:=h)'): unknown identifier 'Biproduct.lift_desc'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 156.8s, verify 0.1s, in=309, out=18732)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  lift g ≫ desc h = desc h ∘ lift g := by rw [show lift g ≫ desc h = desc h ∘ lift g by rw [Function.comp_def]]
  _ = desc h ∘ (∑ j : J, Sigma j ∘ Pi j) ∘ lift g := by rw [HasBiproduct.sum_sigma_pi]
  _ = (desc h ∘ (∑ j : J, Sigma j ∘ Pi j)) ∘ lift g := rfl
  _ = (∑ j : J, desc h ∘ (Sigma j ∘ Pi j)) ∘ lift g := by rw [comp_sum]
  _ = ∑ j : J, (desc h ∘ (Sigma j ∘ Pi j)) ∘ lift g := by rw [sum_comp]
  _ = ∑ j : J, (desc h ∘ Sigma j) ∘ (Pi j ∘ lift g) := by
    apply Finset.sum_congr rfl
    intro j _
    have h1 : (desc h ∘ (Sigma j ∘ Pi j)) ∘ lift g = (desc h ∘ Sigma j) ∘ (Pi j ∘ lift g) := by
      calc
        (desc h ∘ (Sigma j ∘ Pi j)) ∘ lift g = desc h ∘ ((Sigma j ∘ Pi j) ∘ lift g) := by rw [comp_assoc]
        _ = desc h ∘ (Sigma j ∘ (Pi j ∘ lift g)) := by rw [comp_assoc]
        _ = (desc h ∘ Sigma j) ∘ (Pi j ∘ lift g) := by rw [comp_assoc]
    rw [h1]
  _ = ∑ j : J, h j ∘ (Pi j ∘ lift g) := by
    apply Finset.sum_congr rfl
    intro j _
    have h2 : desc h ∘ Sigma j = h j := by apply HasBiproduct.desc_sigma
    rw [h2]
    <;> simp [comp_assoc]
  _ = ∑ j : J, (h j ∘ Pi j) ∘ lift g := by
    apply Finset.sum_congr rfl
    intro j _
    rw [comp_assoc]
  _ = ∑ j : J, h j ∘ (g j) := by
    apply Finset.sum_congr rfl
    intro j _
    have h3 : Pi j ∘ lift g = g j := by apply HasBiproduct.lift_pi
    rw [h3]
    <;> simp [comp_assoc]
  _ = ∑ j : J, g j ≫ h j := by
    apply Finset.sum_congr rfl
    intro j _
    have h4 : h j ∘ g j = g j ≫ h j := by
      rw [show h j ∘ g j = g j ≫ h j by
        rw [Function.comp_def]
        <;> rfl]
    rw [h4]
    <;> simp [comp_assoc]
```

**lean_error:** tail step 1/40 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=306, out=512)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext j
simp [biproduct.π_comp_lift, biproduct.desc_comp_ι, Finset.sum_ite_eq']
```

**lean_error:** tail step 1/2 ('ext j'): no applicable extensionality theorem found for

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 1.6s, in=1915, out=804)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum,
    biproduct.ι_π, Category.assoc, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl]
```

**lean_error:** tail step 1/2 ('simp [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum,'): <stdin>:1:63: unexpected end of input; expected ']'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 173.7s, verify 0.2s, in=1869, out=20800)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
have h₁ : (∑ j : J, π f j ≫ h j) = (∑ k : J, π f k ≫ h k) := by
  apply Finset.sum_bij' (fun (k : J) _ => k) (fun (j : J) _ => j)
  <;> simp_all [Finset.mem_univ]
  <;> aesop
rw [h₁]
rw [comp_sum]
apply Finset.sum_congr rfl
intro k _
rw [sum_comp]
<;> simp [Finset.sum_const, nsmul_eq_mul]
<;> rfl
rw [Finset.sum_comm]
apply Finset.sum_congr rfl
intro j _
apply Finset.sum_congr rfl
intro k _
calc
  (g j ≫ ι f j) ≫ (π f k ≫ h k) = g j ≫ (ι f j ≫ (π f k ≫ h k)) := by rw [← Category.assoc]
  _ = g j ≫ ((ι f j ≫ π f k) ≫ h k) := by rw [Category.assoc]
  _ = g j ≫ (ι f j ≫ π f k) ≫ h k := by rw [Category.assoc]
have h₂ : ∀ (j k : J), ι f j ≫ π f k = if j = k then (1 : T ⟶ T) else 0 := by
  intro j k
  have h₃ : ι f j ≫ π f k = if j = k then (1 : T ⟶ T) else 0 := by
    rw [← biproduct.ι_π]
    <;> simp [h₃]
    <;> aesop
  exact h₃
apply Finset.sum_congr rfl
intro j _
apply Finset.sum_congr rfl
intro k _
rw [h₂ j k]
apply Finset.sum_congr rfl
intro j _
have h₃ : ∑ k : J, g j ≫ (if j = k then (1 : T ⟶ T) else (0 : T ⟶ T)) ≫ h k = g j ≫ (∑ k : J, (if j = k then (1 : T ⟶ T) else (0 : T ⟶ T)) ≫ h k) := by
  rw [← comp_sum]
  <;> simp [Finset.sum_const, nsmul_eq_mul]
  <;> rfl
rw [h₃]
apply Finset.sum_congr rfl
intro k _
split_ifs <;>
  (try { simp [Category.comp_one] }) <;>
  (try { simp [Category.zero_comp] })
apply Finset.sum_congr rfl
intro j _
have h₄ : (∑ k : J, if j = k then h k else 0) = h j := by
  have h₅ : (∑ k : J, if j = k then h k else 0) = if j ∈ (Finset.univ : Finset J) then h j else 0 := by
    apply Finset.sum_ite_eq'
    <;> simp_all [Finset.mem_univ]
    <;> aesop
  rw [h₅]
  have h₆ : (j : J) ∈ (Finset.univ : Finset J) := by
    apply Finset.mem_univ
  rw [h₆]
  <;> simp
rw [h₄]
```

**lean_error:** tail step 2/58 ('have h₁ : (∑ j : J, π f j ≫ h j) = (∑ k : J, π f k ≫ h k) := by'): <stdin>:1:63: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.4s, in=1842, out=901)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp]
rw [comp_sum]
simp [biproduct.ι_π_assoc]
```

**lean_error:** tail step 3/4 ('rw [comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=2670, out=1582)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum, Category.assoc,
  biproduct.ι_π, biproduct.ι_π_assoc, Finset.sum_dite_eq', Finset.mem_univ]
```

**lean_error:** tail step 1/2 ('simpa [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum, Category.assoc,'): <stdin>:1:80: unexpected end of input; expected '*' or '-'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 191.4s, verify 0.4s, in=2639, out=23090)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : lift g = ∑ j : J, g j ≫ biproduct.ι f j := by rw [biproduct.lift_eq]
have h2 : desc h = ∑ j : J, biproduct.π f j ≫ h j := by rw [biproduct.desc_eq]
have h3 : lift g ≫ desc h = (∑ j : J, g j ≫ biproduct.ι f j) ≫ (∑ j : J, biproduct.π f j ≫ h j) := by rw [h1, h2]
have h4 : lift g ≫ desc h = ∑ i : J, (g i ≫ biproduct.ι f i) ≫ (∑ j : J, biproduct.π f j ≫ h j) := by
  rw [h3]
  rw [sum_comp]
have h5 : lift g ≫ desc h = ∑ i : J, ∑ j : J, (g i ≫ biproduct.ι f i) ≫ (biproduct.π f j ≫ h j) := by
  rw [h4]
  apply Finset.sum_congr rfl
  intro i _
  rw [comp_sum]
have h6 : lift g ≫ desc h = ∑ i : J, ∑ j : J, g i ≫ (biproduct.ι f i ≫ biproduct.π f j) ≫ h j := by
  rw [h5]
  apply Finset.sum_congr rfl
  intro i _
  apply Finset.sum_congr rfl
  intro j _
  -- Use associativity: (f ≫ g) ≫ h = f ≫ (g ≫ h)
  rw [← Category.assoc]
have h7 : lift g ≫ desc h = ∑ i : J, ∑ j : J, g i ≫ (if i = j then 𝟙 (f i) else 0) ≫ h j := by
  rw [h6]
  apply Finset.sum_congr rfl
  intro i _
  apply Finset.sum_congr rfl
  intro j _
  -- Use biproduct.ι_π_assoc to get ι f i ≫ π f j = if i = j then 𝟙 (f i) else 0
  have h7₁ : biproduct.ι f i ≫ biproduct.π f j = if i = j then 𝟙 (f i) else 0 := by
    have h7₂ : biproduct.π f j ∘ biproduct.ι f i = if j = i then 𝟙 (f j) else 0 := by
      have h7₃ : biproduct.π f j ∘ biproduct.ι f i = if j = i then 𝟙 (f j) else 0 := by
        apply biproduct.ι_π_assoc
      exact h7₃
    -- Now, biproduct.ι f i ≫ biproduct.π f j = biproduct.π f j ∘ biproduct.ι f i
    have h7₄ : biproduct.ι f i ≫ biproduct.π f j = biproduct.π f j ∘ biproduct.ι f i := by
      simp [CategoryExt.iff, Function.comp_apply]
      <;> rfl
    rw [h7₄]
    -- Now, we have: if j = i then 𝟙 (f j) else 0
    -- We want: if i = j then 𝟙 (f i) else 0
    split_ifs <;> simp_all [eq_comm]
    <;> try { aesop }
    <;> try {
      ext x
      simp_all
    }
  rw [h7₁]
have h8 : lift g ≫ desc h = ∑ i : J, g i ≫ (∑ j : J, (if i = j then 𝟙 (f i) else 0) ≫ h j) := by
  rw [h7]
  -- Use sum_comp to pull out g i from the inner sum over j
  apply Finset.sum_congr rfl
  intro i _
  rw [sum_comp]
have h9 : lift g ≫ desc h = ∑ i : J, g i ≫ h i := by
  rw [h8]
  apply Finset.sum_congr rfl
  intro i _
  -- Now, we need to show that (∑ j : J, (if i = j then 𝟙 (f i) else 0) ≫ h j) = h i
  have h9₁ : (∑ j : J, (if i = j then 𝟙 (f i) else 0) ≫ h j) = h i := by
    calc
      (∑ j : J, (if i = j then 𝟙 (f i) else 0) ≫ h j) = ∑ j : J, if i = j then (𝟙 (f i) ≫ h j) else 0 := by
        apply Finset.sum_congr rfl
        intro j _
        split_ifs <;> simp [*, CategoryExt.iff, Function.comp_apply]
        <;> try { aesop }
        <;> try {
          ext x
          simp_all
        }
      _ = ∑ j : J, if i = j then h j else 0 := by
        apply Finset.sum_congr rfl
        intro j _
        split_ifs <;> simp [*, CategoryExt.iff, Function.comp_apply]
        <;> try { aesop }
        <;> try {
          ext x
          simp_all
        }
      _ = h i := by
        -- Now, we need to show that the sum of the indicator function times h j is h i.
        have h9₂ : (∑ j : J, if i = j then h j else 0) = h i := by
          calc
            _ = ∑ j : J, if j = i then h j else 0 := by
              apply Finset.sum_congr rfl
              intro j _
              split_ifs <;> simp_all [eq_comm]
              <;> try { aesop }
            _ = h i := by
              -- The sum over j of the indicator function is the value at i.
              have h9₃ : (∑ j : J, if j = i then h j else 0) = h i := by
                classical
                -- Use the filter method
                have h9₄ : ∑ j : J, if j = i then h j else 0 = ∑ j in ({i} : Finset J), h i := by
                  apply Finset.sum_subset
                  · intro j hj
                    split_ifs <;> simp_all [hj]
                    <;> aesop
                  · intro j _
                    simp
                rw [h9₄]
                simp [Finset.sum_singleton]
              exact h9₃
        exact h9₂
  rw [h9₁]
rwh [h9]
```

**lean_error:** tail step 4/103 ('have h4 : lift g ≫ desc h = ∑ i : J, (g i ≫ biproduct.ι f i) ≫ (∑ j : J, biproduct.π f j ≫ h j) := by'): <stdin>:1:101: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.3s, in=2610, out=769)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp only [sum_comp, comp_sum]
ext j
simp [biproduct.ι_π_assoc]
```

**lean_error:** tail step 3/4 ('ext j'): no applicable extensionality theorem found for

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.4s, in=2610, out=1095)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum,
    Category.assoc, biproduct.ι_π, Finset.sum_dite_eq', Finset.mem_univ]
```

**lean_error:** tail step 1/2 ('simpa [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum,'): <stdin>:1:64: unexpected end of input; expected '*' or '-'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 180.9s, verify 0.4s, in=2775, out=21656)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : biproduct.lift g = ∑ j : J, g j ≫ biproduct.ι f j := by rw [biproduct.lift_eq]
have h2 : biproduct.desc h = ∑ j : J, biproduct.π f j ≫ h j := by rw [biproduct.desc_eq]
rw [h1, h2]
calc
  (∑ j : J, g j ≫ biproduct.ι f j) ≫ (∑ k : J, biproduct.π f k ≫ h k) = ∑ j : J, (g j ≫ biproduct.ι f j) ≫ (∑ k : J, biproduct.π f k ≫ h k) := by
    rw [sum_comp]
  _ = ∑ j : J, ∑ k : J, (g j ≫ biproduct.ι f j) ≫ (biproduct.π f k ≫ h k) := by
    apply Finset.sum_congr rfl
    intro j _
    rw [comp_sum]
  _ = ∑ j : J, ∑ k : J, (if j = k then g j ≫ h k else 0) := by
    apply Finset.sum_congr rfl
    intro j _
    apply Finset.sum_congr rfl
    intro k _
    have h3 : (g j ≫ biproduct.ι f j) ≫ (biproduct.π f k ≫ h k) = if j = k then g j ≫ h k else 0 := by
      have h4 : (g j ≫ biproduct.ι f j) ≫ (biproduct.π f k ≫ h k) = g j ≫ (biproduct.ι f j ≫ (biproduct.π f k ≫ h k)) := by
        rw [← Category.assoc]
      rw [h4]
      have h5 : g j ≫ (biproduct.ι f j ≫ (biproduct.π f k ≫ h k)) = g j ≫ ((biproduct.ι f j ≫ biproduct.π f k) ≫ h k) := by
        rw [← Category.assoc]
      rw [h5]
      have h6 : (biproduct.ι f j ≫ biproduct.π f k) = if j = k then (1 : f j ⟶ f j) else 0 := by
        apply biproduct.ι_π_assoc
      rw [h6]
      have h7 : g j ≫ ((if j = k then (1 : f j ⟶ f j) else 0) ≫ h k) = if j = k then g j ≫ h k else 0 := by
        split_ifs <;> simp_all [comp_one, comp_zero]
        <;>
        (try { contradiction }) <;>
        (try { aesop })
      rw [h7]
    rw [h3]
  _ = ∑ j : J, g j ≫ h j := by
    apply Finset.sum_congr rfl
    intro j _
    have h8 : (∑ k : J, if j = k then g j ≫ h k else 0) = g j ≫ h j := by
      classical
      have h9 : (∑ k : J, if j = k then g j ≫ h k else 0) = ∑ k in (Finset.filter (fun k : J => j = k) (Finset.univ : Finset J)), g j ≫ h k := by
        rw [Finset.sum_ite_eq']
        <;> simp [Finset.filter_eq']
        <;>
        (try { aesop })
      rw [h9]
      have h10 : (Finset.filter (fun k : J => j = k) (Finset.univ : Finset J)) = ({j} : Finset J) := by
        ext x
        simp [Finset.mem_filter, Finset.mem_univ, Finset.mem_singleton]
        <;>
        (try { constructor <;> intro h <;> (try { tauto }) <;> (try { aesop }) })
      rw [h10]
      have h11 : ∑ k in ({j} : Finset J), g j ≫ h k = g j ≫ h j := by
        simp [Finset.sum_singleton]
      rw [h11]
    rw [h8]
```

**lean_error:** tail step 4/53 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 8.9s, verify 0.5s, in=2615, out=845)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp only [sum_comp, comp_sum]
rw [Finset.sum_comm]
simp [biproduct.ι_π_assoc]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```
