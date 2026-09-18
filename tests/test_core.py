import struct
import pytest
from doomc.lmp import Demo, Ticcmd, read_demo, savegame_button
from doomc.mapbuild import MapBuilder, Sector
from doomc.rule110 import cell, trace
from doomc.savegame import parse_savegame
from doomc.__main__ import compile_spec


def test_demo_independent_known_bytes():
    d = Demo(tics=[Ticcmd(25, -3, -256, 130)])
    assert d.to_bytes() == bytes([109,2,1,1,0,0,0,0,0,1,0,0,0,25,253,255,130,128])
    assert read_demo(d.to_bytes()).tics == d.tics
    assert [savegame_button(i) for i in range(8)] == [130,134,138,142,146,150,154,158]
    with pytest.raises(ValueError):
        Ticcmd(forwardmove=-128).bytes()
    with pytest.raises(ValueError):
        savegame_button(8)
    with pytest.raises(ValueError):
        savegame_button(-1)


def test_rule_table():
    assert [cell(i>>2, (i>>1)&1, i&1) for i in range(8)] == [0,1,1,1,0,1,1,0]
    assert trace([0,0,0,1], 2) == [[0,0,0,1],[0,0,1,1],[0,1,1,1]]


@pytest.mark.parametrize("n", [1,2,4,8,16,32])
def test_scaling(tmp_path, n):
    spec = {"system":"rule110", "boundary":"periodic", "initial":[0]*(n-1)+[1], "steps":n-1}
    out = tmp_path / "trace.wad"
    meta = compile_spec(spec, out)
    first = out.read_bytes()
    compile_spec(spec, out)
    assert first == out.read_bytes()
    assert len(meta["rows"]) == n
    assert len(meta["mapping"]) == n*n


def test_bound():
    with pytest.raises(ValueError):
        trace([1]*64, 63)


def test_builder_keeps_specials():
    m = MapBuilder()
    m.add_sector(Sector())
    m.add_rect(0,0,128,128,0)
    m.add_rect(128,0,256,128,0)
    m.set_line_special(128,0,128,128,92,1)
    a = m.build_lumps()
    assert a == m.build_lumps()
    assert any(s[3:5] == (92,1) for s in struct.iter_unpack('<7h', dict(a)['LINEDEFS']))


def test_save_strided_fingerprints():
    header = bytes(24) + b'version 109'.ljust(16,b'\0') + bytes([2,1,1,1,0,0,0,0,0,36])
    fp = [(111,9,192,0,101), (111,9,80,0,102)]
    world = b''.join(struct.pack('<2h5H', h,128,*f) for h,f in zip([0,24],fp))
    saved = parse_savegame(header + bytes(302) + world + b'\x1d', fp)
    assert saved.floorheights == [0,24]
    assert saved.leveltime == 36
