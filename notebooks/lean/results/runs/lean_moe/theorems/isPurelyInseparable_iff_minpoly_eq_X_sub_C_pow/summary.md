# isPurelyInseparable_iff_minpoly_eq_X_sub_C_pow   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/PurelyInseparable.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [isPurelyInseparable_iff_natSepDegree_eq_one,
  minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow q]
```

**True premises at k:** `isPurelyInseparable_iff_natSepDegree_eq_one`, `minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=396, out=542)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using isPurelyInseparable_iff (F:=F) (E:=E) (q:=q)
```

**lean_error:** tail step 1/1 ('simpa using isPurelyInseparable_iff (F:=F) (E:=E) (q:=q)'): invalid argument name 'q' for function 'isPurelyInseparable_iff'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 254.7s, verify 0.2s, in=345, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · -- Prove the forward direction: IsPurelyInseparable F E ⇒ (∀ x : E, ∃ n, ...)
    intro h
    by_cases hq1 : q = 1
    · -- Case q = 1: characteristic 0
      have hChar0 : CharP F 0 := by
        by_contra h
        -- If CharP F p for some p > 0, then ExpChar F p holds, so q = p by uniqueness of ExpChar, contradicting q = 1.
        have h₂ : ∃ p : ℕ, Fact (CharP F p) := by
          -- Since F is a field, its characteristic is either 0 or a prime.
          have h₃ : CharP F 0 ∨ ∃ p : ℕ, Fact (CharP F p) := by
            by_cases h₄ : CharP F 0
            · exact Or.inl h₄
            · obtain ⟨p, hp⟩ := (CharP F).eq_zero_or_prime
              exact Or.inr ⟨p, hp⟩
          cases h₃ with
          | inl h₄ =>
            exfalso
            exact h h₄
          | inr ⟨p, hp⟩ =>
            exact ⟨p, hp⟩
        obtain ⟨p, hp⟩ := h₂
        have h₃ : p ≠ 0 := by
          by_contra h₄
          have h₅ : p = 0 := by simpa using h₄
          have h₆ : Fact (CharP F 0) := by
            simpa [h₅] using hp
          have h₇ : CharP F 0 := h₆
          exact h h₇
        have h₄ : ExpChar F p := by
          -- Since CharP F p, we have ExpChar F p.
          have h₅ : ExpChar F p := by
            apply Fact.expChar
          exact h₅
        have h₅ : q = p := by
          -- By uniqueness of ExpChar, if ExpChar F q and ExpChar F p, then q = p.
          have h₆ : ExpChar F q := hF
          have h₇ : ExpChar F p := h₄
          have h₈ : q = p := by
            apply ExpChar.unique
            · exact h₆
            · exact h₇
          exact h₈
        have h₆ : q ≠ 1 := by
          intro h₆
          have h₇ : p = 1 := by linarith
          have h₈ : p = 0 := by
            have h₉ : p.Prime := by
              -- The characteristic of a field is prime if not zero.
              have h₁₀ : Fact (CharP F p) := hp
              exact Fact.ne_zero.mp (by
                intro h₁₁
                have h₁₂ : p = 0 := by simpa using h₁₁
                have h₁₃ : CharP F 0 := by
                  simpa [h₁₂] using hp
                exact h h₁₃
              )
              -- In a field, if the characteristic is not zero, it is prime.
              have h₁₄ : p.Prime := by
                apply Nat.Prime.ne_zero
                exact h₁₀
                <;>
                (try decide) <;>
                (try {
                  have h₁₅ := CharP F.eq_zero_or_prime
                  cases h₁₅ with
                  | inl h₁₅ =>
                    exfalso
                    simp_all [CharP.F]
                  | inr ⟨p', hp'⟩ =>
                    have h₁₆ : p' = p := by
                      simp_all [Fact.CharP]
                    <;>
                    aesop
                  }) <;>
                  (try {
                    have h₁₅ := CharP F.eq_zero_or_prime
                    cases h₁₅ with
                    | inl h₁₅ =>
                      exfalso
                      simp_all [CharP.F]
                    | inr ⟨p', hp'⟩ =>
                      have h₁₆ : p' = p := by
                        simp_all [Fact.CharP]
                      <;>
                      aesop
                  })
              exact h₁₄
            have h₁₀ : p = 1 := by linarith
            have h₁₁ : p.Prime := h₉
            rw [h₁₀] at h₁₁
            norm_num at h₁₁
          simp_all [CharP.F]
        have h₇ : q ≠ 1 := h₆
        linarith
      -- Now we know CharP F 0.
      have hAlg : Algebraic F E := by
        apply IsPurelyInseparable.alg
        exact h
      -- Since CharP F 0, F is perfect.
      have hPerfect : IsPerfect F := IsPerfect.of_char_zero hChar0
      -- Over a perfect field, every algebraic element is separable.
      have hSep : ∀ (x : E), Separable (minpoly F x) := by
        intro x
        have hx : Algebraic F x := hAlg x
        have h₁ : IsIrreducible (minpoly F x) := minpoly.isIrreducible x
        have h₂ : Separable (minpoly F x) := by
          apply hPerfect.irreducible_separable
          exact h₁
        exact h₂
      -- Since the extension is purely inseparable, every element is purely inseparable.
      have hPure : ∀ (x : E), IsPurelyInseparable (minpoly F x) := by
        intro x
        have h₁ : IsPurelyInseparable (algebraMap F E) x := by
          -- Use the fact that the extension is purely inseparable.
          have h₂ : IsPurelyInseparable F E := h
          exact IsPurelyInseparable.map_mem h₂ x
        -- Now we need to relate IsPurelyInseparable (algebraMap F E) x to IsPurelyInseparable (minpoly F x).
        -- In Mathlib, IsPurelyInseparable f x is defined as IsPurelyInseparable (minpoly (source f) x).
        have h₃ : IsPurelyInseparable (algebraMap F E) x = IsPurelyInseparable (minpoly F x) := by
          simp [IsPurelyInseparable]
          <;>
          aesop
        rw [h₃] at h₁
        exact h₁
      -- Now we show that if an element is both separable and purely inseparable, then its minimal polynomial has degree 1.
      have hSurj : Function.Surjective (algebraMap F E) := by
        intro y
        have h₁ : Separable (minpoly F y) := hSep y
        have h₂ : IsPurelyInseparable (minpoly F y) := hPure y
        have h₃ : (minpoly F y).degree = 1 := by
          -- Prove that the degree is 1.
          have h₄ : Separable (minpoly F y) := h₁
          have h₅ : IsPurelyInseparable (minpoly F y) := h₂
          have h₆ : (minpoly F y).degree = 1 := by
            by_contra h₇
            -- If the degree is not 1, then it is either 0 or at least 2.
            have h₈ : (minpoly F y).degree ≠ 1 := h₇
            have h₉ : (minpoly F y).degree = 0 ∨ (minpoly F y).degree ≥ 2 := by
              by_cases h₁₀ : (minpoly F y).degree = 0
              · exact Or.inl h₁₀
              · have h₁₁ : (minpoly F y).degree ≥ 1 := by
                  exact Nat.pos_iff_ne_zero.mpr (by
                    intro h₁₂
                    have h₁₃ : (minpoly F y) = 0 := by simpa using h₁₂
                    have h₁₄ : IsIrreducible (minpoly F y) := minpoly.isIrreducible y
                    exact h₁₄.ne_zero h₁₃
                  )
                have h₁₂ : (minpoly F y).degree ≠ 1 := h₈
                have h₁₃ : (minpoly F y).degree ≥ 2 := by
                  by_contra h₁₄
                  have h₁₅ : (minpoly F y).degree ≤ 1 := by linarith
                  have h₁₆ : (minpoly F y).degree = 1 := by
                    by_contra h₁₇
                    have h₁₈ : (minpoly F y).degree ≠ 1 := h₁₇
                    have h₁₉ : (minpoly F y).degree = 0 := by
                      omega
                    exact Or.inl h₁₉
                  exact h₁₆
                exact h₁₃
              exact Or.inr h₁₃
            cases h₉ with
            | inl h₉ =>
              -- Case: degree 0.
              have h₁₀ : (minpoly F y) = 0 := by
                have h₁₁ : (minpoly F y).degree = 0 := h₉
                have h₁₂ : (minpoly F y) = 0 := by
                  apply Polynomial.eq_zero_of_degree_eq_zero
                  <;> simp_all
                exact h₁₂
              have h₁₁ : IsIrreducible (minpoly F y) := minpoly.isIrreducible y
              rw [h₁₀] at h₁₁
              exact absurd h₁₁ (by simp)
            | inr h₉ =>
              -- Case: degree ≥ 2.
              have h₁₀ : (minpoly F y).degree ≥ 2 := h₉
              -- Since the polynomial is purely inseparable, we can write it as q.comp (X ^ p) where p is the characteristic.
              -- But in characteristic 0, this forces it to be constant.
              have h₁₁ : IsPurelyInseparable (minpoly F y) := h₂
              have h₁₂ : CharP F 0 := hChar0
              have h₁₃ : (minpoly F y).degree = 0 := by
                -- Use the fact that in characteristic 0, a purely inseparable polynomial is constant.
                have h₁₄ : IsPurelyInseparable (minpoly F y) := h₁₁
                have h₁₅ : CharP F 0 := h₁₂
                have h₁₆ : (minpoly F y).degree = 0 := by
                  -- Use the definition of IsPurelyInseparable for polynomials.
                  rw [Polynomial.isPurelyInseparable_iff] at h₁₄
                  obtain ⟨q, hq⟩ := h₁₄
                  have h₁₇ : (minpoly F y) = q.comp (Polynomial.X ^ CharP F) := by
                    simpa [hq] using hq
                  rw [h₁₇]
                  have h₁₈ : CharP F 0 := h₁₂
                  simp [h₁₈, Polynomial.X_pow, Polynomial.comp_C]
                  <;>
                  (try decide) <;>
                  (try {
                    ring_nf at *
                    <;>
                    simp_all [Polynomial.degree_C]
                    <;>
                    omega
                  })
                exact h₁₆
              have h₁₄ : (minpoly F y).degree ≥ 2 := h₁₀
              linarith
          exact h₆
        -- Now we know that the minimal polynomial has degree 1.
        have h₄ : (minpoly F y).degree = 1 := h₃
        have h₅ : monic (minpoly F y) := minpoly.monic y
        have h₆ : ∃ (a : F), minpoly F y = Polynomial.X - Polynomial.C a := by
          -- A monic polynomial of degree 1 is of the form X - a.
          have h₇ : (minpoly F y).degree = 1 := h₄
          have h₈ : monic (minpoly F y) := h₅
          have h₉ : ∃ (a : F), minpoly F y = Polynomial.X - Polynomial.C a := by
            use (minpoly F y).coeff 0
            have h₁₀ : minpoly F y = Polynomial.X - Polynomial.C ((minpoly F y).coeff 0) := by
              have h₁₁ : (minpoly F y).degree = 1 := h₇
              have h₁₂ : monic (minpoly F y) := h₈
              have h₁₃ : minpoly F y = Polynomial.X + Polynomial.C ((minpoly F y).coeff 0) := by
                apply Polynomial.eq_X_add_C_of_degree_eq_one
                <;> simp_all [h₁₁, h₁₂]
              rw [h₁₃]
              <;> simp [sub_eq_add_neg, Polynomial.C_neg]
              <;>
              (try ring_nf at *) <;>
              (try simp_all [Polynomial.coeff_sub, Polynomial.coeff_C, Polynomial.coeff_X]) <;>
              (try omega)
            exact h₁₀
          exact h₉
        obtain ⟨a, ha⟩ := h₆
        have h₇ : minpoly F y = Polynomial.X - Polynomial.C a := ha
        have h₈ : (algebraMap F E) a = y := by
          have h₉ : minpoly F y = Polynomial.X - Polynomial.C a := h₇
          have h₁₀ : IsRoot (minpoly F y) y := by
            apply minpoly_isRoot
          rw [h₉] at h₁₀
          simpa [sub_eq_zero, Polynomial.C_sub_X] using h₁₀
        exact ⟨a, h₈⟩
      -- Now we know that the algebra map is surjective.
      -- Hence, it is an isomorphism (since it's always injective).
      -- Therefore, for any x : E, we can write x = (algebraMap F E) a for some a : F.
      -- Then minpoly F x = X - a, and map (algebraMap F E) (minpoly F x) = X - x.
      -- And (X - C x) ^ q ^ n = (X - x) ^ 1 ^ n = X - x.
      have hMain : ∀ (x : E), ∃ n, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := by
        intro x
        have h₁ : Function.Surjective (algebraMap F E) := hSurj
        obtain ⟨a, ha⟩ := h₁ x
        have h₂ : (algebraMap F E) a = x := ha
        have h₃ : Polynomial.map (algebraMap F E) (minpoly F x) = Polynomial.X - Polynomial.C x := by
          have h₄ : minpoly F x = Polynomial.X - Polynomial.C a := by
            have h₅ : (algebraMap F E) a = x := h₂
            have h₆ : minpoly F x = Polynomial.X - Polynomial.C a := by
              have h₇ : minpoly F (algebraMap F E) a = Polynomial.X - Polynomial.C a := by
                have h₈ : minpoly F (algebraMap F E) a = Polynomial.X - Polynomial.C a := by
                  have h₉ : minpoly F (algebraMap F E) a = Polynomial.X - Polynomial.C (a : F) := by
                    -- Since a : F, and the algebra map is injective,
```

