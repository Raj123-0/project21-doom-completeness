import pytest
from doomc.__main__ import compile_spec

def test_compile_spec_unsupported_system(tmp_path):
    spec = {"system": "conway", "boundary": "periodic", "initial": [0, 1], "steps": 1}
    with pytest.raises(ValueError, match="only periodic Rule 110 trace visualization is supported"):
        compile_spec(spec, tmp_path / "out.wad")

def test_compile_spec_missing_keys(tmp_path):
    spec = {"system": "rule110", "boundary": "periodic"}
    with pytest.raises(ValueError, match="required keys: system, boundary, initial, steps"):
        compile_spec(spec, tmp_path / "out.wad")
