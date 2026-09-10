
#!/usr/bin/env python
# coding: utf-8

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from ase.io import read, write
from pymatgen.core import Structure


VARIANT = {
    "Li": "Li_sv",
    "Fe": "Fe_sv",
    "Mo": "Mo_sv",
    "Cr": "Cr_pv",
    "V": "V_sv",
    "Bi": "Bi_d",
    "Mg": "Mg_pv",
    "Cs": "Cs_sv",
    "Rh": "Rh_pv",
    "Hf": "Hf_pv",
    "N": "N",
    "Cl": "Cl",
    "Ti": "Ti_sv",
    "Ba": "Ba_sv",
    "Mn": "Mn_sv",
    "Cu": "Cu_pv",
    "Y": "Y_sv",
    "In": "In_d",
    "Na": "Na_pv",
    "W": "W_sv",
    "Pd": "Pd_pv",
    "Ta": "Ta_pv",
    "S": "S",
    "Br": "Br",
    "O": "O",
    "Ca": "Ca_sv",
    "Ni": "Ni_pv",
    "Zn": "Zn",
    "Zr": "Zr_sv",
    "Sn": "Sn_d",
    "K": "K_sv",
    "Re": "Re_pv",
    "Pt": "Pt_pv",
    "Ge": "Ge_d",
    "Se": "Se",
    "P": "P",
    "Sr": "Sr_sv",
    "Nb": "Nb_sv",
    "Co": "Co",
    "Sc": "Sc_sv",
    "La": "La",
    "Pb": "Pb_d",
    "Rb": "Rb_sv",
    "Ru": "Ru_pv",
    "Ir": "Ir",
    "Ga": "Ga_d",
    "F": "F",
    "Si": "Si",
    "C": "C",
    "Tm": "Tm_3",
    "Ag": "Ag_pv",
    "Er": "Er_3",
    "Gd": "Gd_3",
    "B": "B",
    "Eu": "Eu_2",
    "Os": "Os_pv",
    "Tb": "Tb_3",
    "Yb": "Yb_2",
    "H": "H",
    "Nd": "Nd_3",
    "Dy": "Dy_3",
    "Sm": "Sm_3",
    "Al": "Al",
    "Pr": "Pr_3",
    "Ho": "Ho_3",
    "Lu": "Lu_3",
}

STRIP_TAGS = {
    "LDAU",
    "LDAUJ",
    "LDAUL",
    "LDAUU",
    "LDAUTYPE",
    "LDAUPRINT",
    "GGA",
}

MAGNETIC_TM = {"Fe", "Mn", "Co", "Ni", "Cu"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build SCAN VASP input directories (optimization + DOS) "
            "for magnetic A-B-O RP-space-group candidates."
        )
    )

    parser.add_argument(
        "--cif-dir",
        required=True,
        type=Path,
        help="Directory containing CIF files.",
    )

    parser.add_argument(
        "--incar-dir",
        required=True,
        type=Path,
        help="Directory containing MPRelaxSet INCAR files.",
    )

    parser.add_argument(
        "--kpoints-dir",
        required=True,
        type=Path,
        help="Directory containing MPRelaxSet KPOINTS files.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Root directory for generated VASP input trees.",
    )

    parser.add_argument(
        "--pp-root",
        required=True,
        type=Path,
        help="Root directory of the PAW PBE pseudopotential library.",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Abort when a structure without Fe/Mn/Co/Ni/Cu is encountered."
        ),
    )

    return parser.parse_args()


def get_mp_magmom(incar_text: str) -> str:
    for line in incar_text.splitlines():
        tag = line.split("=", 1)[0].strip().upper()

        if tag == "MAGMOM":
            if "=" not in line:
                continue

            value = line.split("=", 1)[1].split("#", 1)[0].strip()
            return f"MAGMOM = {value}"

    return ""


def structure_has_magnetic_tm(structure: Structure) -> bool:
    return any(
        str(site.specie.symbol) in MAGNETIC_TM
        for site in structure
    )


def _parse_encut(incar_text: str) -> int:
    for line in incar_text.splitlines():
        key = line.split("#", 1)[0].split("=", 1)[0].strip().upper()

        if key == "ENCUT":
            try:
                value = line.split("=", 1)[1].split("#", 1)[0].strip()
                return int(float(value))
            except (IndexError, ValueError):
                pass

    return 0


