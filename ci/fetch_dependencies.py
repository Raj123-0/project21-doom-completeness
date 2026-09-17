"""Download pinned external archives, verify SHA256, extract locally. Windows."""
import hashlib
import urllib.request
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = [
    ('https://github.com/chocolate-doom/chocolate-doom/releases/download/chocolate-doom-3.1.1/chocolate-doom-3.1.1-win64.zip',
     'cdoom.zip', 'cdoom-bin', '58c34c61ae954493fce5ff01fd553898240a0de25658aa97b43ac9510c49581f'),
    ('https://github.com/freedoom/freedoom/releases/download/v0.13.0/freedoom-0.13.0.zip',
     'freedoom.zip', 'freedoom', '3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59'),
]
for url, name, dest, digest in ARCHIVES:
    path = ROOT / name
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f'SHA256 mismatch: {path}')
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            target = (ROOT / dest / info.filename).resolve()
            if not target.is_relative_to((ROOT / dest).resolve()):
                raise ValueError('archive path traversal')
        archive.extractall(ROOT / dest)
    print('verified and extracted', name, digest)
