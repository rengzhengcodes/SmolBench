# RatFunc.laurentAux_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/Laurent.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, ← mk_one, mk_eq_div, laurentAux_div, mk_eq_div, taylor_one, map_one, map_one]
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one`, `RatFunc.mk_eq_div`, `RatFunc.laurentAux_div`, `RatFunc.mk_eq_div`, `Polynomial.taylor_one`, `map_one`, `map_one`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | · |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 5.8s, verify 0.1s, in=347, out=857)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [laurentAux]
```

**final state (truncated):**
```
R : Type u
inst✝ : CommRing R
hdomain : IsDomain R
r s : R
p q : R[X]
f : RatFunc R
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 192.5s, verify 0.1s, in=292, out=22726)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h_laurent : laurentAux r (algebraMap R[X] (RatFunc R) p) = algebraMap R[X] (RatFunc R) p := by
  have h₂ : ∀ (q : R[X]), laurentAux r (algebraMap R[X] (RatFunc R) q) = algebraMap R[X] (RatFunc R) q := by
    intro q
    induction q using Polynomial.induction_on' with
    | h_zero =>
      simp [laurentAux_zero]
    | h_cons c q ih =>
      simp_all [laurentAux_add, laurentAux_mul, laurentAux_C, laurentAux_X, pow_succ, mul_add, add_mul,
                algebraMap_add, algebraMap_mul, algebraMap_zero, algebraMap_one, algebraMap_C, algebraMap_X]
      <;>
      (try ring_nf at *) <;>
      (try simp_all [laurentAux_add, laurentAux_mul, laurentAux_C, laurentAux_X]) <;>
      (try assumption) <;>
      (try exact ih) <;>
      (try linarith)
  exact h₂ p
have h_taylor : taylor r p = p := by
  have h₂ : ∀ (q : R[X]), taylor r q = q := by
    intro q
    induction q using Polynomial.induction_on' with
    | h_zero =>
      simp [taylor_zero]
    | h_cons c q ih =>
      simp_all [taylor_add, taylor_mul, taylor_C, taylor_X, pow_succ, mul_add, add_mul] <;>
      (try ring_nf at *) <;>
      (try simp_all [taylor_add, taylor_mul, taylor_C, taylor_X]) <;>
      (try assumption) <;>
      (try exact ih) <;>
      (try linarith)
  exact h₂ p
have h₁ : laurentAux r (algebraMap R[X] (RatFunc R) p) = algebraMap R[X] (RatFunc R) p := h_laurent
have h₂ : taylor r p = p := h_taylor
have h₃ : algebraMap R[X] (RatFunc R) (taylor r p) = algebraMap R[X] (RatFunc R) p := by
  rw [h₂]
rw [h₁]
rw [h₃]
<;> rfl
```

**lean_error:** tail step 1/37 ('have h_laurent : laurentAux r (algebraMap R[X] (RatFunc R) p) = algebraMap R[X] (RatFunc R) p := by'): <stdin>:1:99: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.4s, verify 0.2s, in=299, out=507)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [laurentAux, taylor]
```

**final state (truncated):**
```
R : Type u
inst✝ : CommRing R
hdomain : IsDomain R
r s : R
p q : R[X]
f : RatFunc R
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.2s, verify 0.1s, in=1491, out=860)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [RatFunc.mk_one, map_one, div_one] using
  (RatFunc.laurentAux_div (r:=r) (p:=p) (q:=(1 : R[X])))
```

**lean_error:** tail step 1/2 ('simpa [RatFunc.mk_one, map_one, div_one] using'): <stdin>:1:46: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 38.7s, verify 0.1s, in=1486, out=4412)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  laurentAux r (algebraMap R[X] (RatFunc R) p) = laurentAux r (RatFunc.mk p 1) := by rw [← RatFunc.mk_one p]
  _ = laurentAux r ((algebraMap R[X] (RatFunc R) p) / (algebraMap R[X] (RatFunc R) 1)) := by rw [RatFunc.mk_eq_div]
  _ = (algebraMap R[X] (RatFunc R) (taylor r p)) / (algebraMap R[X] (RatFunc R) (taylor r 1)) := by rw [RatFunc.laurentAux_div]
  _ = (algebraMap R[X] (RatFunc R) (taylor r p)) / 1 := by
    have h : algebraMap R[X] (RatFunc R) (taylor r 1) = 1 := by
      calc
        algebraMap R[X] (RatFunc R) (taylor r 1) = algebraMap R[X] (RatFunc R) (1 : R[X]) := by rw [Polynomial.taylor_one]
        _ = 1 := by simp [map_one]
    rw [h]
  _ = algebraMap R[X] (RatFunc R) (taylor r p) := by simp
```