def patch_incar_relaxation(
    incar_text: str,
    mp_magmom: str,
    has_tm: bool = True,
) -> str:
    mp_encut = _parse_encut(incar_text)
    final_encut = max(mp_encut, 600)

    lines = incar_text.splitlines()
    new_lines = []

    found = {
        key: False
        for key in [
            "METAGGA",
            "LASPH",
            "ALGO",
            "ISMEAR",
            "SIGMA",
            "EDIFF",
            "EDIFFG",
            "ENCUT",
            "NELM",
            "LCHARG",
            "LWAVE",
            "NSW",
            "IBRION",
            "ISIF",
            "MAGMOM",
            "ISPIN",
            "PREC",
            "LREAL",
        ]
    }

    for line in lines:
        raw_tag = line.split("#", 1)[0].split("=", 1)[0].strip().upper()

        if raw_tag in STRIP_TAGS:
            continue

        if raw_tag == "METAGGA":
            new_lines.append("METAGGA = SCAN")
            found["METAGGA"] = True

        elif raw_tag == "LMETAGGA":
            continue

        elif raw_tag == "LASPH":
            new_lines.append("LASPH = .TRUE.")
            found["LASPH"] = True

        elif raw_tag == "ALGO":
            new_lines.append("ALGO = All")
            found["ALGO"] = True

        elif raw_tag == "ISMEAR":
            new_lines.append("ISMEAR = 0")
            found["ISMEAR"] = True

        elif raw_tag == "SIGMA":
            new_lines.append("SIGMA = 0.05")
            found["SIGMA"] = True

        elif raw_tag == "EDIFF":
            new_lines.append("EDIFF = 1E-5")
            found["EDIFF"] = True

        elif raw_tag == "EDIFFG":
            new_lines.append("EDIFFG = -0.02")
            found["EDIFFG"] = True

        elif raw_tag == "ENCUT":
            new_lines.append(f"ENCUT = {final_encut}")
            found["ENCUT"] = True

        elif raw_tag == "NELM":
            new_lines.append("NELM = 200")
            found["NELM"] = True

        elif raw_tag == "NSW":
            new_lines.append("NSW = 99")
            found["NSW"] = True

        elif raw_tag == "IBRION":
            new_lines.append("IBRION = 2")
            found["IBRION"] = True

        elif raw_tag == "ISIF":
            new_lines.append("ISIF = 3")
            found["ISIF"] = True

        elif raw_tag == "LCHARG":
            new_lines.append("LCHARG = .TRUE.")
            found["LCHARG"] = True

        elif raw_tag == "LWAVE":
            new_lines.append("LWAVE = .TRUE.")
            found["LWAVE"] = True

        elif raw_tag == "MAGMOM":
            if has_tm and mp_magmom:
                new_lines.append(mp_magmom)
            found["MAGMOM"] = True

        elif raw_tag == "ISPIN":
            new_lines.append(
                "ISPIN = 2" if has_tm else "ISPIN = 1"
            )
            found["ISPIN"] = True

        elif raw_tag == "PREC":
            new_lines.append("PREC = Accurate")
            found["PREC"] = True

        elif raw_tag == "LREAL":
            new_lines.append("LREAL = .FALSE.")
            found["LREAL"] = True

        else:
            new_lines.append(line)

    if not found["METAGGA"]:
        new_lines.append("METAGGA = SCAN")

    if not found["LASPH"]:
        new_lines.append("LASPH = .TRUE.")

    if not found["ALGO"]:
        new_lines.append("ALGO = All")

    if not found["ISPIN"]:
        new_lines.append(
            "ISPIN = 2" if has_tm else "ISPIN = 1"
        )

    if not found["PREC"]:
        new_lines.append("PREC = Accurate")

    if not found["LREAL"]:
        new_lines.append("LREAL = .FALSE.")

    if not found["ISMEAR"]:
        new_lines.append("ISMEAR = 0")

    if not found["SIGMA"]:
        new_lines.append("SIGMA = 0.05")

    if not found["EDIFF"]:
        new_lines.append("EDIFF = 1E-5")

    if not found["EDIFFG"]:
        new_lines.append("EDIFFG = -0.02")

    if not found["ENCUT"]:
        new_lines.append(f"ENCUT = {final_encut}")

    if not found["NELM"]:
        new_lines.append("NELM = 200")

    if not found["NSW"]:
        new_lines.append("NSW = 99")

    if not found["IBRION"]:
        new_lines.append("IBRION = 2")

    if not found["ISIF"]:
        new_lines.append("ISIF = 3")

    if not found["LCHARG"]:
        new_lines.append("LCHARG = .TRUE.")

    if not found["LWAVE"]:
        new_lines.append("LWAVE = .TRUE.")

    if not found["MAGMOM"] and has_tm and mp_magmom:
        new_lines.append(mp_magmom)

    new_lines.extend(
        [
            "AMIX = 0.1",
            "BMIX = 0.0001",
            "AMIX_MAG = 0.4",
            "BMIX_MAG = 0.0001",
            "POTIM = 0.2",
            "ISYM = 0",
            "NCORE = 4",
        ]
    )

    return "\n".join(new_lines) + "\n"


