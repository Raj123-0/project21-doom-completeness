# Research log — Project 21 (Doom-completeness)

Entries are chronological; each records what was actually done and checked,
including negative results. No timezone or physical experiment is inferred.

## 2026-09-17 — session log

### Gate 0 — recon and formalization — DONE (partial goals)
- Cloned chocolate-doom; reference commit
  `895f581c5d91497bdda0516612da803fe5843e28`; status clean at the cited files.
- `docs/doom_transition.md`: pinned line-level evidence for G_Ticker /
  P_Ticker / thinkers; explicit statement that no formal C semantics exists.
- `docs/definitions_limits.md`: quantified definitions and theorem directions;
  the finite-capacity obstruction is stated in the unbounded-guest-into-finite-
  host direction and explicitly does not refute the existential Strong claim.
- Prior art pinned and metadata-checked: Cook 2004 (Rule110 universality),
  Neary & Woods ICALP 2006 (P-completeness), Chocolate Doom source. See
  `substrate/utm_spec.md` for what these do and do not provide.
- Engine binaries obtained from official release archives, SHA256 recorded in
  `ci/fetch_dependencies.py`; Freedoom 0.13.0 used as IWAD; no copyrighted WADs.

### Gate 1 — weak theorem — PARTIAL
- `BoundedRule110.conditional_composition` (in `substrate/utm_proof.lean`): a
  conditional composition of commuting diagrams with all premises explicit.
  Correctly labelled trivial; not presented as a result.

### Gate 2 — strong theorem attack — PARTIAL (obstructions only)
- Proved in Lean: `collision_no_decoder`, `capacity_bound`,
  `finite_no_injection`, `finite_collision`, `unbounded_no_decoder`,
  `fixed_clock_injective`, `collision_no_fixed_clock`.
- Honest outcome: these obstruct **unbounded guests in a fixed finite closed
  installation** and **exact fixed-clock reversible embedding of a colliding
  transition**. They do NOT refute the requested existential Strong definition
  (Doom into an unbounded substrate). Documented in `definitions_limits.md`.

### Gate 3 — substrate UTM — BLOCKED, negative result shipped
- No UTM constructed; no universality proof. `substrate/utm_spec.md` lists all
  missing witnesses. `utm_proof.lean` = bounded Rule110 truth table + finite
  zero-exterior trace (axiom-free audit for those parts).

### Gate 4 — compiler — SHIPPED as bounded visualization backend
- `doomc` compiles a JSON spec to a deterministic PWAD gallery of a periodic
  Rule 110 trace (width 1..32, steps 0..31; explicit rejection beyond).
  Determinism is regression-tested (`tests/test_core.py::test_scaling`).
- The trace is computed by Python before launch. **Doom does not compute it.**
- Vanilla 1.9 demo writer verified against hand-computed bytes (independent of
  the chocolate-doom source tree); BTS_SAVEGAME constants verified against
  pinned d_event.h. Demo requests an engine savegame for state readback.
- End-to-end: `ci/verify_engine.py` — two real headless Chocolate Doom 3.1.1
  runs of `wads/doom_utm.wad` + `.lmp`, 172 tics each, demo-requested save at
  leveltime 170, equal partial-world projection SHA256
  `8f5f6e247cf0bd770da72b81a4422716e08b8159dce8d4d721f97debd992800a`.
- Scaling N=1..32 compiled; N=64 rejected by backend policy. `log/benchmarks.json`.
- Negative: **no native in-engine Rule110 gadget, no WAD UTM, no formal C
  semantics.** `tics per simulated step` is not measurable: Doom executes no
  CA transition. This is stated rather than benchmarked away.

### Gate 5 — paper and publication
- `paper/doom_complete.tex`: partial report; explicit PDF-JS limitation section;
  anticipated Reviewer-2 section; compiled twice with MiKTeX (exit 0).
  PDF execution was not attempted; no PDF impossibility result is claimed.
- No video or audiovisual recording; headless evidence only.
- Public repo: see commit/push record below once created.

### Gate 6 — reality check (mandatory absurd step, kept short and self-aware)
- Fictional console transcript: `> IDDQD; IDKFA; IDCLIP; IDCLEV`.
  `error: universe console interface not supplied`. `> Esc`.
- No physical keys were pressed, no Planck-scale manipulation was possible,
  and no measurement of the universe was performed. The demo-playback hypothesis
  is a joke, not an inference. This corrects an earlier draft that described
  imaginary physical actions as observations. Status: NOT AN EXPERIMENT.

### Gate 7 — Final Session (Blocked Workstreams)
- Workstream D (Strong Existential Proof): BLOCKED / negative result. Attempted to formally prove the strong existential claim in Lean, but realized any such proof without exhibiting a fixed, computationally universal machine is a mathematical tautology (merely pulling back a transition function across an injection). Thus, the strong claim remains unproved.
- Workstream A (Native In-Engine Gadget): BLOCKED / negative result. Given the complexities of vanilla thinker scheduling and level layout constraints, a fully native, self-contained Rule 110 gadget running inside the engine loop could not be built and verified in this session.
- Workstream B (Formal C Semantics): BLOCKED / negative result. Mechanizing a sufficient abstract subset of Chocolate Doom's C execution in Lean 4 to bridge the gap to actual binary semantics proved infeasible.
- Workstream C (Python/WAD Correspondence Mechanization): BLOCKED / negative result. Mechanizing the Python compiler's behavior and the WAD format specification in Lean to prove consistency mathematically was determined to be too complex for this session.
- Workstream F (Scale and Performance Limits): BLOCKED / negative result. Without a functional native gadget, true engine limits could not be evaluated beyond the established Python compiler bounds (N=64 rejection).
- Workstream E (Enhanced Engine Verification): BLOCKED / negative result. Extracting a full engine state hash beyond the partial sector projection and certifying interactive rendering were determined to be infeasible.

### Verification summary (final state of this session)
- Lean: both files exit 0; axiom audit printed (three core-classical results,
  four axiom-free; no sorry/admit/native_decide). See `docs/lean_validation.md`.
- Python: 11 tests pass; compileall clean; deterministic regeneration verified.
- Engine: two 172-tic headless playbacks, matching partial projections; logs in
  `log/engine_verification.json`.
- Artifact SHA256s are recorded in `log/artifact_hashes.json`.
