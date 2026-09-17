"""Minimal, dependency-free Doom WAD (IWAD/PWAD) container reader/writer.

Format reference: Doom WAD file format (header: 'PWAD'/'IWAD', int32 numlumps,
int32 infotableofs; each lump: int32 filepos, int32 size, char[8] name).

We write uncompressed PWADs only, and we read enough structure to write tests
that round-trip a generated WAD (reviewer-2 insurance: the writer is checked
against its own reader, and the WAD is separately loaded by Chocolate Doom).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List, Tuple

WAD_MAGIC = b"PWAD"


@dataclass
class Lump:
    name: str
    data: bytes

    def __post_init__(self) -> None:
        raw = self.name.encode("ascii")
        if len(raw) > 8:
            raise ValueError(f"lump name too long: {self.name!r}")
        self.name = raw.decode("ascii")


def _pad_name(name: str) -> bytes:
    raw = name.encode("ascii")
    if len(raw) > 8:
        raise ValueError(f"lump name too long: {name!r}")
    return raw + b"\0" * (8 - len(raw))


def write_wad(path: str, lumps: List[Tuple[str, bytes]], magic: bytes = WAD_MAGIC) -> None:
    """Write lumps to a WAD file, in the order given."""
    header_size = 12
    directory: List[Tuple[int, int, bytes]] = []
    offset = header_size
    body = bytearray()
    for name, data in lumps:
        body += data
        directory.append((offset, len(data), _pad_name(name)))
        offset += len(data)
    # Directory follows the lump data.
    dir_bytes = bytearray()
    for pos, size, padded in directory:
        dir_bytes += struct.pack("<ii", pos, size) + padded
    with open(path, "wb") as fh:
        fh.write(magic + struct.pack("<ii", len(lumps), offset))
        fh.write(bytes(body))
        fh.write(bytes(dir_bytes))


def read_wad(path: str) -> Dict[str, bytes]:
    """Read a WAD into an ordered dict name -> data (last lump of a name wins)."""
    with open(path, "rb") as fh:
        blob = fh.read()
    magic = blob[:4]
    if magic not in (b"IWAD", b"PWAD"):
        raise ValueError(f"not a WAD file: magic={magic!r}")
    numlumps, infotableofs = struct.unpack_from("<ii", blob, 4)
    out: Dict[str, bytes] = {}
    for i in range(numlumps):
        pos, size = struct.unpack_from("<ii", blob, infotableofs + 16 * i)
        name = blob[infotableofs + 16 * i + 8 : infotableofs + 16 * i + 16]
        out[name.rstrip(b"\0").decode("ascii").upper()] = blob[pos : pos + size]
    return out


def list_lumps(path: str) -> List[Tuple[str, int]]:
    with open(path, "rb") as fh:
        blob = fh.read()
    numlumps, infotableofs = struct.unpack_from("<ii", blob, 4)
    out = []
    for i in range(numlumps):
        pos, size = struct.unpack_from("<ii", blob, infotableofs + 16 * i)
        name = blob[infotableofs + 16 * i + 8 : infotableofs + 16 * i + 16]
        out.append((name.rstrip(b"\0").decode("ascii"), size))
    return out