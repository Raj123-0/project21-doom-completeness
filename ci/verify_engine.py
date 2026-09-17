"""Run the shipped gallery twice; verify partial world projection, not UTM state."""
import hashlib
import json
import os
import struct
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "doomc"))
from doomc.runner import ChocolateDoom
from doomc.savegame import parse_savegame
from doomc.wadfile import list_lumps, read_wad
from doomc.lmp import read_demo


def verify():
    wad = ROOT / "wads/doom_utm.wad"
    demo = wad.with_suffix('.lmp')
    exe = Path(os.environ.get('CHOCOLATE_DOOM', ROOT / 'cdoom-bin/chocolate-doom.exe'))
    iwad = Path(os.environ.get('FREEDOOM_IWAD', ROOT / 'freedoom/freedoom-0.13.0/freedoom1.wad'))
    names = [n for n, _ in list_lumps(str(iwad))]
    first = names.index('F_START') + 1
    lumps = read_wad(str(wad))
    fps, expected = [], []
    for floor, ceil, flat, top, light, special, tag in struct.iter_unpack('<hh8s8shhh', lumps['SECTORS']):
        fps.append((names.index(flat.rstrip(b'\0').decode())-first,
                    names.index(top.rstrip(b'\0').decode())-first, light, special, tag))
        expected.append((floor,ceil,light,special,tag))
    runs = []
    for index in range(2):
        work = Path(tempfile.mkdtemp(prefix='gallery-', dir=ROOT))
        engine = ChocolateDoom(str(exe), str(iwad), str(work), timeout=60)
        result = engine.run_demo(str(wad),str(demo),timedemo=True)
        assert result.ok, result.stdout + result.stderr
        assert f'timed {len(read_demo(demo.read_bytes()).tics)} gametics' in result.stderr + result.stdout
        assert 'doomsav0.dsg' in result.savegames
        raw = Path(result.savegames['doomsav0.dsg']).read_bytes()
        saved = parse_savegame(raw, fps)
        assert saved.leveltime == 170, saved.leveltime
        actual = list(zip(saved.floorheights,saved.ceilingheights,saved.lightlevels,saved.specials,saved.tags))
        assert actual == expected
        projection = struct.pack('<I', saved.leveltime) + b''.join(struct.pack('<5h',*r) for r in actual)
        record = asdict(result)
        record['full_state_sha256'] = saved.full_hash()
        record['projection_sha256'] = hashlib.sha256(projection).hexdigest()
        record['saved_leveltime'] = saved.leveltime
        record['projection'] = 'leveltime u32; per sector floor,ceiling,light,special,tag i16 LE'
        record['note'] = 'static gallery state; not full engine state, rendering, or native computation'
        runs.append(record)
    assert runs[0]['projection_sha256'] == runs[1]['projection_sha256']
    assert runs[0]['full_state_sha256'] == runs[1]['full_state_sha256']
    log = ROOT / 'log'
    log.mkdir(exist_ok=True)
    report = {'engine_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
              'iwad_sha256':hashlib.sha256(iwad.read_bytes()).hexdigest(), 'runs':runs}
    (log / 'engine_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: two real engine playbacks, 172 tics each; full state SHA256',runs[0]['full_state_sha256'])

if __name__ == '__main__':
    verify()
