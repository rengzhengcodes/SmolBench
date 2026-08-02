## Current goal
```
⊢ (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x
```

## Full tactic state
```
case h.ι_mul
R : Type u_1
M : Type u_2
N : Type u_3
N' : Type u_4
inst✝⁶ : CommRing R
inst✝⁵ : AddCommGroup M
inst✝⁴ : AddCommGroup N
inst✝³ : AddCommGroup N'
inst✝² : Module R M
inst✝¹ : Module R N
inst✝ : Module R N'
g : N →ₗ[R] N'
x : CliffordAlgebra 0
m : M
hx :
  ∀ (f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N),
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) (f i)) x = g ((liftAlternating f) x)
f : (i : ℕ) → M [⋀^Fin i]→ₗ[R] N
⊢ (liftAlternating fun i => (AlternatingMap.curryLeft ((LinearMap.compAlternatingMap g) (f (Nat.succ i)))) m) x =
    (liftAlternating fun i => (LinearMap.compAlternatingMap g) ((AlternatingMap.curryLeft (f (Nat.succ i))) m)) x
```

## Proof so far (6 tactics)
```lean
ext v
rw [LinearMap.comp_apply]
induction' v using CliffordAlgebra.left_induction with r x y hx hy x m hx generalizing f
rw [liftAlternating_algebraMap, liftAlternating_algebraMap, map_smul,
  LinearMap.compAlternatingMap_apply]
rw [map_add, map_add, map_add, hx, hy]
rw [liftAlternating_ι_mul, liftAlternating_ι_mul, ← hx]
```

## Theorem
`ExteriorAlgebra.liftAlternating_comp` in `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`

## Premises used in the next tactic
- `AlternatingMap.curryLeft_compAlternatingMap`

## Premise signatures
### `AlternatingMap.curryLeft_compAlternatingMap` (commanddeclaration)
```lean
@[simp]
theorem curryLeft_compAlternatingMap {n : ℕ} (g : N'' →ₗ[R'] N₂'')
    (f : M'' [⋀^Fin n.succ]→ₗ[R'] N'') (m : M'') :
    (g.compAlternatingMap f).curryLeft m = g.compAlternatingMap (f.curryLeft m)
```

## Premise full source (with proof)
### `AlternatingMap.curryLeft_compAlternatingMap` (commanddeclaration) at `Mathlib/LinearAlgebra/Alternating/Basic.lean`
```lean
@[simp]
theorem curryLeft_compAlternatingMap {n : ℕ} (g : N'' →ₗ[R'] N₂'')
    (f : M'' [⋀^Fin n.succ]→ₗ[R'] N'') (m : M'') :
    (g.compAlternatingMap f).curryLeft m = g.compAlternatingMap (f.curryLeft m) :=
  rfl
```

## Transitive premise context (1-hop, 1/1 premises, ≈167 tokens)
### `Fin` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Fin n` is a natural number `i` with the constraint that `0 ≤ i < n`.
It is the "canonical type with `n` elements".
-/
structure Fin (n : Nat) where
  /-- If `i : Fin n`, then `i.val : ℕ` is the described number. It can also be
  written as `i.1` or just `i` when the target type is known. -/
  val  : Nat
  /-- If `i : Fin n`, then `i.2` is a proof that `i.1 < n`. -/
  isLt : LT.lt val n
```
