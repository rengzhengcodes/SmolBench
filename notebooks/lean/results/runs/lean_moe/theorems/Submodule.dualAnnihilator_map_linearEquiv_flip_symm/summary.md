# Submodule.dualAnnihilator_map_linearEquiv_flip_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PerfectPairing.lean`  

**Ground-truth tail (from k):**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**True premises at k:** `Submodule.map_dualCoannihilator_linearEquiv_flip`, `LinearEquiv.flip_flip`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 28.5s, verify 0.5s, in=407, out=6023)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ψ
  constructor
  · intro h
    have h' := (mem_dualAnnihilator).1 h
    refine (Submodule.mem_map).2 ?_
    refine ⟨e.symm ψ, ?_, ?_⟩
    · intro φ hφ
      have : ((LinearEquiv.symm (LinearEquiv.flip e)) φ) ψ = 0 :=
        h' _ ((Submodule.mem_map).2 ⟨φ, hφ, rfl⟩)
      simpa using this
    · simpa using (LinearEquiv.apply_symm_apply e ψ)
  · intro h
    rcases (Submodule.mem_map).1 h with ⟨n, hn, rfl⟩
    have hn' := (mem_dualCoannihilator).1 hn
    apply (mem_dualAnnihilator).2
    intro φ hφ
    rcases (Submodule.mem_map).1 hφ with ⟨φ', hφ', rfl⟩
    have : φ' n = 0 := hn' _ hφ'
    simpa using this
```

**lean_error:** tail step 3/19 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 281.3s, verify 0.1s, in=369, out=32066)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem dualAnnihilator_map_symm_flip_e {R : Type u_1} {M : Type u_2} {N : Type u_3}
    [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N]
    [IsReflexive R M] (e : N ≃ₗ[R] Dual R M) (p : Submodule R (Dual R N))
    [IsReflexive R N] :
    dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p) := by
  have h_ortho' : dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map ((LinearEquiv.flip e).dualMap) (dualAnnihilator p) := by
    have h₁ : dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = orthogonal (map (LinearEquiv.symm (LinearEquiv.flip e)) p) := by rw [dualAnnihilator_eq_orthogonal]
    have h₂ : orthogonal (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap) ⁻¹' (orthogonal p) := by
      apply Map.orthogonal_map
    have h₃ : ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap) ⁻¹' (orthogonal p) = map (((LinearEquiv.symm (LinearEquiv.flip e)).dualMap).symm) (orthogonal p) := by
      have h₄ : ((LinearEquiv.symm (LinearEquiv.flip e)) : Dual R N ≃ₗ[R] M) := LinearEquiv.symm (LinearEquiv.flip e)
      have h₅ : ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap : Dual R M →ₗ[R] Dual R (Dual R N)) := h₄.dualMap
      have h₆ : Function.Bijective ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap) := h₅.bijective
      have h₇ : ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap) ⁻¹' (orthogonal p) = map (((LinearEquiv.symm (LinearEquiv.flip e)).dualMap).symm) (orthogonal p) := by
        apply Equiv.map_inv_map
        <;>
        (try infer_instance) <;>
        (try exact h₆) <;>
        (try simp_all [Function.Bijective])
        <;>
        (try aesop)
      rw [h₇]
    calc
      dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = h₁ := by rw [h₁]
      _ = h₂ := by rw [h₂]
      _ = h₃ := by rw [h₃]
      _ = map (((LinearEquiv.symm (LinearEquiv.flip e)).dualMap).symm) (orthogonal p) := by rw
      _ = map ((LinearEquiv.flip e).dualMap) (dualAnnihilator p) := by
        have h₄ : ((LinearEquiv.symm (LinearEquiv.flip e)).dualMap).symm = (LinearEquiv.flip e).dualMap := by
          rw [LinearMap.dualMap_symm]
        rw [h₄]
        <;> rw [dualAnnihilator_eq_orthogonal]
  
  have h_ι_prop : (LinearEquiv.flip e).dualMap ∘ (fun n : N => Dual.eval n : N → Dual R (Dual R N)) = e := by
    ext n
    ext m
    simp [LinearMap.dualMap_apply, Dual.eval_apply, LinearEquiv.flip_apply_apply]
  
  have h_ι_surj : Function.Surjective (fun n : N => Dual.eval n : N → Dual R (Dual R N)) := by
    have h₁ : Function.Surjective (fun n : N => Dual.eval n : N → Dual R (Dual R N)) :=
      IsReflexive.dualEquiv this.surjective
    exact h₁
  
  have h_map_ι : map (fun n : N => Dual.eval n : N → Dual R (Dual R N)) (dualCoannihilator p) = dualAnnihilator p := by
    apply Subset.antisymm
    · -- Prove map ι (dualCoannihilator p) ⊆ dualAnnihilator p
      intro ψ hψ
      rw [Set.mem_image] at hψ
      obtain ⟨n, hn, rfl⟩ := hψ
      rw [dualAnnihilator_eq_orthogonal]
      intro φ hφ
      have h₁ : (Dual.eval n) φ = φ n := rfl
      have h₂ : φ n = 0 := hn hφ
      rw [h₁] at *
      exact h₂
    · -- Prove dualAnnihilator p ⊆ map ι (dualCoannihilator p)
      intro ψ hψ
      have h₁ : Function.Surjective (fun n : N => Dual.eval n : N → Dual R (Dual R N)) := h_ι_surj
      obtain ⟨n, rfl⟩ := h₁ ψ
      have h₂ : n ∈ dualCoannihilator p := by
        intro φ hφ
        have h₃ : (Dual.eval n) φ = φ n := rfl
        have h₄ : ψ φ = 0 := hψ hφ
        rw [h₃] at h₄
        exact h₄
      exact h₂
  
  have h_final : dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p) := by
    calc
      dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map ((LinearEquiv.flip e).dualMap) (dualAnnihilator p) := by rw [h_ortho']
      _ = map ((LinearEquiv.flip e).dualMap) (map (fun n : N => Dual.eval n : N → Dual R (Dual R N)) (dualCoannihilator p)) := by
        rw [h_map_ι]
      _ = map (((LinearEquiv.flip e).dualMap) ∘ (fun n : N => Dual.eval n : N → Dual R (Dual R N))) (dualCoannihilator p) := by
        rw [map_map]
      _ = map e (dualCoannihilator p) := by
        rw [h_ι_prop]
  
  exact h_final
```