**lean_error:** tail step 2/256 ('· -- Prove the forward direction: IsPurelyInseparable F E ⇒ (∀ x : E, ∃ n, ...)'): <stdin>:1:79: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.3s, in=336, out=1071)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h x
    exact (IsPurelyInseparable.isPurelyInseparable_iff hF).mp h x
  · intro h
    exact (IsPurelyInseparable.isPurelyInseparable_iff hF).mpr h
```

**lean_error:** tail step 2/5 ('· intro h x'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.2s, verify 0.3s, in=1322, out=2389)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h x
    have hx := ((isPurelyInseparable_iff_natSepDegree_eq_one (F:=F) (E:=E)).1 h) x
    rcases (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow (F:=F) (E:=E) (x:=x)).1 hx with ⟨n, hn⟩
    exact ⟨n, hn⟩
  · intro h
    have h' : ∀ x : E, (minpoly F x).natSepDegree = 1 := by
      intro x
      rcases h x with ⟨n, hn⟩
      exact (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow (F:=F) (E:=E) (x:=x)).2 ⟨n, hn⟩
    exact ((isPurelyInseparable_iff_natSepDegree_eq_one (F:=F) (E:=E)).2 h')
```

**lean_error:** tail step 2/11 ('· intro h x'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 36.7s, verify 0.4s, in=1309, out=4115)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
constructor
· intro h x
  exact (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow x).mp (h x)
