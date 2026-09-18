"""Headless Chocolate Doom driver: the artifact-verification harness.

Chocolate Doom supports ``-nodraw`` (src/doom/g_game.c:2333) plus SDL dummy
video/audio drivers, so a generated WAD and a `.lmp` can be *actually run* on
this machine with no display, no sound and no video recording.  Evidence is
textual: engine exit status, engine stdout/stderr, savegame dumps requested by
the demo itself, and `-statdump` output.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence


@dataclass
class EngineRun:
    cmd: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration_s: float
    savegames: Dict[str, str] = field(default_factory=dict)  # name -> path
    statdump: Optional[str] = None

    @property
    def ok(self) -> bool:
        log = self.stdout + self.stderr
        import re
        return self.returncode == 0 or bool(re.search(r"timed \d+ gametics in \d+ realtics", log))


DEFAULT_EXE = r"cdoom-bin\chocolate-doom.exe"
DEFAULT_IWAD = r"freedoom\freedoom-0.13.0\freedoom1.wad"


class ChocolateDoom:
    def __init__(
        self,
        exe: str = DEFAULT_EXE,
        iwad: str = DEFAULT_IWAD,
        workdir: str = "_engine_run",
        timeout: float = 600.0,
    ) -> None:
        self.exe = str(Path(exe).resolve())
        self.iwad = str(Path(iwad).resolve())
        self.workdir = Path(workdir).resolve()
        self.timeout = timeout
        if not Path(self.exe).exists():
            raise FileNotFoundError(self.exe)
        if not Path(self.iwad).exists():
            raise FileNotFoundError(self.iwad)

    def run_demo(
        self,
        wad: str,
        demo: str,
        save_dir: Optional[str] = None,
        statdump: bool = True,
        timedemo: bool = False,
        extra: Sequence[str] = (),
    ) -> EngineRun:
        work = self.workdir
        work.mkdir(parents=True, exist_ok=True)
        save_path = Path(save_dir).resolve() if save_dir else work / "save"
        save_path.mkdir(parents=True, exist_ok=True)
        if any(save_path.iterdir()):
            raise ValueError("use an empty save directory; existing saves are never deleted")

        args: List[str] = [
            self.exe,
            "-iwad",
            self.iwad,
            "-file",
            str(Path(wad).resolve()),
            "-config",
            str(work / "chocolate-doom.cfg"),
            "-savedir",
            str(save_path),
            "-nosound",
            "-nomusic",
            "-nosfx",
            "-window",
        ]
        if timedemo:
            args += ["-timedemo", str(Path(demo).resolve())]
        else:
            args += ["-playdemo", str(Path(demo).resolve())]
        if statdump:
            args += ["-statdump", str(work / "statdump.txt")]
        args += list(extra)

        env = dict(os.environ)
        env["SDL_VIDEODRIVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"
        t0 = time.time()
        proc = subprocess.run(
            args,
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            input="",
        )
        dur = time.time() - t0
        saves = {
            p.name: str(p) for p in sorted(save_path.glob("*.dsg"))
        } if save_path.exists() else {}
        stat = None
        sp = work / "statdump.txt"
        if sp.exists():
            stat = sp.read_text(errors="replace")
        return EngineRun(
            cmd=args,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_s=dur,
            savegames=saves,
            statdump=stat,
        )