def patch_incar_dos(
    incar_text: str,
    mp_magmom: str,
    has_tm: bool = True,
) -> str:
    mp_encut = _parse_encut(incar_text)
    final_encut = max(mp_encut, 600)

    lines = incar_text.splitlines()
    new_lines = []

    found = {
        key: False
        for key in [
            "METAGGA",
            "LASPH",
            "ALGO",
            "ISMEAR",
            "EDIFF",
            "ENCUT",
            "NELM",
            "LCHARG",
            "LWAVE",
            "NSW",
            "IBRION",
            "ISIF",
            "ICHARG",
            "NEDOS",
            "LORBIT",
            "MAGMOM",
            "ISPIN",
            "PREC",
            "LREAL",
        ]
    }

    for line in lines:
        raw_tag = line.split("#", 1)[0].split("=", 1)[0].strip().upper()

        if raw_tag in STRIP_TAGS:
            continue

        if raw_tag in ("EDIFFG", "SIGMA"):
            continue

        if raw_tag == "METAGGA":
            new_lines.append("METAGGA = SCAN")
            found["METAGGA"] = True

        elif raw_tag == "LMETAGGA":
            continue

        elif raw_tag == "LASPH":
            new_lines.append("LASPH = .TRUE.")
            found["LASPH"] = True

        elif raw_tag == "ALGO":
            new_lines.append("ALGO = All")
            found["ALGO"] = True

        elif raw_tag == "ISMEAR":
            new_lines.append("ISMEAR = -5")
            found["ISMEAR"] = True

        elif raw_tag == "EDIFF":
            new_lines.append("EDIFF = 1E-5")
            found["EDIFF"] = True

        elif raw_tag == "ENCUT":
            new_lines.append(f"ENCUT = {final_encut}")
            found["ENCUT"] = True

        elif raw_tag == "NELM":
            new_lines.append("NELM = 200")
            found["NELM"] = True

        elif raw_tag == "NSW":
            new_lines.append("NSW = 0")
            found["NSW"] = True

        elif raw_tag == "IBRION":
            new_lines.append("IBRION = -1")
            found["IBRION"] = True

        elif raw_tag == "ISIF":
            new_lines.append("ISIF = 2")
            found["ISIF"] = True

        elif raw_tag == "LCHARG":
            new_lines.append("LCHARG = .FALSE.")
            found["LCHARG"] = True

        elif raw_tag == "LWAVE":
            new_lines.append("LWAVE = .FALSE.")
            found["LWAVE"] = True

        elif raw_tag == "ICHARG":
            new_lines.append("ICHARG = 1")
            found["ICHARG"] = True

        elif raw_tag == "NEDOS":
            new_lines.append("NEDOS = 2000")
            found["NEDOS"] = True

        elif raw_tag == "LORBIT":
            new_lines.append("LORBIT = 11")
            found["LORBIT"] = True

        elif raw_tag == "MAGMOM":
            if has_tm and mp_magmom:
                new_lines.append(mp_magmom)
            found["MAGMOM"] = True

        elif raw_tag == "ISPIN":
            new_lines.append(
                "ISPIN = 2" if has_tm else "ISPIN = 1"
            )
            found["ISPIN"] = True

        elif raw_tag == "PREC":
            new_lines.append("PREC = Accurate")
            found["PREC"] = True

        elif raw_tag == "LREAL":
            new_lines.append("LREAL = .FALSE.")
            found["LREAL"] = True

        else:
            new_lines.append(line)

    if not found["METAGGA"]:
        new_lines.append("METAGGA = SCAN")

    if not found["LASPH"]:
        new_lines.append("LASPH = .TRUE.")

    if not found["ALGO"]:
        new_lines.append("ALGO = All")

    if not found["ISPIN"]:
        new_lines.append(
            "ISPIN = 2" if has_tm else "ISPIN = 1"
        )

    if not found["PREC"]:
        new_lines.append("PREC = Accurate")

    if not found["LREAL"]:
        new_lines.append("LREAL = .FALSE.")

    if not found["ISMEAR"]:
        new_lines.append("ISMEAR = -5")

    if not found["EDIFF"]:
        new_lines.append("EDIFF = 1E-5")

    if not found["ENCUT"]:
        new_lines.append(f"ENCUT = {final_encut}")

    if not found["NELM"]:
        new_lines.append("NELM = 200")

    if not found["NSW"]:
        new_lines.append("NSW = 0")

    if not found["IBRION"]:
        new_lines.append("IBRION = -1")

    if not found["ISIF"]:
        new_lines.append("ISIF = 2")

    if not found["LCHARG"]:
        new_lines.append("LCHARG = .FALSE.")

    if not found["LWAVE"]:
        new_lines.append("LWAVE = .FALSE.")

    if not found["ICHARG"]:
        new_lines.append("ICHARG = 1")

    if not found["NEDOS"]:
        new_lines.append("NEDOS = 2000")

    if not found["LORBIT"]:
        new_lines.append("LORBIT = 11")

    if not found["MAGMOM"] and has_tm and mp_magmom:
        new_lines.append(mp_magmom)

    new_lines.extend(
        [
            "AMIX = 0.1",
            "BMIX = 0.0001",
            "AMIX_MAG = 0.4",
            "BMIX_MAG = 0.0001",
            "NCORE = 4",
        ]
    )

    return "\n".join(new_lines) + "\n"


