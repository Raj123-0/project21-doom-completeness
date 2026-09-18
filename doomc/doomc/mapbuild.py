"""Structured Doom map generation: rectangular tilings -> vanilla MAP lumps.

Design constraints (deliberate, to keep the generator verifiable):

* The map is a tiling of axis-aligned rectangles ("rects").  Each rect belongs
  to exactly one sector.  Because every rect is axis aligned and the tiling is
  a grid partition, a guillotine (no-split) BSP always exists, and we build it
  by recursive bisection instead of a general node builder.  No seg is ever
  split; the generator refuses layouts where no guillotine cut exists.
* Vertex winding: each rect contributes its 4 edges clockwise (viewed with +y
  up), so the rect interior is on the *right* (side 0 of P_PointOnLineSide,
  src/doom/p_map.c) of every edge.  A shared edge appears twice, in opposite
  directions, and merges into one two-sided linedef whose front sector is the
  rect on the right of the linedef direction.
* Segs are emitted per rect (4 per rect), so subsector membership is exact.

Format references: src/doom/p_setup.c (P_LoadVertexes .. P_LoadBlockMap).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .wadfile import write_wad

# linedef flags (doomdef.h / r_defs.h)
ML_BLOCKING = 1
ML_BLOCKMONSTERS = 2
ML_TWOSIDED = 4
ML_BLOCKSOUND = 64

NF_SUBSECTOR = 0x8000

FRACUNIT = 1 << 16


@dataclass(frozen=True)
class Sector:
    floorheight: int = 0
    ceilingheight: int = 128
    floorpic: str = "FLOOR4_8"
    ceilingpic: str = "CEIL3_5"
    lightlevel: int = 192
    special: int = 0
    tag: int = 0


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int
    sector: int

    def __post_init__(self) -> None:
        if self.x0 >= self.x1 or self.y0 >= self.y1:
            raise ValueError(f"degenerate rect: {self}")
        for v in (self.x0, self.y0, self.x1, self.y1):
            if not -32768 <= v <= 32767:
                raise ValueError(f"vertex out of int16 range: {v}")


@dataclass(frozen=True)
class Thing:
    x: int
    y: int
    angle: int
    type: int
    options: int = 7  # easy|medium|hard (bits 0..2); bit3=ambush, bit4=multiplayer only


def _shorts(values: Sequence[int], name: str = "") -> bytes:
    return struct.pack("<" + "h" * len(values), *values)


def doom_side_pn(x: int, y: int, sx: int, sy: int, dx: int, dy: int) -> int:
    """P_PointOnLineSide for the infinite line through (sx,sy), direction (dx,dy).

    Mirrors src/doom/p_map.c P_PointOnLineSide: 0 = right-hand (front) side.
    """
    if dx == 0:
        if x <= sx:
            return 1 if dy > 0 else 0
        return 1 if dy < 0 else 0
    if dy == 0:
        if y <= sy:
            return 1 if dx < 0 else 0
        return 1 if dx > 0 else 0
    px = x - sx
    py = y - sy
    return 0 if py * dx < dy * px else 1


class MapBuilder:
    def __init__(self) -> None:
        self.sectors: List[Sector] = []
        self.rects: List[Rect] = []
        self.things: List[Thing] = []
        self.line_specials: Dict[frozenset, Tuple[int, int]] = {}
        self.geometry_report: Dict[str, int] = {}

    # -- construction -----------------------------------------------------
    def set_line_special(
        self, x1: int, y1: int, x2: int, y2: int, special: int, tag: int
    ) -> None:
        """Attach a linedef special + tag to the two-sided line between two vertices."""
        self.line_specials[frozenset({(int(x1), int(y1)), (int(x2), int(y2))})] = (
            int(special),
            int(tag),
        )
    def add_sector(self, sector: Sector) -> int:
        self.sectors.append(sector)
        return len(self.sectors) - 1

    def add_rect(self, x0: int, y0: int, x1: int, y1: int, sector: int) -> None:
        self.rects.append(Rect(int(x0), int(y0), int(x1), int(y1), sector))

    def add_thing(self, x: int, y: int, angle: int, type_: int, options: int = 7) -> None:
        self.things.append(Thing(int(x), int(y), int(angle), int(type_), int(options)))

    # -- derived structures ----------------------------------------------
    def _rect_edges(self, r: Rect) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """4 directed edges, clockwise: interior on the right of each edge."""
        bl = (r.x0, r.y0)
        br = (r.x1, r.y0)
        tr = (r.x1, r.y1)
        tl = (r.x0, r.y1)
        return [(tl, tr), (tr, br), (br, bl), (bl, tl)]

    def validate(self) -> None:
        n = len(self.rects)
        for i in range(n):
            a = self.rects[i]
            if a.sector < 0 or a.sector >= len(self.sectors):
                raise ValueError(f"rect {i} refers to unknown sector {a.sector}")
            for j in range(i + 1, n):
                b = self.rects[j]
                if a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1:
                    raise ValueError(f"rects overlap: {a} vs {b}")

    def _vertices(self) -> Tuple[List[Tuple[int, int]], Dict[Tuple[int, int], int]]:
        verts: List[Tuple[int, int]] = []
        index: Dict[Tuple[int, int], int] = {}
        for r in self.rects:
            for v in ((r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)):
                if v not in index:
                    index[v] = len(verts)
                    verts.append(v)
        return verts, index

    def _linedefs(self, vindex: Dict[Tuple[int, int], int]) -> List[dict]:
        """Merge directed edges into linedefs (two-sided pairs + one-sided walls)."""
        directed: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[int]] = {}
        for ri, r in enumerate(self.rects):
            for (v1, v2) in self._rect_edges(r):
                directed.setdefault((v1, v2), []).append(ri)

        used: set = set()
        linedefs: List[dict] = []
        for (v1, v2), owners in directed.items():
            if (v1, v2) in used:
                continue
            used.add((v1, v2))
            back_owners = directed.get((v2, v1), [])
            front_rect = owners[0]
            if back_owners:
                used.add((v2, v1))
                linedefs.append(
                    dict(
                        v1=v1,
                        v2=v2,
                        front_rect=front_rect,
                        back_rect=back_owners[0],
                        flags=ML_TWOSIDED,
                    )
                )
            else:
                linedefs.append(
                    dict(
                        v1=v1,
                        v2=v2,
                        front_rect=front_rect,
                        back_rect=None,
                        flags=ML_BLOCKING | ML_BLOCKSOUND,
                    )
                )
        return linedefs

    def _apply_specials(self, linedefs: List[dict]) -> None:
        for ld in linedefs:
            key = frozenset({ld["v1"], ld["v2"]})
            special, tag = self.line_specials.get(key, (0, 0))
            ld["special"] = special
            ld["tag"] = tag

    def build_lumps(self, mapname: str = "E1M1") -> List[Tuple[str, bytes]]:
        self.validate()
        verts, vindex = self._vertices()
        linedefs = self._linedefs(vindex)
        self._apply_specials(linedefs)
        missing = set(self.line_specials) - {
            frozenset({ld["v1"], ld["v2"]}) for ld in linedefs
        }
        if missing:
            raise ValueError(f"line specials attached to non-existent edges: {missing}")

        # --- sidedefs -----------------------------------------------------
        sidedefs: List[dict] = []
        for ld in linedefs:
            ld["side_indices"] = []
            for rect_i in (ld["front_rect"], ld["back_rect"]):
                if rect_i is None:
                    ld["side_indices"].append(-1)
                    continue
                sidedefs.append(
                    dict(xoff=0, yoff=0, top="STARTAN3", bot="STARTAN3",
                         mid="STARTAN3" if ld["back_rect"] is None else "-",
                         sector=self.rects[rect_i].sector)
                )
                ld["side_indices"].append(len(sidedefs) - 1)

        # --- segs: one per (rect, edge) -----------------------------------
        segs_by_rect: List[List[dict]] = [[] for _ in self.rects]
        for li, ld in enumerate(linedefs):
            for rect_i in (ld["front_rect"], ld["back_rect"]):
                if rect_i is None:
                    continue
                rect = self.rects[rect_i]
                match = None
                for (a, b) in self._rect_edges(rect):
                    if {a, b} == {ld["v1"], ld["v2"]}:
                        match = (a, b)
                        break
                assert match is not None, "rect edge must back its linedef"
                side = 0 if rect_i == ld["front_rect"] else 1
                segs_by_rect[rect_i].append(
                    dict(v1=vindex[match[0]], v2=vindex[match[1]], linedef=li, side=side)
                )

        # --- subsectors: one per rect, contiguous seg runs -----------------
        subsectors: List[dict] = []
        ordered_segs: List[dict] = []
        for ri, r in enumerate(self.rects):
            first = len(ordered_segs)
            ordered_segs.extend(segs_by_rect[ri])
            subsectors.append(
                dict(numsegs=len(segs_by_rect[ri]), firstseg=first, sector=r.sector)
            )

        # --- BSP by guillotine bisection -----------------------------------
        nodes: List[dict] = []

        def rect_bbox(ri: int) -> Tuple[int, int, int, int]:
            r = self.rects[ri]
            return (r.y1, r.y0, r.x0, r.x1)  # BOXTOP, BOXBOTTOM, BOXLEFT, BOXRIGHT

        def find_cut(group: Sequence[int]):
            cands = []
            xs = sorted({self.rects[i].x0 for i in group} | {self.rects[i].x1 for i in group})
            ys = sorted({self.rects[i].y0 for i in group} | {self.rects[i].y1 for i in group})
            for pos in xs:
                if all(self.rects[i].x1 <= pos or self.rects[i].x0 >= pos for i in group):
                    a = [i for i in group if self.rects[i].x0 >= pos]
                    b = [i for i in group if self.rects[i].x1 <= pos]
                    if a and b:
                        cands.append((abs(len(a) - len(b)), 0, pos, a, b))
            for pos in ys:
                if all(self.rects[i].y1 <= pos or self.rects[i].y0 >= pos for i in group):
                    a = [i for i in group if self.rects[i].y1 <= pos]
                    b = [i for i in group if self.rects[i].y0 >= pos]
                    if a and b:
                        cands.append((abs(len(a) - len(b)), 1, pos, a, b))
            if not cands:
                return None
            cands.sort(key=lambda c: c[0])
            _, axis, pos, a, b = cands[0]
            if axis == 0:  # vertical splitter, direction (0,1): side 0 is +x
                return (pos, 0, 0, 1), a, b
            # horizontal splitter, direction (1,0): side 0 is -y
            return (0, pos, 1, 0), a, b

        def subtree_bbox(child: int) -> Tuple[int, int, int, int]:
            if child & NF_SUBSECTOR:
                return rect_bbox(child & ~NF_SUBSECTOR)
            a, b = nodes[child]["bbox0"], nodes[child]["bbox1"]
            return (max(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]))

        def build(group: Sequence[int]) -> int:
            group = list(group)
            if len(group) == 1:
                return NF_SUBSECTOR | group[0]
            cut = find_cut(group)
            if cut is None:
                raise ValueError("layout is not guillotine-splittable")
            splitter, c0, c1 = cut
            sx, sy, dx, dy = splitter
            for i in c0:
                r = self.rects[i]
                if doom_side_pn((r.x0+r.x1)/2, (r.y0+r.y1)/2, sx, sy, dx, dy) != 0:
                    raise AssertionError("c0 must lie on side 0 of the splitter")
            for i in c1:
                r = self.rects[i]
                if doom_side_pn((r.x0+r.x1)/2, (r.y0+r.y1)/2, sx, sy, dx, dy) != 1:
                    raise AssertionError("c1 must lie on side 1 of the splitter")
            child0 = build(c0)
            child1 = build(c1)
            nodes.append(
                dict(
                    x=sx, y=sy, dx=dx, dy=dy,
                    bbox0=subtree_bbox(child0), bbox1=subtree_bbox(child1),
                    children=(child0, child1),
                )
            )
            return len(nodes) - 1

        if len(self.rects) < 2:
            raise ValueError("need at least 2 rects: the engine requires NODES")
        build(list(range(len(self.rects))))

        # --- blockmap: conservative bbox insertion -------------------------
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        xorigin = min(xs) - 8
        yorigin = min(ys) - 8
        xblocks = (max(xs) + 8 - xorigin + 127) // 128
        yblocks = (max(ys) + 8 - yorigin + 127) // 128
        blocks: List[List[int]] = [[] for _ in range(xblocks * yblocks)]
        for li, ld in enumerate(linedefs):
            x0, y0 = verts[vindex[ld["v1"]]]
            x1, y1 = verts[vindex[ld["v2"]]]
            bx0 = max(0, (min(x0, x1) - xorigin) // 128)
            bx1 = min(xblocks - 1, (max(x0, x1) - xorigin) // 128)
            by0 = max(0, (min(y0, y1) - yorigin) // 128)
            by1 = min(yblocks - 1, (max(y0, y1) - yorigin) // 128)
            for by in range(by0, by1 + 1):
                for bx in range(bx0, bx1 + 1):
                    blocks[by * xblocks + bx].append(li)

        # --- serialize -----------------------------------------------------
        things = b"".join(
            _shorts([t.x, t.y, t.angle, t.type, t.options]) for t in self.things
        )
        linedef_bytes = b"".join(
            _shorts([vindex[ld["v1"]], vindex[ld["v2"]], ld["flags"], ld["special"],
                     ld["tag"], ld["side_indices"][0], ld["side_indices"][1]])
            for ld in linedefs
        )
        sidedef_bytes = b"".join(
            _shorts([s["xoff"], s["yoff"]])
            + s["top"].encode("ascii").ljust(8, b"\0")
            + s["bot"].encode("ascii").ljust(8, b"\0")
            + s["mid"].encode("ascii").ljust(8, b"\0")
            + _shorts([s["sector"]])
            for s in sidedefs
        )
        vertex_bytes = b"".join(_shorts([x, y]) for (x, y) in verts)
        def seg_angle(s):
            a, b = verts[s["v1"]], verts[s["v2"]]
            return {(1, 0): 0, (0, 1): 16384, (-1, 0): -32768, (0, -1): -16384}[
                ((b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1]))]

        seg_bytes = b"".join(
            _shorts([s["v1"], s["v2"], seg_angle(s), s["linedef"], s["side"], 0])
            for s in ordered_segs
        )
        ssector_bytes = b"".join(
            _shorts([s["numsegs"], s["firstseg"]]) for s in subsectors
        )
        node_bytes = b"".join(
            _shorts([n["x"], n["y"], n["dx"], n["dy"], *n["bbox0"], *n["bbox1"]])
            + struct.pack("<HH", n["children"][0], n["children"][1])
            for n in nodes
        )
        sector_bytes = b"".join(
            _shorts([s.floorheight, s.ceilingheight])
            + s.floorpic.encode("ascii").ljust(8, b"\0")
            + s.ceilingpic.encode("ascii").ljust(8, b"\0")
            + _shorts([s.lightlevel, s.special, s.tag])
            for s in self.sectors
        )
        reject_bytes = bytes((len(self.sectors) * len(self.sectors) + 7) // 8)

        offsets: List[int] = []
        cur = 4 + len(blocks)
        for blk in blocks:
            offsets.append(cur)
            cur += len(blk) + 2
        if cur > 0xFFFF:
            raise ValueError("blockmap too large for the 16-bit vanilla format")

        def gen_blocklist():
            for blk in blocks:
                yield 0
                yield from blk
                yield 0xFFFF

        blocklist = list(gen_blocklist())
        blockmap_bytes = (
            _shorts([xorigin, yorigin, xblocks, yblocks])
            + struct.pack(f"<{len(offsets)}H", *offsets)
            + struct.pack(f"<{len(blocklist)}H", *blocklist)
        )

        self._lumps = [
            (mapname, b""),
            ("THINGS", things),
            ("LINEDEFS", linedef_bytes),
            ("SIDEDEFS", sidedef_bytes),
            ("VERTEXES", vertex_bytes),
            ("SEGS", seg_bytes),
            ("SSECTORS", ssector_bytes),
            ("NODES", node_bytes),
            ("SECTORS", sector_bytes),
            ("REJECT", reject_bytes),
            ("BLOCKMAP", blockmap_bytes),
        ]
        self.geometry_report = dict(
            rects=len(self.rects),
            sectors=len(self.sectors),
            linedefs=len(linedefs),
            sidedefs=len(sidedefs),
            segs=len(ordered_segs),
            subsectors=len(subsectors),
            nodes=len(nodes),
            vertices=len(verts),
            blockmap_blocks=xblocks * yblocks,
            wad_bytes=sum(len(d) for _, d in self._lumps),
        )
        return self._lumps

    def write(self, path: str, mapname: str = "E1M1") -> Dict[str, int]:
        lumps = self.build_lumps(mapname)
        write_wad(path, lumps)
        return dict(self.geometry_report)
