# Project 21 — Doom-completeness: a checked partial result

**No UTM was built. Strong Doom-completeness is neither proved nor refuted.**
The playable artifact is a **precomputed periodic Rule 110 trace gallery**.
Doom renders/explores it; Python computes the trace before the engine starts.
The requested filename `doom_utm.wad` is retained for compatibility, not as a claim.

## Shipped and checked

- `proofs/DoomComplete.lean`: lossless-encoding capacity obstruction and an
  exact fixed-clock reversible-host obstruction. These are abstract theorems,
  not a verified application to Chocolate Doom's C state.
- `substrate/utm_proof.lean`: Rule 110 truth table, finite zero-exterior trace,
  length lemmas, conditional simulation composition. **Not a universality proof.**
- `doomc/`: deterministic JSON-to-PWAD **visualization** backend, vanilla demo
  writer, structured map builder, and partial savegame-state observer.
- `wads/doom_utm.wad`, `.lmp`, `.json`: 8 cells by 8 generations plus corridors;
  explorable E1M1. Bright cells = 1; dark cells = 0. Walk east along the entrance
  corridor and press Use at its east wall to exit. No custom copyrighted assets.
- `log/engine_verification.json`: two real Chocolate Doom 3.1.1 runs, 172 tics
  each, with engine-written saves at leveltime 170 and equal **partial world
  projection** hashes. The demo is generated input, not a human/engine recording.
- `paper/doom_complete.tex` and the typeset `paper/doom_complete.pdf`,
  compiled with MiKTeX pdflatex: partial research report with an explicit
  PDF-JS limitation section. The PDF is static; it does not run Doom and does
  not pretend to.

No videos, screenshots, or audiovisual recordings were made. Headless engine
playback is tested; interactive appearance, audio and all viewpoints are not
certified. A successful `-nodraw` run does not prove renderer correctness.

## Reproduce on Windows (PowerShell)

Clone the repository; set `$root` to its absolute path (example below).
Python >=3.11 and Lean 4.34.0 are required. Runtime Python uses only the stdlib.
Tests require pytest. No runtime third-party Python packages are needed.

```powershell
$root = 'C:\Users\davea\OneDrive\Desktop\dooom'
Set-Location $root
python "$root\ci\fetch_dependencies.py"
$env:PYTHONPATH = "$root\doomc"
python -m doomc "$root\substrate\example.json" "$root\wads\doom_utm.wad"
python -m pytest "$root\tests" -q
lean "$root\proofs\DoomComplete.lean"
lean "$root\substrate\utm_proof.lean"
python "$root\ci\verify_engine.py"
```

Install Lean with elan using the pinned `lean-toolchain`; the local session used
`C:\Users\davea\.elan\bin\lean.exe`. CI installs the same toolchain.
Dependency fetching downloads official Chocolate Doom 3.1.1 Windows and Freedoom
0.13.0 archives and checks recorded SHA256 values. Binaries/IWADs are **not** in
this repository. Source recon used a newer commit than the tested release;
see `docs/doom_transition.md` for the distinction.

Interactive play (does not record anything):
```powershell
& "$root\cdoom-bin\chocolate-doom.exe" -iwad "$root\freedoom\freedoom-0.13.0\freedoom1.wad" -file "$root\wads\doom_utm.wad" -warp 1 1 -skill 3 -window
```
Playback (demo requests a save, so isolate the destination):
```powershell
$save = Join-Path $env:TEMP ([guid]::NewGuid().ToString())
New-Item -ItemType Directory $save | Out-Null
& "$root\cdoom-bin\chocolate-doom.exe" -iwad "$root\freedoom\freedoom-0.13.0\freedoom1.wad" -file "$root\wads\doom_utm.wad" -playdemo "$root\wads\doom_utm.lmp" -savedir $save -window
```
The automated verifier uses `-timedemo -nodraw -nosound`, SDL dummy drivers, fresh
save directories, exact tic counts and sector observations. Chocolate Doom's
normal timedemo report exits through `I_Error`, so its exit status can be -1
(4294967295 on Windows). We retain that status, not rewrite it to zero.

## What the proof does NOT say

A fixed bounded closed digital installation has finitely many distinguishable
states. It cannot losslessly host arbitrarily many configurations at once.
This concerns **unbounded guest into finite Doom**, not **Doom into unbounded
Rule 110**. The user's existential Strong statement therefore survives that
obstruction. Exact reversible simulation with a fixed clock cannot merge states
without retaining information; history/projection or a noninjective host changes
those assumptions. No minimal sufficient extension of vanilla Doom was proved.

The formal finite trace uses zero exterior; the gallery uses a periodic ring.
Only their common local truth table is formally identified. Neither is Cook's
universal global construction. Python/WAD correspondence is regression-tested,
not proved in Lean. No Doom C computability/termination theorem was mechanized.

## Bounds and scale

Compiler supports width 1..32 and steps 0..31. `ci/benchmark.py` measures
N=1,2,4,8,16,32 and the explicit rejection at 64; this is compiler policy, not an
engine impossibility limit. Sectors = (width+1)(steps+2). Trace computation is
O(width * steps); geometry generation includes quadratic validation; REJECT
storage is quadratic in sector count. Tics per **simulated** CA step are N/A:
no CA transition is executed by Doom. Only the default gallery is engine-tested.

See `docs/definitions_limits.md`, `substrate/utm_spec.md`, `log/research_log.md`
and the paper for open obligations and prior art. No arXiv/SIGBOVIK submission
has been made. MIT covers original code/docs/map geometry; external projects
retain their own licenses. Choosing Chocolate Doom does not remove Doom's
trademark or commercial WAD copyright restrictions.
