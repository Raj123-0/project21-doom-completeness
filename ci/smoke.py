"""Minimal geometry and real-engine smoke test; no UTM claim."""
import json
import struct
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "doomc"))
from doomc.mapbuild import MapBuilder, Sector
from doomc.lmp import Demo, Ticcmd, savegame_button
from doomc.runner import ChocolateDoom


def build_smoke(out):
    m = MapBuilder()
    m.add_sector(Sector(tag=101))
    m.add_sector(Sector(tag=102))
    m.add_rect(0, 0, 256, 256, 0)
    m.add_rect(256, 0, 512, 256, 1)
    m.add_thing(128, 128, 0, 1)
    lumps = dict(m.build_lumps())
    assert len(lumps["LINEDEFS"]) == 7 * 14
    assert len(lumps["SIDEDEFS"]) == 8 * 30
    assert len(lumps["NODES"]) == 28
    node = struct.unpack("<12h2H", lumps["NODES"])
    assert node[:4] == (256, 0, 0, 1), node
    assert node[-2:] == (0x8001, 0x8000), node
    assert node[4:8] == (256, 0, 256, 512), node
    assert node[8:12] == (256, 0, 0, 256), node
    lines = list(struct.iter_unpack("<7h", lumps["LINEDEFS"]))
    assert sum(bool(line[2] & 4) for line in lines) == 1
    words = struct.unpack("<" + "H" * (len(lumps["BLOCKMAP"]) // 2), lumps["BLOCKMAP"])
    blocks = words[2] * words[3]
    for offset in words[4:4+blocks]:
        assert words[offset] == 0
        p = offset + 1
        while words[p] != 65535:
            assert words[p] < 7
            p += 1
    assert m.build_lumps() == list(lumps.items()), "non-deterministic builder"
    m.write(str(out / "smoke.wad"))
    Demo(tics=[Ticcmd() for _ in range(35)] +
         [Ticcmd(buttons=savegame_button(0)), Ticcmd(), Ticcmd()]).write(str(out / "smoke.lmp"))
    print(json.dumps({"geometry": m.geometry_report, "node": node, "lines": lines}, indent=2))


if __name__ == "__main__":
    out = Path(tempfile.mkdtemp(prefix="smoke-", dir=ROOT))
    build_smoke(out)
    engine = ChocolateDoom(str(ROOT / "cdoom-bin/chocolate-doom.exe"),
                           str(ROOT / "freedoom/freedoom-0.13.0/freedoom1.wad"),
                           str(out / "engine"), timeout=45)
    result = engine.run_demo(str(out / "smoke.wad"), str(out / "smoke.lmp"),
                             timedemo=True, extra=["-devparm"])
    (out / "engine.json").write_text(json.dumps(asdict(result), indent=2))
    print("ARTIFACT DIRECTORY:", out)
    print("EXIT:", result.returncode)
    print(result.stdout)
    print(result.stderr)
    print("SAVES:", result.savegames)
    assert result.savegames, "engine did not write a savegame"