def build_potcar(
    structure: Structure,
    pp_root: Path,
    output_dir: Path,
) -> bool:
    """
    Build POTCAR if the requested pseudopotential library exists.

    Returns True if POTCAR was created, False if the pseudopotential
    library is unavailable.
    """
    elements = [str(element) for element in structure.elements]

    missing = []

    for element in elements:
        if element not in VARIANT:
            missing.append(
                f"{element}: not present in VARIANT mapping"
            )
            continue

        pp_file = pp_root / VARIANT[element] / "POTCAR"

        if not pp_file.exists():
            missing.append(str(pp_file))

    if missing:
        print("  POTCAR   : NOT BUILT")
        print("  Missing pseudopotentials:")

        for item in missing:
            print(f"    {item}")

        return False

    potcar_path = output_dir / "POTCAR"

    with open(potcar_path, "wb") as output:
        for element in elements:
            pp_file = pp_root / VARIANT[element] / "POTCAR"
            output.write(pp_file.read_bytes())

    print(f"  POTCAR   : {potcar_path}")
    return True


def main() -> None:
    args = parse_args()

    cif_dir = args.cif_dir
    incar_dir = args.incar_dir
    kpoints_dir = args.kpoints_dir
    output_dir = args.output_dir
    pp_root = args.pp_root
    strict = args.strict

    print("=" * 60)
    print("STAGE 02 – SCAN VASP INPUT BUILDER")
    print("=" * 60)
    print(f"CIF source directory     : {cif_dir}")
    print(f"INCAR source directory   : {incar_dir}")
    print(f"KPOINTS source directory : {kpoints_dir}")
    print(f"Output directory         : {output_dir}")
    print(f"Pseudopotential root     : {pp_root}")
    print(f"Strict mode              : {strict}")
    print("=" * 60)

    for directory in (cif_dir, incar_dir, kpoints_dir):
        if not directory.exists():
            raise FileNotFoundError(
                f"Required input directory does not exist: {directory}"
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    cif_map = {
        path.name.split("_", 1)[0]: path
        for path in sorted(cif_dir.glob("*.cif"))
    }

    incar_map = {
        path.name.split("_", 1)[0]: path
        for path in sorted(incar_dir.glob("*_INCAR"))
    }

    kpoints_map = {
        path.name.split("_", 1)[0]: path
        for path in sorted(kpoints_dir.glob("*_KPOINTS"))
    }

    all_ids = sorted(set(cif_map) & set(incar_map))

    print(f"CIF files found          : {len(cif_map)}")
    print(f"INCAR files found        : {len(incar_map)}")
    print(f"KPOINTS files found      : {len(kpoints_map)}")
    print(f"Matched CIF + INCAR      : {len(all_ids)}")
    print("=" * 60)

    success = 0
    skipped = 0
    failed = 0
    potcar_missing = 0

    failed_list: list[tuple[str, str]] = []
    batch_folders: dict[str, list[str]] = {}

    batch_size = 15
    magnetic_count = 0

    for index, material_id in enumerate(all_ids, start=1):
        cif_path = cif_map[material_id]
        incar_path = incar_map[material_id]
        kpoints_path = kpoints_map.get(material_id)

        folder_name = cif_path.stem

        print(f"[{index}/{len(all_ids)}] {material_id}")
        print(f"  CIF      : {cif_path.name}")
        print(f"  INCAR    : {incar_path.name}")

        if kpoints_path is None:
            message = "no KPOINTS found"
            print(f"  WARNING  : {message}")

            failed += 1
            failed_list.append((folder_name, message))
            continue

        print(f"  KPOINTS  : {kpoints_path.name}")

        try:
            atoms = read(str(cif_path))

            tmp_poscar = output_dir / "_tmp_poscar.vasp"

            write(
                str(tmp_poscar),
                atoms,
                format="vasp",
                direct=True,
                sort=True,
                vasp5=True,
            )

            structure = Structure.from_file(tmp_poscar)

            tmp_poscar.unlink(missing_ok=True)

            has_tm = structure_has_magnetic_tm(structure)

        except Exception as error:
            failed += 1

            failed_list.append(
                (folder_name, f"read-structure: {error}")
            )

            print(
                f"  ERROR    : structure load failed: {error}"
            )

            continue

        if not has_tm:
            message = "no Fe/Mn/Co/Ni/Cu in structure"

            if strict:
                raise RuntimeError(
                    f"{folder_name}: {message}"
                )

            print(
                f"  WARNING  : {message} (skipping)"
            )

            skipped += 1
            continue

        print("  Magnetic TM detected")

        try:
            incar_text = incar_path.read_text(
                encoding="utf-8"
            )

            mp_magmom = get_mp_magmom(incar_text)

            print(
                "  MP MAGMOM: "
                f"{mp_magmom if mp_magmom else 'not found'}"
            )

        except Exception as error:
            failed += 1

            failed_list.append(
                (folder_name, f"read-incar: {error}")
            )

            print(
                f"  ERROR    : INCAR read failed: {error}"
            )

            continue

        batch_number = (
            magnetic_count // batch_size
        ) + 1

        batch_name = f"batch_{batch_number:03d}"

        batch_path = output_dir / batch_name
        base_path = batch_path / folder_name

        opt_path = base_path / "optimization"
        dos_path = base_path / "dos"

        opt_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        dos_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            opt_poscar = opt_path / "POSCAR"

            write(
                str(opt_poscar),
                atoms,
                format="vasp",
                direct=True,
                sort=True,
                vasp5=True,
            )

            opt_structure = Structure.from_file(
                str(opt_poscar)
            )

            opt_incar = patch_incar_relaxation(
                incar_text,
                mp_magmom,
                has_tm=has_tm,
            )

            dos_incar = patch_incar_dos(
                incar_text,
                mp_magmom,
                has_tm=has_tm,
            )

            (
                opt_path / "INCAR"
            ).write_text(
                opt_incar,
                encoding="utf-8",
            )

            (
                dos_path / "INCAR"
            ).write_text(
                dos_incar,
                encoding="utf-8",
            )

            shutil.copy2(
                str(kpoints_path),
                str(opt_path / "KPOINTS"),
            )

            shutil.copy2(
                str(kpoints_path),
                str(dos_path / "KPOINTS"),
            )

            print("  POSCAR   : created")
            print("  INCAR    : optimization + DOS created")
            print("  KPOINTS  : copied")

            potcar_ok_opt = build_potcar(
                opt_structure,
                pp_root,
                opt_path,
            )

            potcar_ok_dos = build_potcar(
                opt_structure,
                pp_root,
                dos_path,
            )

            if not potcar_ok_opt or not potcar_ok_dos:
                potcar_missing += 1

            batch_folders.setdefault(
                batch_name,
                [],
            ).append(folder_name)

            magnetic_count += 1
            success += 1

            print(
                f"  OK       : "
                f"{batch_name}/{folder_name}"
            )

        except Exception as error:
            failed += 1

            failed_list.append(
                (folder_name, str(error))
            )

            print(
                f"  ERROR    : build failed: {error}"
            )

    print()
    print("=" * 60)
    print("STAGE 02 SUMMARY")
    print("=" * 60)
    print(f"Processed magnetic       : {success}")
    print(f"Skipped non-magnetic     : {skipped}")
    print(f"Failed                   : {failed}")
    print(f"Missing POTCAR libraries : {potcar_missing}")
    print(f"Output directory         : {output_dir}")

    if failed_list:
        print()
        print("Failed structures:")

        for name, error in failed_list:
            print(f"  {name}: {error}")

    print("=" * 60)

    if potcar_missing:
        print()
        print(
            "WARNING: Some POTCAR files were not created because "
            "the required pseudopotential library is not available."
        )

        print(
            "This is expected in the current Colab environment."
        )

    print()
    print(
        "Stage 02 input-tree generation finished."
    )


if __name__ == "__main__":
    main()
