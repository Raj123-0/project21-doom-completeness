"""Hash the staged publication tree, excluding this manifest itself.

Run after git add, then git add log/artifact_hashes.json. Hashes describe Git's
canonical bytes (text LF), so clone with .gitattributes or verify git blobs.
"""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
manifest = {}
for name in names:
    if not name or name == 'log/artifact_hashes.json':
        continue
    data = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
    manifest[name] = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(ROOT/'log/artifact_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Hashed',len(manifest),'staged publication files')