**lean_error:** tail step 1/73 ('theorem dualAnnihilator_map_symm_flip_e {R : Type u_1} {M : Type u_2} {N : Type u_3}'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.5s, verify 0.3s, in=357, out=490)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [dualAnnihilator, dualCoannihilator, LinearEquiv.flip, LinearEquiv.symm]
<;>
aesop
```

**lean_error:** tail step 2/4 ('simp [dualAnnihilator, dualCoannihilator, LinearEquiv.flip, LinearEquiv.symm]'): tactic 'simp' failed, nested error:

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 37.4s, verify 1.4s, in=981, out=8290)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (Submodule.map_dualCoannihilator_linearEquiv_flip (e := e.flip) (p := p)).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.5s, verify 0.1s, in=1016, out=32768)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hψ_in : ψ ∈ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) := by
  intro m hm
  -- Obtain φ such that m = (e.flip).symm φ and φ ∈ p
  obtain ⟨φ, hφ, rfl⟩ := hm
  -- Now, ψ m = (e n) m
  have h1 : ψ m = (e n) m := by
    rw [hn]
    <;> simp [mul_comm]
  rw [h1]
  -- (e n) m = (e.flip) m n
  have h2 : (e n) m = (LinearEquiv.flip e) m n := by
    simp [LinearEquiv.flip_apply]
    <;>
    simp_all [LinearMap.apply_comp_apply]
    <;>
    ring_nf
    <;>
    simp_all
  rw [h2]
  -- Now, m = (e.flip).symm φ, so (e.flip) m = φ
  have h3 : (LinearEquiv.flip e) m = φ := by
    have h4 : (LinearEquiv.flip e) m = (LinearEquiv.flip e) ((LinearEquiv.symm (LinearEquiv.flip e)) φ) := by
      rw [hφ]
    rw [h4]
    <;> simp [LinearEquiv.apply_symm_apply]
  rw [h3]
  -- So we have φ n
  -- Since n ∈ p.dualCoannihilator, and φ ∈ p, we have φ n = 0
  have h4 : φ n = 0 := by
    have h5 : n ∈ p.dualCoannihilator := hn'
    have h6 : φ ∈ p := hφ
    exact h5 h6
  rw [h4]
  <;> simp
```

**lean_error:** tail step 1/34 ('have hψ_in : ψ ∈ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) := by'): <stdin>:1:86: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 15.9s, verify 0.1s, in=937, out=1630)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip (e := e.flip) p, flip_flip]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.3s, verify 0.1s, in=1929, out=3287)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (Submodule.map_dualCoannihilator_linearEquiv_flip (R:=R) (M:=N) (N:=M) (e:=e.flip) p).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.3s, verify 0.1s, in=2016, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁₀ : map e p = ((map e p).dualAnnihilator).dualAnnihilator := by
  have h₁₁ : IsReflexive R (Dual R M) := by
    -- Since M is reflexive, Dual R M is reflexive
    exact IsReflexive.dual inst✝
  -- Use the property of reflexive modules: q = (q.dualAnnihilator).dualAnnihilator
  have h₁₂ : map e p = ((map e p).dualAnnihilator).dualAnnihilator := by
    apply Eq.symm
    apply h₁₁.dualAnnihilator_dualAnnihilator
  exact h₁₂
```

**lean_error:** tail step 1/9 ('have h₁₀ : map e p = ((map e p).dualAnnihilator).dualAnnihilator := by'): <stdin>:1:70: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 64.5s, verify 0.2s, in=1899, out=6774)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [map_dualCoannihilator_linearEquiv_flip]
rw [flip_flip]
```

**lean_error:** tail step 1/2 ('rw [map_dualCoannihilator_linearEquiv_flip]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.6s, verify 0.1s, in=1843, out=4313)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (map_dualCoannihilator_linearEquiv_flip (R:=R) (M:=N) (N:=M) (e:=e.flip) p).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 287.4s, verify 0.1s, in=2140, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
R : Type u_1
M : Type u_2
N : Type u_3
inst✝⁵ : CommRing R
inst✝⁴ : AddCommGroup M
inst✝³ : Module R M
inst✝² : AddCommGroup N
inst✝¹ : Module R N
inst✝ : IsReflexive R M
e : N ≃ₗ[R] Dual R M
p : Submodule R (Dual R N)
this : IsReflexive R N
⊢ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p)
```

**lean_error:** tail step 1/13 ('R : Type u_1'): <stdin>:1:1: unknown tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.2s, in=1894, out=504)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip]
<;> simp [LinearEquiv.flip_flip]
```

**lean_error:** tail step 2/2 ('<;> simp [LinearEquiv.flip_flip]'): <stdin>:1:0: expected tactic
