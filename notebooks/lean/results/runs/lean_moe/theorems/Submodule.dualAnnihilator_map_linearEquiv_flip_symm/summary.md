# Submodule.dualAnnihilator_map_linearEquiv_flip_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PerfectPairing.lean`  

**Ground-truth tail (from k):**
```lean
rw [← map_dualCoannihilator_linearEquiv_flip, flip_flip]
```

**True premises at k:** `Submodule.map_dualCoannihilator_linearEquiv_flip`, `LinearEquiv.flip_flip`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

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

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 37.4s, verify 1.4s, in=981, out=8290)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (Submodule.map_dualCoannihilator_linearEquiv_flip (e := e.flip) (p := p)).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.3s, verify 0.1s, in=1929, out=3287)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (Submodule.map_dualCoannihilator_linearEquiv_flip (R:=R) (M:=N) (N:=M) (e:=e.flip) p).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.6s, verify 0.1s, in=1843, out=4313)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [LinearEquiv.flip_flip] using
  (map_dualCoannihilator_linearEquiv_flip (R:=R) (M:=N) (N:=M) (e:=e.flip) p).symm
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.flip_flip] using'): <stdin>:1:35: unexpected end of input
