# Definitions and limits

## Checked abstract results (`proofs/DoomComplete.lean`)

* `Injective e`: for all `x,y`, `e x = e y` implies `x = y`.
  A lossless encoding has a decoder `d` with `d (e x) = x` for **every** source
  state. `encoding_injective` derives injectivity; `collision_no_decoder`
  excludes such a decoder given distinct `x,y` with equal encodings.
* `capacity_bound`: if `samples` is a duplicate-free finite source list,
  `e` is injective, and every encoded source state belongs to the finite list
  `states`, then `samples.length <= states.length`. The host list need not be
  duplicate-free; its length is an upper bound, not necessarily cardinality.
* `finite_no_injection` and `finite_collision`: if the same cover and distinct
  samples have `states.length < samples.length`, encoding is noninjective and
  there exist distinct source states with the same encoding. The existential
  witnesses are not asserted to belong to `samples` in the theorem's conclusion.
* `unbounded_no_decoder`: a source with duplicate-free lists longer than every
  natural bound cannot have a lossless encoding covered by one fixed finite
  host list. The arbitrarily-large-samples property is an explicit hypothesis;
  there is no formal Turing-machine definition or Doom-state enumeration here.
* `iterate f 0 x = x`; `iterate f (n+1) x = f (iterate f n x)`.
  `iterate_injective` shows every fixed iterate of an injective function is
  injective. Here reversibility is used only through injectivity; a two-sided
  inverse would be sufficient, but no inverse for Doom is claimed.
* `fixed_clock_injective`: for guest `g : A -> A`, host `h : B -> B`, injective
  `e : A -> B`, and one fixed `k : Nat`, if `h` is injective and
  `iterate h k (e x) = e (g x)` for **all** `x`, then `g` is injective.
  `collision_no_fixed_clock` excludes that exact equation when `g` has a
  witnessed collision. It holds also for `k=0`; no positive-clock assumption
  is needed. It does not require a finite host.

## Direction and quantifiers matter

The encoding direction above is **guest into host**. Encoding arbitrarily many
Turing configurations injectively into one fixed finite closed Doom state space
is obstructed, conditional on those definitions and bounds. This does NOT
obstruct encoding a finite Doom transition system into an unbounded machine.

A strong existential statement of the latter form, e.g. existence of a universal
machine `U`, injective `E : DoomState -> UConfig`, and a clock with
`U^k(E(s)) = E(DoomStep(s))`, is neither established nor refuted by the
finite-capacity result. If a proposed `U` is injective and the proposed
`DoomStep` has an actual full-state collision, the fixed-clock theorem excludes
that *particular exact reversible embedding*, not every universal machine.
Neither of those premises is proved for the C program. We do not replace a
strong existential definition with its opposite direction and claim refutation.

The results do not rule out families of larger finite boards or WADs indexed
by a time/space bound, bounded computation, noninjective observations, restricted
reachable subsets, variable-time encodings, or reversible simulation that retains
history. In particular `decode(h^k(e x)) = g x` is weaker than the exact equation
above: history can remain in the host. General computability universality with
input/output decoding does not automatically require the statewise injection
assumed by these obstruction lemmas.

## Checked bounded fallback (`substrate/utm_proof.lean`)

`rule110` has Wolfram order `111,110,101,100,011,010,001,000`, with outputs
`0,1,1,0,1,1,1,0`. All eight cases agree with `ruleByCases`.
`step` updates a fixed-length list synchronously, treating both exterior neighbors
as false anew at each step; it is neither a ring nor an infinite-tape semantics.
`step_length` proves width preservation. `trace n row` returns the initial row
and `n` successors; `trace_length` proves length `n+1`. `bounded_trace` checks
width 7 and four updates of `0001000`: `0011000`, `0111000`, `1101000`, `1111000`.
This boundary convention is explicit; no unbounded-domain equivalence is proved.

`conditional_composition` composes two assumed one-step commuting diagrams.
It asserts neither existence of their encodings nor their computability,
injectivity, clock bounds, or implementation by C/WAD data.

## Trust and unresolved obligations

Both files import only `Init` from the pinned Lean distribution, with no mathlib,
Lake dependencies, custom axioms, admitted goals, or native-decision proofs.
The finite-list capacity proofs use core classical/list lemmas and their ordinary
foundation dependencies (`propext`, `Classical.choice`, `Quot.sound`); these are
reported, not disguised as newly proved axioms. Collision/clock algebra and the
Rule110 truth table/trace have no axiom dependencies in the printed audit.

Blocked research obligations: a concrete UTM/WAD construction; unbounded memory
semantics or a uniform resource-indexed construction; a valid input compiler and
output decoder; initialization and invariant proofs; clock and halt detection;
formal C semantics, source/binary refinement and I/O closure. See
[../substrate/utm_spec.md](../substrate/utm_spec.md) and
[lean_validation.md](lean_validation.md). No native WAD computation is claimed.