· intro h x
  exact (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow x).mpr (h x)
```

**lean_error:** tail step 3/6 ('· intro h x'): unsolved goals

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=1222, out=475)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.5s, verify 0.4s, in=5042, out=2475)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
haveI := hF
  constructor
  · intro h x
    have hx := ((isPurelyInseparable_iff_natSepDegree_eq_one (F:=F) (E:=E)).1 h) x
    rcases (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow (F:=F) (E:=E) (x:=x)).1 hx with ⟨n, hn⟩
    exact ⟨n, hn⟩
  · intro h
    have hx : ∀ x : E, (minpoly F x).natSepDegree = 1 := by
      intro x
      rcases h x with ⟨n, hn⟩
      exact (minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow (F:=F) (E:=E) (x:=x)).2 ⟨n, hn⟩
    exact ((isPurelyInseparable_iff_natSepDegree_eq_one (F:=F) (E:=E)).2 hx)
```

**lean_error:** tail step 3/12 ('· intro h x'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.1s, verify 0.1s, in=5149, out=3501)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 : IsPurelyInseparable F E ↔ ∀ x : E, (minpoly F x).natSepDegree = 1 := by
  apply isPurelyInseparable_iff_natSepDegree_eq_one
  
have h2 : (∀ x : E, (minpoly F x).natSepDegree = 1) ↔ (∀ x : E, ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n) := by
  constructor
  · -- Prove the forward direction: if forall x, natSepDegree=1, then forall x, exists n, ...
    intro h x
    have h₁ : (minpoly F x).natSepDegree = 1 := h x
    have h₂ : (minpoly F x).natSepDegree = 1 ↔ ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := by
      apply minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow
    exact (h₂.mp h₁)
  · -- Prove the backward direction: if forall x, exists n, ..., then forall x, natSepDegree=1
    intro h x
    have h₁ : ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := h x
    have h₂ : (minpoly F x).natSepDegree = 1 ↔ ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := by
      apply minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow
    exact (h₂.mpr h₁)
  
