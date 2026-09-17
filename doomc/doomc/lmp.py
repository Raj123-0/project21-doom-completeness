"""Vanilla Doom 1.9 demo (.lmp) writer.

Format (Doom 1.9 / "version 109"), as read by G_DoPlayDemo (src/doom/g_game.c:2235)
and G_ReadDemoTiccmd (src/doom/g_game.c:1980):

  header (13 bytes):
    byte  version        (109 for doom 1.9 / vanilla)
    byte  skill          (0..4)
    byte  episode        (1..4, Doom 1 only)
    byte  map            (1..9,  Doom 1 only)
    byte  deathmatch
    byte  respawn
    byte  fast
    byte  nomonsters
    byte  consoleplayer
    byte  playeringame[0..3]
  then one record per tic:
    int8  forwardmove
    int8  sidemove
    uint8 angleturn high byte (low byte is zero in version 109)
    uint8 buttons
  terminated by the demo marker 0x80 (DEMOMARKER, g_game.c:1977).

Buttons are BT_* bits (d_event.h) plus the special-button encoding
BT_SPECIAL | code, which is how a *demo* can ask the engine to write a
savegame (g_game.c:1017-1048, case BTS_SAVEGAME) -- our state readback channel.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List

DEMO_VERSION = 109
DEMOMARKER = 0x80

BT_ATTACK = 0x01
BT_USE = 0x02
BT_SPECIAL = 0x80
BT_SPECIALMASK = 0x03
BTS_PAUSE = 0x01
BTS_SAVEGAME = 0x02
BTS_SAVEMASK = 28
BTS_SAVESHIFT = 2


@dataclass
class Ticcmd:
    forwardmove: int = 0
    sidemove: int = 0
    angleturn: int = 0
    buttons: int = 0

    def bytes(self) -> bytes:
        if not -127 <= self.forwardmove <= 127 or not -128 <= self.sidemove <= 127:
            raise ValueError("movement out of range or reserved demo marker")
        if not 0 <= self.buttons <= 255:
            raise ValueError("buttons out of range")
        if self.angleturn % 256:
            raise ValueError("version 109 requires angleturn divisible by 256")
        return struct.pack("<bbBB", self.forwardmove, self.sidemove,
                           (self.angleturn >> 8) & 255, self.buttons)


def _clamp_i8(v: int) -> int:
    return max(-128, min(127, int(v)))


def savegame_button(slot: int) -> int:
    """Button byte that makes G_Ticker save the game to ``slot`` (0..7).

    g_game.c:1041: savegameslot = (buttons & BTS_SAVEMASK) >> BTS_SAVESHIFT
    """
    if not 0 <= slot <= 7:
        raise ValueError("savegame slot must be 0..7")
    return BT_SPECIAL | BTS_SAVEGAME | (slot << BTS_SAVESHIFT)


@dataclass
class Demo:
    skill: int = 2
    episode: int = 1
    map: int = 1
    deathmatch: int = 0
    respawn: int = 0
    fast: int = 0
    nomonsters: int = 0
    consoleplayer: int = 0
    playeringame: List[int] = field(default_factory=lambda: [1, 0, 0, 0])
    tics: List[Ticcmd] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        head = bytes(
            [
                DEMO_VERSION,
                self.skill,
                self.episode,
                self.map,
                self.deathmatch,
                self.respawn,
                self.fast,
                self.nomonsters,
                self.consoleplayer,
                *self.playeringame[:4],
            ]
        )
        body = b"".join(t.bytes() for t in self.tics)
        return head + body + bytes([DEMOMARKER])

    def write(self, path: str) -> None:
        with open(path, "wb") as fh:
            fh.write(self.to_bytes())


def read_demo(blob: bytes) -> Demo:
    """Parse a vanilla-format demo (used by our own test-suite)."""
    if blob[0] != DEMO_VERSION:
        raise ValueError(f"unexpected demo version {blob[0]}")
    d = Demo(
        skill=blob[1],
        episode=blob[2],
        map=blob[3],
        deathmatch=blob[4],
        respawn=blob[5],
        fast=blob[6],
        nomonsters=blob[7],
        consoleplayer=blob[8],
        playeringame=list(blob[9:13]),
    )
    i = 13
    while i < len(blob) and blob[i] != DEMOMARKER:
        fwd, side, turn, buttons = struct.unpack_from("<bbBB", blob, i)
        d.tics.append(Ticcmd(fwd, side, (turn if turn < 128 else turn - 256) << 8, buttons))
        i += 4
    if i != len(blob) - 1 or blob[i] != DEMOMARKER:
        raise ValueError("missing marker or trailing data")
    return d