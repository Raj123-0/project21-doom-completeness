"""Compiler-only bounded scaling; no native computation benchmark implied."""
import json
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'doomc'))
from doomc.__main__ import compile_spec

results = []
with tempfile.TemporaryDirectory() as tmp:
    for n in [1,2,4,8,16,32,64]:
        tracemalloc.start()
        start = time.perf_counter()
        try:
            p = Path(tmp) / 'bench.wad'
            meta = compile_spec({'system':'rule110','boundary':'periodic',
                                 'initial':[0]*(n-1)+[1],'steps':n-1},p)
            entry = {'N':n,'wad_bytes':p.stat().st_size,'sectors':meta['geometry']['sectors'],
                     'tics_per_simulated_step':None,'engine_tested':False}
        except ValueError as exc:
            entry = {'N':n,'rejected':str(exc),'meaning':'compiler policy, not engine limit'}
        entry['compile_seconds'] = time.perf_counter()-start
        entry['python_peak_bytes'] = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        results.append(entry)
(ROOT/'log').mkdir(exist_ok=True)
(ROOT/'log/benchmarks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
