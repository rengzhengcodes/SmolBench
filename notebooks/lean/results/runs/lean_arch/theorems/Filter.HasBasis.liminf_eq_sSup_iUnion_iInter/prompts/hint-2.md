## Current goal
```
⊢ x ∈ {a | ∃ i, p i ∧ ∀ ⦃x : ι⦄, x ∈ s i → a ≤ f x} ↔ x ∈ ⋃ j, ⋂ i, Iic (f ↑i)
```

## Full tactic state
```
case e_a.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι✝ : Type u_4
ι'✝ : Type u_5
inst✝ : ConditionallyCompleteLattice α
ι : Type u_6
ι' : Type u_7
f : ι → α
v : Filter ι
p : ι' → Prop
s : ι' → Set ι
hv : HasBasis v p s
x : α
⊢ x ∈ {a | ∃ i, p i ∧ ∀ ⦃x : ι⦄, x ∈ s i → a ≤ f x} ↔ x ∈ ⋃ j, ⋂ i, Iic (f ↑i)
```

## Proof so far (3 tactics)
```lean
simp_rw [liminf_eq, hv.eventually_iff]
congr
ext x
```

## Theorem
`Filter.HasBasis.liminf_eq_sSup_iUnion_iInter` in `Mathlib/Order/LiminfLimsup.lean`

## Premises used in the next tactic
- `Set.mem_setOf_eq`
- `Set.iInter_coe_set`
- `Set.mem_iUnion`
- `Set.mem_iInter`
- `Set.mem_Iic`
- `Subtype.exists`
- `exists_prop`

## Premise signatures
### `Set.mem_setOf_eq` (commanddeclaration)
```lean
@[simp, mfld_simps] theorem mem_setOf_eq {x : α} {p : α → Prop} : (x ∈ {y | p y}) = p x
```

### `Set.iInter_coe_set` (commanddeclaration)
```lean
@[simp]
theorem iInter_coe_set {α β : Type*} (s : Set α) (f : s → Set β) :
    ⋂ i, f i = ⋂ i ∈ s, f ⟨i, ‹i ∈ s›⟩
```

### `Set.mem_iUnion` (commanddeclaration)
```lean
@[simp]
theorem mem_iUnion {x : α} {s : ι → Set α} : (x ∈ ⋃ i, s i) ↔ ∃ i, x ∈ s i
```

### `Set.mem_iInter` (commanddeclaration)
```lean
@[simp]
theorem mem_iInter {x : α} {s : ι → Set α} : (x ∈ ⋂ i, s i) ↔ ∀ i, x ∈ s i
```

### `Set.mem_Iic` (commanddeclaration)
```lean
@[simp]
theorem mem_Iic : x ∈ Iic b ↔ x ≤ b
```

### `Subtype.exists` (commanddeclaration)
```lean
@[simp]
protected theorem «exists» {q : { a // p a } → Prop} : (∃ x, q x) ↔ ∃ a b, q ⟨a, b⟩
```

### `exists_prop` (commanddeclaration)
```lean
@[simp] theorem exists_prop : (∃ _h : a, b) ↔ a ∧ b
```

## Premise full source (with proof)
### `Set.mem_setOf_eq` (commanddeclaration) at `Mathlib/Data/Set/Defs.lean`
```lean
@[simp, mfld_simps] theorem mem_setOf_eq {x : α} {p : α → Prop} : (x ∈ {y | p y}) = p x := rfl
```

### `Set.iInter_coe_set` (commanddeclaration) at `Mathlib/Data/Set/Lattice.lean`
```lean
@[simp]
theorem iInter_coe_set {α β : Type*} (s : Set α) (f : s → Set β) :
    ⋂ i, f i = ⋂ i ∈ s, f ⟨i, ‹i ∈ s›⟩ :=
  iInter_subtype _ _
```

### `Set.mem_iUnion` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
@[simp]
theorem mem_iUnion {x : α} {s : ι → Set α} : (x ∈ ⋃ i, s i) ↔ ∃ i, x ∈ s i :=
  ⟨fun ⟨_, ⟨⟨a, (t_eq : s a = _)⟩, (h : x ∈ _)⟩⟩ => ⟨a, t_eq.symm ▸ h⟩, fun ⟨a, h⟩ =>
    ⟨s a, ⟨⟨a, rfl⟩, h⟩⟩⟩
```

### `Set.mem_iInter` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
@[simp]
theorem mem_iInter {x : α} {s : ι → Set α} : (x ∈ ⋂ i, s i) ↔ ∀ i, x ∈ s i :=
  ⟨fun (h : ∀ a ∈ { a : Set α | ∃ i, s i = a }, x ∈ a) a => h (s a) ⟨a, rfl⟩,
    fun h _ ⟨a, (eq : s a = _)⟩ => eq ▸ h a⟩
```

### `Set.mem_Iic` (commanddeclaration) at `Mathlib/Data/Set/Intervals/Basic.lean`
```lean
@[simp]
theorem mem_Iic : x ∈ Iic b ↔ x ≤ b :=
  Iff.rfl
```

### `Subtype.exists` (commanddeclaration) at `Mathlib/Data/Subtype.lean`
```lean
@[simp]
protected theorem «exists» {q : { a // p a } → Prop} : (∃ x, q x) ↔ ∃ a b, q ⟨a, b⟩ :=
  ⟨fun ⟨⟨a, b⟩, h⟩ ↦ ⟨a, b, h⟩, fun ⟨a, b, h⟩ ↦ ⟨⟨a, b⟩, h⟩⟩
```

### `exists_prop` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
@[simp] theorem exists_prop : (∃ _h : a, b) ↔ a ∧ b :=
  ⟨fun ⟨hp, hq⟩ => ⟨hp, hq⟩, fun ⟨hp, hq⟩ => ⟨hp, hq⟩⟩
```
