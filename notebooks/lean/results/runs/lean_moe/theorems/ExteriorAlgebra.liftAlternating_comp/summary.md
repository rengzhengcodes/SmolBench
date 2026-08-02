# ExteriorAlgebra.liftAlternating_comp   (k=6, 7 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**True premises at k:** `AlternatingMap.curryLeft_compAlternatingMap`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.0s, verify 0.3s, in=583, out=2500)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [LinearMap.compAlternatingMap]
```

**lean_error:** tail step 1/1 ('simpa [LinearMap.compAlternatingMap]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 84.8s, verify 0.1s, in=553, out=9525)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem h.ι_mul {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4}
    [CommRing R] [AddCommGroup M] [AddCommGroup N] [AddCommGroup N']
    [Module R M] [Module R N] [Module R N']
    (g : N →ₗ[R] N')
    (x : CliffordAlgebra 0)
    (m : M)
    (hx :
      ∀ (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N),
        (liftAlternating fun i => (LinearMap.compAlternatingMap g) (f i)) x = g ((liftAlternating f) x))
    (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N) :
    (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
        (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x := by
  have h_main : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by
    apply liftAlternating_congr
    intro i
    have h₁ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) = (LinearMap.compAlternatingMap g) ∘ (AlternatingMap.curryLeft (f (Nat.succ i))) := by
      apply AlternatingMap.curryLeft_comp_left
    have h₂ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
      rw [h₁]
      <;> simp [Function.comp_apply]
      <;>
      rfl
    exact h₂
  
  have h_final : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x := by
    rw [h_main]
    <;>
    rfl
  
  exact h_final
```

**lean_error:** tail step 1/28 ("theorem h.ι_mul {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4}"): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.1s, verify 0.6s, in=535, out=567)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr!
<;> simp [LinearMap.compAlternatingMap, AlternatingMap.curryLeft]
<;> rfl
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.2s, verify 0.7s, in=1003, out=1445)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 108.4s, verify 0.1s, in=996, out=12189)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h_eq : (fun i : ℕ => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) = (fun i : ℕ => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by
  funext i
  rw [show (LinearMap.compAlternatingMap g) (f (Nat.succ i)) = g.compAlternatingMap (f (Nat.succ i)) by rfl]
  rw [AlternatingMap.curryLeft_compAlternatingMap]
  <;> rfl
rw [h_eq]
<;> rfl
```

**lean_error:** tail step 1/7 ('have h_eq : (fun i : ℕ => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) = (fun i : ℕ => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by'): <stdin>:1:211: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.1s, in=970, out=435)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr' with i
rw [AlternatingMap.curryLeft_compAlternatingMap]
```

**lean_error:** tail step 1/2 ("congr' with i"): <stdin>:1:1: unknown tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.0s, verify 0.5s, in=1195, out=711)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [AlternatingMap.curryLeft_compAlternatingMap]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 151.0s, verify 0.1s, in=1192, out=17937)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem ExteriorAlgebra.liftAlternating_comp {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4} [CommRing R] [AddCommGroup M] [AddCommGroup N] [AddCommGroup N'] [Module R M] [Module R N] [Module R N'] (g : N →ₗ[R] N') (x : CliffordAlgebra 0) (m : M) (hx : ∀ (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N), (liftAlternating fun i => (LinearMap.compAlternatingMap g) (f i)) x = g ((liftAlternating f) x)) (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N) :
    (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
        (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x := by
  ext v
  rw [LinearMap.comp_apply]
  induction' v using CliffordAlgebra.left_induction with r x y hx hy x m hx generalizing f
  rw [liftAlternating_algebraMap, liftAlternating_algebraMap, map_smul, LinearMap.compAlternatingMap_apply]
  rw [map_add, map_add, map_add, hx, hy]
  rw [liftAlternating_ι_mul, liftAlternating_ι_mul, ← hx]
  have h_main : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) m) x := by
    have h_family : (fun i : ℕ => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i))))) = (fun i : ℕ => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by
      funext i
      have h₁ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
        have h₂ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
          -- Use the lemma AlternatingMap.curryLeft_compAlternatingMap to show the equality
          have h₃ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
            -- Apply the lemma with the appropriate arguments
            have h₄ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
              -- Use the lemma AlternatingMap.curryLeft_compAlternatingMap
              rw [AlternatingMap.curryLeft_compAlternatingMap]
              <;>
              simp_all [Function.comp_apply]
              <;>
              try aesop
            exact h₄
          exact h₃
        exact h₂
      exact h₁
    -- Use the equality of the families to rewrite the liftAlternating
    calc
      (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x = (liftAlternating (fun i : ℕ => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) m) x := by
        rw [h_family]
      _ = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) m) x := by rfl
  exact h_main
```

**lean_error:** tail step 1/34 ("theorem ExteriorAlgebra.liftAlternating_comp {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4} [CommRing R] [AddCommGroup M] [AddCommGroup N] [AddCommGroup N'] [Module R M] [Module R N] [Module R N'] (g : N →ₗ[R] N') (x : CliffordAlgebra 0) (m : M) (hx : ∀ (f : (i : ℕ) → 

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.2s, verify 0.4s, in=1167, out=483)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
  ext i
  rw [AlternatingMap.curryLeft_compAlternatingMap]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.8s, verify 0.5s, in=1198, out=918)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 98.9s, verify 0.1s, in=1247, out=11127)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem ExteriorAlgebra.liftAlternating_comp {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4} [CommRing R] [AddCommGroup M] [AddCommGroup N] [AddCommGroup N'] [Module R M] [Module R N] [Module R N'] (g : N →ₗ[R] N') (x : CliffordAlgebra 0) (m : M) (hx : ∀ (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N), (liftAlternating fun i => (LinearMap.compAlternatingMap g) (f i)) x = g ((liftAlternating f) x)) (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N) : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x := by
  have h_family : (fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i))) m)) = (fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by
    funext i
    have h₂ : (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m = (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
      rw [AlternatingMap.curryLeft_compAlternatingMap]
    exact h₂
  
  have h_lift : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i))) m)) = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) := by
    apply liftAlternating_congr
    exact h_family
  
  have h_main : (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i))) m)) x = (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x := by
    rw [h_lift]
  
  exact h_main
```

**lean_error:** tail step 1/12 ("theorem ExteriorAlgebra.liftAlternating_comp {R : Type u_1} {M : Type u_2} {N : Type u_3} {N' : Type u_4} [CommRing R] [AddCommGroup M] [AddCommGroup N] [AddCommGroup N'] [Module R M] [Module R N] [Module R N'] (g : N →ₗ[R] N') (x : CliffordAlgebra 0) (m : M) (hx : ∀ (f : (i : ℕ) → 

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.7s, verify 0.4s, in=1185, out=764)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [AlternatingMap.curryLeft_compAlternatingMap]
```