**lean_error:** tail step 1/11 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.2s, verify 0.5s, in=1478, out=713)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← RatFunc.mk_one p]
rw [RatFunc.mk_eq_div]
rw [RatFunc.laurentAux_div]
simp [Polynomial.taylor_one, map_one]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.3s, in=3239, out=1596)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← RatFunc.mk_one]
simp [RatFunc.mk_eq_div]
simpa using (RatFunc.laurentAux_div (r:=r) (p:=p) (q:=(1 : R[X])))
```

**lean_error:** tail step 1/3 ('simp [← RatFunc.mk_one]'): tactic 'simp' failed, nested error:

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 63.0s, verify 0.1s, in=3289, out=7061)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : laurentAux r ((algebraMap R[X] (RatFunc R)) p / (algebraMap R[X] (RatFunc R)) (1 : R[X])) = (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) := by
  apply RatFunc.laurentAux_div
have h₂ : (algebraMap R[X] (RatFunc R)) (1 : R[X]) = 1 := by
  apply map_one
have h₃ : ((algebraMap R[X] (RatFunc R)) p) / (algebraMap R[X] (RatFunc R)) (1 : R[X]) = (algebraMap R[X] (RatFunc R)) p := by
  rw [h₂]
  <;> simp [div_one]
have h₄ : laurentAux r ((algebraMap R[X] (RatFunc R)) p) = laurentAux r (((algebraMap R[X] (RatFunc R)) p) / (algebraMap R[X] (RatFunc R)) (1 : R[X])) := by
  rw [h₃]
have h₅ : taylor r (1 : R[X]) = (1 : R[X]) := by
  rw [Polynomial.taylor_one]
have h₆ : (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) = 1 := by
  rw [h₅]
  <;> apply map_one
have h₇ : (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) = (algebraMap R[X] (RatFunc R)) (taylor r p) := by
  rw [h₆]
  <;> simp [div_one]
have h₈ : laurentAux r ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) (taylor r p) := by
  calc
    laurentAux r ((algebraMap R[X] (RatFunc R)) p) = laurentAux r (((algebraMap R[X] (RatFunc R)) p) / (algebraMap R[X] (RatFunc R)) (1 : R[X])) := by rw [h₄]
    _ = (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) := by rw [h₁]
    _ = (algebraMap R[X] (RatFunc R)) (taylor r p) := by rw [h₇]
exact h₈
```

**lean_error:** tail step 1/23 ('have h₁ : laurentAux r ((algebraMap R[X] (RatFunc R)) p / (algebraMap R[X] (RatFunc R)) (1 : R[X])) = (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) := by'): <stdin>:1:204: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=3271, out=612)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RatFunc.mk_eq_div, RatFunc.laurentAux_div, Polynomial.taylor_one, map_one, div_one]
```

**lean_error:** tail step 1/1 ('simp only [RatFunc.mk_eq_div, RatFunc.laurentAux_div, Polynomial.taylor_one, map_one, div_one]'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=3075, out=1265)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [map_one, Polynomial.taylor_one] using
    (RatFunc.laurentAux_div (r := r) (p := p) (q := (1 : R[X])))
```

**lean_error:** tail step 1/2 ('simpa [map_one, Polynomial.taylor_one] using'): <stdin>:1:44: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 73.4s, verify 0.1s, in=3557, out=8335)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem RatFunc.laurentAux_algebraMap {R : Type u} [CommRing R] [IsDomain R] {r s : R} {p q : R[X]} {f : RatFunc R} :
    (laurentAux r) ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) ((taylor r) p) := by
  have h_one : (algebraMap R[X] (RatFunc R)) (1 : R[X]) = (1 : RatFunc R) := by
    simp [map_one]
  
  have h_two : (algebraMap R[X] (RatFunc R)) p = (algebraMap R[X] (RatFunc R)) p / (algebraMap R[X] (RatFunc R)) (1 : R[X]) := by
    rw [h_one]
    <;> simp [div_one]
  
  have h_three : laurentAux r ((algebraMap R[X] (RatFunc R)) p) = laurentAux r (((algebraMap R[X] (RatFunc R)) p) / ((algebraMap R[X] (RatFunc R)) (1 : R[X]))) := by
    rw [h_two]
  
  have h_four : laurentAux r (((algebraMap R[X] (RatFunc R)) p) / ((algebraMap R[X] (RatFunc R)) (1 : R[X]))) = (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) := by
    apply laurentAux_div
  
  have h_five : taylor r (1 : R[X]) = (1 : R[X]) := by
    simp [taylor_one]
    <;> simp [C_1]
  
  have h_six : (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) = (1 : RatFunc R) := by
    rw [h_five]
    <;> simp [map_one]
  
  have h_seven : (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) = (algebraMap R[X] (RatFunc R)) (taylor r p) := by
    rw [h_six]
    <;> simp [div_one]
  
  have h_eight : laurentAux r ((algebraMap R[X] (RatFunc R)) p) = (algebraMap R[X] (RatFunc R)) (taylor r p) := by
    calc
      laurentAux r ((algebraMap R[X] (RatFunc R)) p) = laurentAux r (((algebraMap R[X] (RatFunc R)) p) / ((algebraMap R[X] (RatFunc R)) (1 : R[X]))) := by rw [h_three]
      _ = (algebraMap R[X] (RatFunc R)) (taylor r p) / (algebraMap R[X] (RatFunc R)) (taylor r (1 : R[X])) := by rw [h_four]
      _ = (algebraMap R[X] (RatFunc R)) (taylor r p) / (1 : RatFunc R) := by rw [h_six]
      _ = (algebraMap R[X] (RatFunc R)) (taylor r p) := by simp [div_one]
  
  apply h_eight
```

**lean_error:** tail step 1/27 ('theorem RatFunc.laurentAux_algebraMap {R : Type u} [CommRing R] [IsDomain R] {r s : R} {p q : R[X]} {f : RatFunc R} :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 28.7s, verify 0.1s, in=3241, out=3024)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← map_one (algebraMap R[X] (RatFunc R))]
rw [laurentAux_div]
simp [taylor_one, map_one]
```

**lean_error:** tail step 1/3 ('rw [← map_one (algebraMap R[X] (RatFunc R))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
