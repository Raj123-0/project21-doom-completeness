import Init

/- The filename is historical: this file does NOT construct or prove a UTM. -/
namespace BoundedRule110

/-- Inputs ordered left, center, right; Wolfram bits 111 down to 000. -/
def rule110 (l c r : Bool) : Bool := (c && !l) || (c != r)

def table : List Bool :=
  [rule110 true true true, rule110 true true false,
   rule110 true false true, rule110 true false false,
   rule110 false true true, rule110 false true false,
   rule110 false false true, rule110 false false false]

theorem truth_table : table =
    [false, true, true, false, true, true, true, false] := by decide

/-- Alternate explicit pattern specification checked on every Boolean triple. -/
def ruleByCases : Bool → Bool → Bool → Bool
  | true, true, true => false
  | true, true, false => true
  | true, false, true => true
  | true, false, false => false
  | false, true, true => true
  | false, true, false => true
  | false, false, true => true
  | false, false, false => false

theorem local_correct (l c r : Bool) : rule110 l c r = ruleByCases l c r := by
  cases l <;> cases c <;> cases r <;> rfl

/-- Fixed-length finite row, false exterior reset at EACH step; no wraparound. -/
def sweep (left : Bool) : List Bool → List Bool
  | [] => []
  | c :: rest => rule110 left c (rest.headD false) :: sweep c rest

def step (row : List Bool) : List Bool := sweep false row

theorem sweep_length (left : Bool) (row : List Bool) :
    (sweep left row).length = row.length := by
  induction row generalizing left with
  | nil => rfl
  | cons c rest ih => simp [sweep, ih]

theorem step_length (row : List Bool) : (step row).length = row.length :=
  sweep_length false row

/-- The trace includes the initial row and exactly n successors. -/
def trace : Nat → List Bool → List (List Bool)
  | 0, row => [row]
  | n + 1, row => row :: trace n (step row)

theorem trace_length (n : Nat) (row : List Bool) :
    (trace n row).length = n + 1 := by
  induction n generalizing row with
  | zero => rfl
  | succ n ih => simp [trace, ih]

/-- Kernel reduction, not native_decide and not a universality proof. -/
theorem bounded_trace : trace 4 [false, false, false, true, false, false, false] =
    [[false, false, false, true, false, false, false],
     [false, false, true, true, false, false, false],
     [false, true, true, true, false, false, false],
     [true, true, false, true, false, false, false],
     [true, true, true, true, false, false, false]] := by decide

/-- Purely conditional composition of one-step commuting diagrams.
    No implementation, C semantics, compiler, or universal machine is supplied. -/
theorem conditional_composition (f : A → A) (g : B → B) (h : C → C)
    (e : A → B) (d : B → C)
    (he : ∀ x, g (e x) = e (f x)) (hd : ∀ y, h (d y) = d (g y)) :
    ∀ x, h (d (e x)) = d (e (f x)) := by
  intro x
  exact (hd (e x)).trans (congrArg d (he x))

end BoundedRule110

#eval BoundedRule110.table
#eval BoundedRule110.trace 4 [false, false, false, true, false, false, false]
#print axioms BoundedRule110.truth_table
#print axioms BoundedRule110.local_correct
#print axioms BoundedRule110.bounded_trace
#print axioms BoundedRule110.conditional_composition
