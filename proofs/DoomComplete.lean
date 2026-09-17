import Init

/- Abstract obstructions only: no claim connecting these types to C execution. -/
namespace DoomComplete

def Injective (f : A → B) : Prop := ∀ ⦃x y⦄, f x = f y → x = y

def iterate (f : A → A) : Nat → A → A
  | 0, x => x
  | n + 1, x => f (iterate f n x)

/-- A decoder that is a left inverse forces lossless encoding. -/
theorem encoding_injective (e : A → B) (d : B → A)
    (roundtrip : ∀ x, d (e x) = x) : Injective e := by
  intro x y h
  calc
    x = d (e x) := (roundtrip x).symm
    _ = d (e y) := congrArg d h
    _ = y := roundtrip y

/-- A witnessed collision rules out a lossless decoder. -/
theorem collision_no_decoder (e : A → B) (x y : A)
    (hne : x ≠ y) (h : e x = e y) :
    ¬ ∃ d : B → A, ∀ z, d (e z) = z := by
  intro ⟨d, hd⟩
  exact hne (encoding_injective e d hd h)

theorem iterate_injective (f : A → A) (hf : Injective f) (n : Nat) :
    Injective (iterate f n) := by
  induction n with
  | zero => intro x y h; exact h
  | succ n ih => intro x y h; exact ih (hf h)

/-- Exact fixed-clock embedding into an injective host implies injective guest.
    This is NOT a theorem about projected/history-retaining simulations. -/
theorem fixed_clock_injective (guest : A → A) (host : B → B)
    (e : A → B) (k : Nat) (he : Injective e) (hh : Injective host)
    (sim : ∀ x, iterate host k (e x) = e (guest x)) : Injective guest := by
  intro x y h
  apply he
  apply iterate_injective host hh k
  exact (sim x).trans ((congrArg e h).trans (sim y).symm)

theorem collision_no_fixed_clock (guest : A → A) (host : B → B)
    (e : A → B) (k : Nat) (he : Injective e) (hh : Injective host)
    (x y : A) (hne : x ≠ y) (h : guest x = guest y) :
    ¬ (∀ z, iterate host k (e z) = e (guest z)) := by
  intro sim
  exact hne (fixed_clock_injective guest host e k he hh sim h)

/-- Explicit finite-capacity bound; `states` may contain duplicates.
    Finiteness is supplied as a complete list, not inferred from Doom source. -/
theorem capacity_bound (e : A → B) (samples : List A) (states : List B)
    (hs : samples.Nodup) (he : Injective e)
    (cover : ∀ x, e x ∈ states) : samples.length ≤ states.length := by
  have hm : (samples.map e).Nodup :=
    List.Pairwise.map e (fun _ _ hne h => hne (he h)) hs
  have sub : samples.map e ⊆ states := by
    intro b hb
    obtain ⟨a, _, rfl⟩ := List.mem_map.mp hb
    exact cover a
  simpa using hm.length_le_of_subset sub

/-- More distinguishable samples than host states rules out injection. -/
theorem finite_no_injection (e : A → B) (samples : List A) (states : List B)
    (hs : samples.Nodup) (cover : ∀ x, e x ∈ states)
    (large : states.length < samples.length) : ¬ Injective e := by
  intro he
  exact Nat.not_le_of_gt large (capacity_bound e samples states hs he cover)

/-- Pigeonhole collision, obtained classically from the finite bound. -/
theorem finite_collision (e : A → B) (samples : List A) (states : List B)
    (hs : samples.Nodup) (cover : ∀ x, e x ∈ states)
    (large : states.length < samples.length) : ∃ x y, x ≠ y ∧ e x = e y := by
  apply Classical.byContradiction
  intro h
  apply finite_no_injection e samples states hs cover large
  intro x y heq
  apply Classical.byContradiction
  intro hne
  exact h ⟨x, y, hne, heq⟩

/-- No lossless encoding for a source with arbitrarily large distinct samples. -/
theorem unbounded_no_decoder (e : A → B) (states : List B)
    (cover : ∀ x, e x ∈ states)
    (unbounded : ∀ n, ∃ xs : List A, xs.Nodup ∧ n < xs.length) :
    ¬ ∃ d : B → A, ∀ x, d (e x) = x := by
  obtain ⟨xs, hs, large⟩ := unbounded states.length
  intro ⟨d, hd⟩
  exact finite_no_injection e xs states hs cover large (encoding_injective e d hd)

end DoomComplete

#print axioms DoomComplete.capacity_bound
#print axioms DoomComplete.finite_collision
#print axioms DoomComplete.unbounded_no_decoder
#print axioms DoomComplete.collision_no_decoder
#print axioms DoomComplete.collision_no_fixed_clock