have h3 : IsPurelyInseparable F E ↔ (∀ x : E, ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n) := by
  rw [h1]
  rw [h2]
  
exact h3
```

**lean_error:** tail step 1/20 ('have h1 : IsPurelyInseparable F E ↔ ∀ x : E, (minpoly F x).natSepDegree = 1 := by'): <stdin>:1:81: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.2s, in=4879, out=582)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.8s, verify 0.1s, in=4560, out=1567)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow] using
    (isPurelyInseparable_iff_natSepDegree_eq_one (F:=F) (E:=E))
```

**lean_error:** tail step 1/2 ('simpa [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow] using'): <stdin>:1:60: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 39.1s, verify 0.4s, in=5548, out=4422)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
apply Iff.intro
· intro h
  intro x
  have h₁ : (minpoly F x).natSepDegree = 1 := h x
  have h₂ : (minpoly F x).natSepDegree = 1 ↔ ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := by
    apply minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow
  exact (h₂.mp h₁)
· intro h
  intro x
  have h₁ : ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := h x
  have h₂ : (minpoly F x).natSepDegree = 1 ↔ ∃ n : ℕ, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n := by
    apply minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow
  exact (h₂.mpr h₁)
```

**lean_error:** tail step 3/14 ('· intro h'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.4s, verify 0.2s, in=4830, out=842)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress
