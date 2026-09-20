#!/usr/bin/env python3
"""Prepare DOS inputs from a completed optimization."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--structure-dir", required=True, type=Path)
    return p.parse_args()


def nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def main() -> int:
    args = parse_args()
    root = args.structure_dir.resolve()
    opt = root / "optimization"
    dos = root / "dos"
    contcar = opt / "CONTCAR"
    if not nonempty(contcar):
        print(f"ERROR: missing/empty optimization/CONTCAR: {contcar}", file=sys.stderr)
        return 1
    for name in ("INCAR", "KPOINTS", "POTCAR"):
        if not nonempty(dos / name):
            print(f"ERROR: missing/empty dos/{name}: {dos / name}", file=sys.stderr)
            return 1
    dos.mkdir(parents=True, exist_ok=True)
    target = dos / "POSCAR"
    if not nonempty(target):
        shutil.copy2(contcar, target)
        print(f"DOS POSCAR prepared: {target}")
    else:
        print(f"DOS POSCAR already valid; leaving unchanged: {target}")

    chgcar = opt / "CHGCAR"
    dos_chgcar = dos / "CHGCAR"
    if nonempty(chgcar) and not nonempty(dos_chgcar):
        shutil.copy2(chgcar, dos_chgcar)
        print(f"CHGCAR copied: {dos_chgcar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
