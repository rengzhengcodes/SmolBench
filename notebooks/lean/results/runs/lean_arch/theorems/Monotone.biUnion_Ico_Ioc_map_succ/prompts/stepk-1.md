## Current goal
```
⊢ ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i))
```

## Full tactic state
```
case neg
α : Type u_1
β : Type u_2
inst✝³ : LinearOrder α
inst✝² : SuccOrder α
inst✝¹ : IsSuccArchimedean α
inst✝ : LinearOrder β
f : α → β
hf : Monotone f
m n : α
hmn : m ≤ n
k : α
hmk : m ≤ k
ihk : ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) = Ioc (f m) (f k)
hk : ¬IsMax k
⊢ ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i))
```
