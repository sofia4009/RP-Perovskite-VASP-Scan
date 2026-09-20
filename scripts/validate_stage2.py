#!/usr/bin/env python3
"""Validate the Stage 2 tree before VASP and after DOS preparation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PRE_OPT = ("POSCAR", "INCAR", "KPOINTS", "POTCAR")
PRE_DOS = ("INCAR", "KPOINTS", "POTCAR")
DOS_OPT = ("CONTCAR",)
DOS_DOS = ("POSCAR", "INCAR", "KPOINTS", "POTCAR")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage2-dir", required=True, type=Path)
    p.add_argument("--phase", choices=("pre", "dos"), required=True)
    return p.parse_args()


def nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def find_structures(root: Path) -> list[Path]:
    # Stage 2 currently creates batch_XXX/<structure> directories.
    structures: list[Path] = []
    for batch in sorted(root.glob("batch_*")):
        if not batch.is_dir():
            continue
        for child in sorted(batch.iterdir()):
            if child.is_dir() and (child / "optimization").is_dir() and (child / "dos").is_dir():
                structures.append(child)
    return structures


def validate_structure(structure: Path, phase: str) -> list[str]:
    opt = structure / "optimization"
    dos = structure / "dos"
    required_opt = PRE_OPT if phase == "pre" else DOS_OPT
    required_dos = PRE_DOS if phase == "pre" else DOS_DOS
    missing: list[str] = []
    for rel in required_opt:
        if not nonempty(opt / rel):
            missing.append(f"optimization/{rel}")
    for rel in required_dos:
        if not nonempty(dos / rel):
            missing.append(f"dos/{rel}")
    return missing


def main() -> int:
    args = parse_args()
    root = args.stage2_dir.resolve()
    if not root.is_dir():
        print(f"ERROR: Stage 2 directory does not exist: {root}", file=sys.stderr)
        return 2

    structures = find_structures(root)
    if not structures:
        print(f"ERROR: no Stage 2 structures found under {root}", file=sys.stderr)
        return 2

    failures: list[tuple[Path, list[str]]] = []
    for structure in structures:
        missing = validate_structure(structure, args.phase)
        if missing:
            failures.append((structure, missing))

    passed = len(structures) - len(failures)
    print(f"Stage 2 validation phase : {args.phase}")
    print(f"Structures                : {len(structures)}")
    print(f"Passing                   : {passed}")
    print(f"Failing                   : {len(failures)}")
    if failures:
        print("Failures:")
        for structure, missing in failures:
            print(f"  {structure}")
            for item in missing:
                print(f"    missing/empty: {item}")
        return 1
    print("Validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
