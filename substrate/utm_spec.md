# UTM specification: BLOCKED / no constructed UTM

There is **no constructed UTM**, no universal Doom WAD, and no formal universality
proof in this project. `utm_proof.lean` is a bounded Rule110 fallback; its filename
is not a claim. It verifies the eight-entry local rule, a zero-exterior finite-row
update, length invariants, one four-step trace and a conditional algebraic
composition lemma. It imports only Lean `Init`.

## Intended claim and missing witnesses

A future native-computation result must fix the engine revision, allowed WAD
features, input channels and resource model. It must supply all of:

1. An actual substrate construction (map/lumps/gadgets with concrete layouts),
   a well-defined legal-state invariant, and independent state readout.
2. An effective, uniform program/input compiler, not an external producer of
   the computation's already-evaluated trace or outputs. Demo playback alone
   does not supply this witness.
3. A specified machine (states, alphabet, tape/configurations, total or partial
   step, halt/output convention), or a complete reduction from such a machine.
4. Initialization, local-step and composition proofs including scheduling,
   signal interference, memory access, and a stated observation/clock relation.
5. An unbounded resource idealization justified by semantics, or a uniform family
   indexed by resource bounds with proved coverage of finite computations. One
   fixed width-seven row or one fixed bounded installation is not an unbounded
   tape. A family of finite simulations must not be presented as one finite UTM.
6. A refinement from the chosen C/binary semantics to the abstract transition,
   accounting for input closure, overflow/undefined behavior, allocation, pause,
   callbacks, failure, and termination. **No formal C semantics proof exists.**
7. Effective output decoding and halt detection, with no external oracle doing
   the intended computation. Evidence must distinguish engine computation from
   compiler/controller computation.

All seven are currently unresolved. In this session, creating a purely native Rule110 gadget
implementation (1), proving the strong existential claim and mechanizing Python/WAD correspondence (3, 4),
mechanizing formal C semantics (6), and measuring engine scale limits for such a gadget (5)
were documented as explicitly blocked workstreams, remaining negative results. The abstract composition lemma
assumes both diagrams; it does not discharge any item above. The finite-capacity obstruction applies
only to the stated lossless state-encoding model, and is not a global negative universality theorem.
Exact definitions are in [../docs/definitions_limits.md](../docs/definitions_limits.md).

## What the literature does and does not provide

* Matthew Cook, **Universality in Elementary Cellular Automata**, *Complex
  Systems* **15**(1), 1–40 (2004).
  DOI: [10.25088/ComplexSystems.15.1.1](https://doi.org/10.25088/ComplexSystems.15.1.1).
  [Publisher abstract](https://www.complex-systems.com/abstracts/v15_i01_a01/).
  Cook establishes universality of Rule110 via a construction involving cyclic
  tag systems and organized backgrounds/signals. The infinite-background
  setting must not be silently replaced with a fixed zero-boundary finite row.
  The publication is a cited external result, not a Lean theorem imported here.
* Turlough Neary and Damien Woods, **P-completeness of Cellular Automaton
  Rule 110**, in *Automata, Languages and Programming*, ICALP 2006,
  LNCS **4051**, 132–143, Springer (2006).
  DOI: [10.1007/11786986_13](https://doi.org/10.1007/11786986_13).
  The publisher abstract states that predicting `t` steps of Rule110 is
  P-complete, proved through polynomial-time simulation of deterministic Turing
  machines. This improves simulation efficiency; it is not a construction in
  Doom and does not establish universality of a fixed finite board. No exact
  polynomial exponent is claimed by these artifacts.

The checked truth table matches Rule110, but matching a local Boolean function
alone does not realize Cook's global construction, its initialization/backgrounds,
its time/space requirements, or any reduction to Doom. Neither citation fills
those gaps. Metadata was checked against publisher pages (Neary/Woods also
against Crossref); no universality theorem from either paper was formalized.
