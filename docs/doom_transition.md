# Doom transition: source reading, model, and limits

## Evidence pinned to an actual checkout

Repository: <https://github.com/chocolate-doom/chocolate-doom>.
`git -C refs/chocolate-doom rev-parse HEAD` returned
`895f581c5d91497bdda0516612da803fe5843e28`.
`git -C refs/chocolate-doom status --porcelain -- src/doom/g_game.c src/doom/p_tick.c`
returned no changes. At recon time the workspace root was not a Git repository;
this is the **reference checkout's** commit, not the research artifacts' commit.
Playback uses the separate official Chocolate Doom 3.1.1 Windows release, not a
build of the newer inspected commit. Both executable and IWAD hashes are in
`log/engine_verification.json`. Source observations are not binary refinement.
The following citations are immutable commit URLs, not links to moving `master`.

* [G_Ticker, g_game.c L910-L1081](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/g_game.c#L910-L1081):
  reborns first (916-919); pending game actions are processed in a loop
  (922-958); player commands are copied from `netcmds`, possibly overwritten
  by demo playback and passed through recording (962-975); special buttons
  can toggle pause or request saving (1017-1048). Dispatch at 1059-1080 calls
  `P_Ticker` plus status/automap/HUD tickers only in `GS_LEVEL`; other states
  have different tickers. One call is not unconditionally one physics update.
* [P_Ticker, p_tick.c L125-L153](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/p_tick.c#L125-L153):
  pause and specified menu conditions return early; otherwise active players
  think, then thinkers, specials and respawn specials update, then `leveltime++`.
* [Thinker operations, p_tick.c L46-L117](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/p_tick.c#L46-L117):
  a circular doubly linked list, tail insertion, lazy removal marked by
  `(actionf_v)(-1)`, eventual unlink/free, and ordered callback execution.
  This is not synchronous cellular-automaton updating.
* [Level setup, g_game.c L695-L720](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/g_game.c#L695-L720):
  calls `P_SetupLevel` and clears command-building state. A WAD is setup data;
  no UTM gadget implementation follows from this call.
* [Random reset, g_game.c L1891-L1926](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/g_game.c#L1891-L1926):
  `M_ClearRandom` is called during new-game initialization. Random-generator
  state still belongs in any sufficient transition state; this call alone
  does not prove determinism of the whole program.
* [Demo I/O, g_game.c L1980-L2085](https://github.com/chocolate-doom/chocolate-doom/blob/895f581c5d91497bdda0516612da803fe5843e28/src/doom/g_game.c#L1980-L2085):
  playback consumes movement, angle and button bytes, with a longtics variant;
  recording reads its quantized command back. The buffer can grow when the
  vanilla demo limit is disabled. A demo is an external command stream, not
  evidence that its producer's computation occurred inside Doom.

## Proposed transition model (not a formal C semantics)

Fix source revision, binary/compiler/ABI, compatibility settings, WAD bytes,
launch parameters, and an environment policy. Let `S` contain every mutable
component needed for a tic-boundary continuation: relevant globals and statics,
players and commands, map objects/sectors, ordered thinkers and heap/allocator
state, RNG indices, pending actions, timing counters, demo buffers/cursors,
and relevant I/O state. This is a requirements list, not a proved minimal or
complete C-state record. Screenshots and player coordinates alone are not `S`.

A useful specification is `delta : S -> I -> Outcome S`, where `I` exposes
commands and any remaining environment effects. `Outcome` distinguishes a
completed boundary, termination and fault. Nontermination requires a partial
semantics or a separate bounded execution fuel; it is not proved absent.
Do not silently turn undefined C behavior, allocation failure, or a nonterminating
callback into a normal tic. The action loop and callback callees need separate
analysis. Only the cited dispatch/thinker code has been inspected for this model;
there is no verified call-graph closure or C-to-Lean refinement.

To obtain the total autonomous `S -> S` used in the abstract lemmas, one must
supply a deterministic closure of all inputs, prove or explicitly specify error
handling, and account for the controller state. A finite prerecorded controller
can be included with its cursor and end behavior. An arbitrary infinite stream
or unbounded external controller is NOT a finite closed state. Variable-size
heaps, files and demos also need bounds before finite-state reasoning applies.
No concrete bound on Doom states is established here.

Mechanizing this complete C semantics layer in Lean 4 to bridge the gap between
the abstract transition and actual Chocolate Doom binary behavior was determined
to be computationally infeasible and is documented as a blocked workstream.

## Exact definitions and scope

See [definitions_limits.md](definitions_limits.md) for quantifiers and theorem
mapping. Lean proves abstract capacity/collision and fixed-clock statements,
plus a finite Rule110 calculation. None proves this `delta` implements Rule110,
that Doom is reversible, that any particular C assignment yields a collision
of full machine states, or that a WAD implements a universal machine. Source
reading is evidence for a proposed model, not a proof of that model.
