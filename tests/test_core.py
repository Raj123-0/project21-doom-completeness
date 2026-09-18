import struct
import pytest
from doomc.lmp import Demo, Ticcmd, read_demo, savegame_button
from doomc.mapbuild import MapBuilder, Sector
from doomc.rule110 import cell, trace
from doomc.savegame import parse_savegame
from doomc.__main__ import compile_spec
from doomc.wadfile import Lump, read_wad


def test_lump_name_too_long():
    with pytest.raises(ValueError, match="lump name too long"):
        Lump('123456789', b'')

def test_demo_independent_known_bytes():
    d = Demo(tics=[Ticcmd(25, -3, -256, 130)])
    assert d.to_bytes() == bytes([109,2,1,1,0,0,0,0,0,1,0,0,0,25,253,255,130,128])
    assert read_demo(d.to_bytes()).tics == d.tics
    assert [savegame_button(i) for i in range(8)] == [130,134,138,142,146,150,154,158]
    with pytest.raises(ValueError):
        Ticcmd(forwardmove=-128).bytes()


def test_read_demo_wrong_version():
    with pytest.raises(ValueError, match="unexpected demo version 108"):
        read_demo(bytes([108]))


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


def test_wadfile_truncated(tmp_path):
    from doomc.wadfile import read_wad, list_lumps
    out = tmp_path / "trunc.wad"
    out.write_bytes(b"PWAD\x00\x00")
    with pytest.raises(ValueError, match="WAD file too small"):
        read_wad(str(out))
    with pytest.raises(ValueError, match="WAD file too small"):
        list_lumps(str(out))


def test_compile_spec_invalid_keys(tmp_path):
    out = tmp_path / "trace.wad"
    with pytest.raises(ValueError, match="required keys: system, boundary, initial, steps"):
        compile_spec({}, out)


def test_compile_spec_invalid_values(tmp_path):
    out = tmp_path / "trace.wad"
    spec = {"system": "invalid", "boundary": "periodic", "initial": [1], "steps": 1}
    with pytest.raises(ValueError, match="only periodic Rule 110 trace visualization is supported"):
        compile_spec(spec, out)

    spec2 = {"system": "rule110", "boundary": "invalid", "initial": [1], "steps": 1}
    with pytest.raises(ValueError, match="only periodic Rule 110 trace visualization is supported"):
        compile_spec(spec2, out)


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


def test_read_wad_invalid_magic(tmp_path):
    invalid_wad = tmp_path / "invalid.wad"
    invalid_wad.write_bytes(b"JWAD\x00\x00\x00\x00\x00\x00\x00\x00")
    with pytest.raises(ValueError, match="not a WAD file: magic=b'JWAD'"):
        read_wad(str(invalid_wad))


def test_parse_savegame_too_short():
    with pytest.raises(ValueError, match="savegame too short"):
        parse_savegame(b"short", [])


def test_parse_savegame_unexpected_version():
    blob = bytes(24) + b"invalid 109".ljust(16, b"\0") + bytes(10)
    with pytest.raises(ValueError, match="unexpected savegame version string"):
        parse_savegame(blob, [])


def test_read_demo_error_paths():
    d = Demo(tics=[Ticcmd(25, -3, -256, 130)])
    valid_bytes = d.to_bytes()

    # Missing DEMOMARKER (truncated)
    with pytest.raises(ValueError, match="missing marker or trailing data"):
        read_demo(valid_bytes[:-1])

    # Trailing data after DEMOMARKER
    with pytest.raises(ValueError, match="missing marker or trailing data"):
        read_demo(valid_bytes + b'\x00')
