"""JSON -> static Rule 110 trace gallery PWAD. No native transition claim."""
import argparse
import json
from pathlib import Path
from .mapbuild import MapBuilder, Sector
from .wadfile import write_wad
from .lmp import Demo, Ticcmd, savegame_button
from .rule110 import trace


def compile_spec(spec, output):
    if set(spec) != {"system", "boundary", "initial", "steps"}:
        raise ValueError("required keys: system, boundary, initial, steps")
    if spec["system"] != "rule110" or spec["boundary"] != "periodic":
        raise ValueError("only periodic Rule 110 trace visualization is supported")
    rows = trace(spec["initial"], spec["steps"])
    width = len(rows[0])
    m = MapBuilder()
    mapping = []
    # Separate light levels make precomputed bits visible; all floors walkable.
    for y in range(len(rows) + 1):
        for x in range(width + 1):
            bit = rows[y-1][x-1] if x and y else None
            sector = m.add_sector(Sector(lightlevel=224 if bit != 0 else 80, tag=1+y*(width+1)+x))
            m.add_rect(x*128, y*128, (x+1)*128, (y+1)*128, sector)
            if bit is not None:
                mapping.append({"generation": y-1, "cell": x-1, "bit": bit, "sector": sector})
    m.add_thing(64, 64, 0, 1)
    # Player can exit using the east wall of the entrance corridor.
    m.set_line_special((width+1)*128, 0, (width+1)*128, 128, 11, 0)
    lumps = m.build_lumps("E1M1")
    metadata = {"claim": "static precomputed trace, NOT UTM or native simulation",
                "boundary": "periodic", "rows": rows, "mapping": mapping,
                "geometry": m.geometry_report}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_wad(str(output), lumps + [("DOOMC", json.dumps(metadata, sort_keys=True).encode())])
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    # Hand-authored input stream, subsequently checked by actual engine playback.
    tics = [Ticcmd(forwardmove=25) for _ in range(70)]
    tics += [Ticcmd(angleturn=512) for _ in range(64)]
    tics += [Ticcmd() for _ in range(35)]
    tics += [Ticcmd(buttons=savegame_button(0)), Ticcmd(), Ticcmd()]
    Demo(tics=tics).write(str(output.with_suffix(".lmp")))
    return metadata


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("spec", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = compile_spec(json.loads(a.spec.read_text()), a.output)
    print(json.dumps(result["geometry"], indent=2))


if __name__ == "__main__":
    main()
