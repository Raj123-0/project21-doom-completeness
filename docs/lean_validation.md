# Lean validation record

Pinned toolchain file: `lean-toolchain` -> `leanprover/lean4:v4.34.0`
Checked with: `Lean (version 4.34.0, x86_64-w64-windows-gnu, commit 293d5d0c0c3f3dded4688b3ccd6a33939ac5102b, Release)`
Local binary: `C:\Users\davea\.elan\bin\lean.exe` (installed via elan for
`leanprover/lean4:stable`, which resolved to 4.34.0). Last run: 2026-09-17.

## Commands and exit codes (PowerShell, from repo root)

```
PS> lean proofs\DoomComplete.lean ; $LASTEXITCODE  -> 0
PS> lean substrate\utm_proof.lean ; $LASTEXITCODE  -> 0
```

Both files `import Init` only. There is no Lake project, no mathlib, no package
download, no `native_decide`, no custom axioms, and no `sorry`/`admit`.

## Full captured output

`proofs/DoomComplete.lean` (all five `#print axioms` lines):

```
'DoomComplete.capacity_bound' depends on axioms: [propext, Classical.choice, Quot.sound]
'DoomComplete.finite_collision' depends on axioms: [propext, Classical.choice, Quot.sound]
'DoomComplete.unbounded_no_decoder' depends on axioms: [propext, Classical.choice, Quot.sound]
'DoomComplete.collision_no_decoder' does not depend on any axioms
'DoomComplete.collision_no_fixed_clock' does not depend on any axioms
DoomComplete exit: 0
```

`substrate/utm_proof.lean`:

```
[false, true, true, false, true, true, true, false]
[[false, false, false, true, false, false, false],
 [false, false, true, true, false, false, false],
 [false, true, true, true, false, false, false],
 [true, true, false, true, false, false, false],
 [true, true, true, true, false, false, false]]
'BoundedRule110.truth_table' does not depend on any axioms
'BoundedRule110.local_correct' does not depend on any axioms
'BoundedRule110.bounded_trace' does not depend on any axioms
'BoundedRule110.conditional_composition' does not depend on any axioms
utm_proof exit: 0
```

Notes: the three capacity results use core classical/list infrastructure and
report the standard foundation axioms; the collision/clock algebra and the
Rule110 truth table, case split, and bounded trace are axiom-free in the audit.
The `#eval` lines are supplementary executations; the stated equalities are
checked by the kernel (`decide`/`rfl`), not by `#eval`.

## Paper recompilation record

The paper is also checked as far as tooling here allows:

```
PS> cd paper
PS> pdflatex -interaction=nonstopmode -halt-on-error doom_complete.tex   (twice)
Output written on doom_complete.pdf. Both passes returned exit code 0.
(The byte size changes when source or PDF metadata changes; see the hash manifest.)
```

Toolchain: MiKTeX 25.12 pdflatex (pdfTeX 3.141592653-2.6-1.40.28), MiKTeX 25.12.
Fresh passes cross-resolve references. The compiled PDF is a static document;
typesetting it is not a computation claim. (An earlier build from a prior draft
produced the 4-page PDF recorded in `paper/latex-validation.txt`; the current
source with the final limitation and empirical sections produces a six-page PDF.)

No theorem in either file refers to Doom's C code, engine state, WAD bytes, or
this repository's Python. The bridge between the abstract lemmas and the engine
is **not mechanized**; see `definitions_limits.md` and `../substrate/utm_spec.md`.
