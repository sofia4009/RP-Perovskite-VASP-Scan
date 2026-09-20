from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "scripts" / "validate_stage2.py"
PREPARE = ROOT / "scripts" / "prepare_dos.py"


def write(path: Path, text: str = "x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_stage2(root: Path):
    opt = root / "batch_001" / "mp-test_X" / "optimization"
    dos = root / "batch_001" / "mp-test_X" / "dos"
    for name in ("POSCAR", "INCAR", "KPOINTS", "POTCAR"):
        write(opt / name)
    for name in ("INCAR", "KPOINTS", "POTCAR"):
        write(dos / name)
    return opt.parent


def test_pre_allows_missing_dos_poscar(tmp_path):
    make_stage2(tmp_path)
    result = subprocess.run([sys.executable, str(VALIDATE), "--stage2-dir", str(tmp_path), "--phase", "pre"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_prepare_dos_requires_contcar(tmp_path):
    structure = make_stage2(tmp_path)
    result = subprocess.run([sys.executable, str(PREPARE), "--structure-dir", str(structure)], capture_output=True, text=True)
    assert result.returncode != 0


def test_prepare_dos_copies_contcar(tmp_path):
    structure = make_stage2(tmp_path)
    write(structure / "optimization" / "CONTCAR", "relaxed")
    result = subprocess.run([sys.executable, str(PREPARE), "--structure-dir", str(structure)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (structure / "dos" / "POSCAR").read_text(encoding="utf-8") == "relaxed"
    result = subprocess.run([sys.executable, str(VALIDATE), "--stage2-dir", str(tmp_path), "--phase", "dos"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_pre_fails_without_potcar(tmp_path):
    structure = make_stage2(tmp_path)
    (structure / "optimization" / "POTCAR").unlink()
    result = subprocess.run([sys.executable, str(VALIDATE), "--stage2-dir", str(tmp_path), "--phase", "pre"], capture_output=True, text=True)
    assert result.returncode != 0
