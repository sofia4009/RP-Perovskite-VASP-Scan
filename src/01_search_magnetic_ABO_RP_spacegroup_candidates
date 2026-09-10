
#!/usr/bin/env python
# coding: utf-8

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from mp_api.client import MPRester
from pymatgen.io.cif import CifWriter
from pymatgen.io.vasp.sets import MPRelaxSet


# RP-compatible space groups
RP_SPACEGROUPS = [139, 14, 12, 62, 164, 127, 140, 87, 63, 15]


def load_api_key() -> str:
    env_path = os.path.expanduser("~/.mp_api_key")
    load_dotenv(env_path)

    api_key = os.getenv("MP_API_KEY")

    if not api_key:
        raise RuntimeError(
            "MP_API_KEY not found in ~/.mp_api_key"
        )

    return api_key


def download_files(
    mpr: MPRester,
    material_id: str,
    formula: str,
    cif_dir: Path,
    incar_dir: Path,
    kpoints_dir: Path,
) -> list[str]:

    cif_path = cif_dir / f"{material_id}_{formula}.cif"
    incar_path = incar_dir / f"{material_id}_{formula}_INCAR"
    kpoints_path = kpoints_dir / f"{material_id}_{formula}_KPOINTS"

    if (
        cif_path.exists()
        and incar_path.exists()
        and kpoints_path.exists()
    ):
        return []

    errors = []

    try:

        structure = mpr.get_structure_by_material_id(
            material_id,
            conventional_unit_cell=True,
        )

        if not cif_path.exists():
            CifWriter(structure).write_file(cif_path)
            print(
                f"    [CIF]     {cif_path.name}",
                flush=True,
            )

        relax_set = MPRelaxSet(structure)

        if not incar_path.exists():
            relax_set.incar.write_file(incar_path)
            print(
                f"    [INCAR]   {incar_path.name}",
                flush=True,
            )

        if not kpoints_path.exists():
            relax_set.kpoints.write_file(kpoints_path)
            print(
                f"    [KPOINTS] {kpoints_path.name}",
                flush=True,
            )

        time.sleep(0.1)

    except Exception as exc:

        msg = f"{material_id} ({formula}): {exc}"

        print(
            f"    ERROR: {msg}",
            flush=True,
        )

        errors.append(msg)

    return errors


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Search magnetic A-B-O RP-space-group candidates "
            "and generate CIF/INCAR/KPOINTS."
        )
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--a-sites",
        nargs="+",
        default=[
            "Li", "Na", "K",
            "Ca", "Sr", "Ba", "Mg",
            "La", "Pr", "Nd", "Sm", "Eu", "Gd",
            "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
            "Y", "Bi",
        ],
    )

    parser.add_argument(
        "--b-sites",
        nargs="+",
        default=[
            "Fe", "Mn", "Co", "Ni", "Cu"
        ],
    )

    parser.add_argument(
        "--anions",
        nargs="+",
        default=["O"],
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    output_dir = args.output_dir

    csv_path = (
        output_dir
        / "magnetic_ABO_RP_spacegroup_candidates.csv"
    )

    cif_dir = (
        output_dir
        / "structures"
        / "cif"
    )

    incar_dir = (
        output_dir
        / "inputs"
        / "mprelax_incar"
    )

    kpoints_dir = (
        output_dir
        / "inputs"
        / "mprelax_kpoints"
    )

    logs_dir = output_dir / "logs"

    for directory in (
        cif_dir,
        incar_dir,
        kpoints_dir,
        logs_dir,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    a_sites = args.a_sites
    b_sites = args.b_sites
    anions = args.anions

    print("=" * 70)
    print("STAGE 01 – MAGNETIC A-B-O RP-SPACE-GROUP SEARCH")
    print("=" * 70)

    print(f"A-site elements : {a_sites}")
    print(f"B-site elements : {b_sites}")
    print(f"Anions          : {anions}")
    print(
        "Chemical systems:",
        len(a_sites) * len(b_sites) * len(anions),
    )

    print()
    print(f"Output directory: {output_dir}")
    print(f"CSV             : {csv_path}")
    print(f"CIF             : {cif_dir}")
    print(f"INCAR           : {incar_dir}")
    print(f"KPOINTS         : {kpoints_dir}")
    print("=" * 70)

    # ---------------------------------------------------------
    # Resume existing CSV
    # ---------------------------------------------------------

    all_results = []
    seen_ids = set()
    errors = []

    if csv_path.exists():

        print("\nExisting CSV detected. Resuming...")

        try:

            old_df = pd.read_csv(
                csv_path,
                dtype={"material_id": str},
            )

            if "material_id" in old_df.columns:

                for _, row in old_df.iterrows():

                    mid = str(row["material_id"])

                    if mid not in seen_ids:

                        seen_ids.add(mid)
                        all_results.append(
                            row.to_dict()
                        )

            print(
                f"Existing records loaded: "
                f"{len(all_results)}"
            )

        except Exception as exc:

            print(
                f"WARNING: could not load existing CSV: {exc}"
            )

    # ---------------------------------------------------------
    # Resume from files already on disk
    # ---------------------------------------------------------

    existing_cif = {
        f.name.split("_", 1)[0]
        for f in cif_dir.iterdir()
        if f.is_file()
        and f.name.endswith(".cif")
    }

    existing_incar = {
        f.name.split("_", 1)[0]
        for f in incar_dir.iterdir()
        if f.is_file()
        and f.name.endswith("_INCAR")
    }

    existing_kpoints = {
        f.name.split("_", 1)[0]
        for f in kpoints_dir.iterdir()
        if f.is_file()
        and f.name.endswith("_KPOINTS")
    }

    print(
        f"CIF already on disk     : {len(existing_cif)}"
    )
    print(
        f"INCAR already on disk   : {len(existing_incar)}"
    )
    print(
        f"KPOINTS already on disk : {len(existing_kpoints)}"
    )

    # ---------------------------------------------------------
    # Materials Project
    # ---------------------------------------------------------

    api_key = load_api_key()

    total_systems = (
        len(a_sites)
        * len(b_sites)
        * len(anions)
    )

    searched = 0
    last_saved = len(all_results)

    SAVE_EVERY = 50

    print("\nStarting Materials Project search...")
    print("=" * 70)

    with MPRester(api_key) as mpr:

        db_version = getattr(
            mpr,
            "db_version",
            None,
        )

        print(
            f"Connected to Materials Project. "
            f"db_version = {db_version!r}"
        )

        print("=" * 70)

        for A in a_sites:

            for B in b_sites:

                for X in anions:

                    searched += 1

                    chemsys = f"{A}-{B}-{X}"

                    print(
                        f"\n[{searched}/{total_systems}] "
                        f"{chemsys}",
                        flush=True,
                    )

                    try:

                        docs = mpr.materials.summary.search(
                            chemsys=chemsys,
                            fields=[
                                "material_id",
                                "formula_pretty",
                                "symmetry",
                                "band_gap",
                                "energy_above_hull",
                                "formation_energy_per_atom",
                                "is_stable",
                                "nelements",
                            ],
                        )

                    except Exception as exc:

                        msg = f"{chemsys}: {exc}"

                        print(
                            f"  ERROR: {exc}",
                            flush=True,
                        )

                        errors.append(msg)
                        continue

                    if not docs:

                        print(
                            "  No entries returned.",
                            flush=True,
                        )

                        continue

                    found = 0

                    for doc in docs:

                        mid = str(doc.material_id)

                        if mid in seen_ids:

                            continue

                        if doc.symmetry:

                            sg_number = (
                                doc.symmetry.number
                            )

                            sg_symbol = (
                                doc.symmetry.symbol
                            )

                            crystal_system = (
                                doc.symmetry.crystal_system
                            )

                        else:

                            sg_number = None
                            sg_symbol = "N/A"
                            crystal_system = "N/A"

                        if (
                            sg_number
                            not in RP_SPACEGROUPS
                        ):

                            continue

                        formula = doc.formula_pretty

                        print(
                            f"  MATCH: {formula} | "
                            f"SG={sg_number} "
                            f"({sg_symbol})",
                            flush=True,
                        )

                        seen_ids.add(mid)
                        found += 1

                        record = {
                            "A_site": A,
                            "B_site": B,
                            "Anion": X,
                            "material_id": mid,
                            "formula": formula,
                            "spacegroup_symbol": sg_symbol,
                            "spacegroup_number": sg_number,
                            "crystal_system": crystal_system,
                            "band_gap": doc.band_gap,
                            "energy_above_hull": (
                                doc.energy_above_hull
                            ),
                            "formation_energy": (
                                doc.formation_energy_per_atom
                            ),
                            "is_stable": doc.is_stable,
                        }

                        all_results.append(record)

                        errs = download_files(
                            mpr=mpr,
                            material_id=mid,
                            formula=formula,
                            cif_dir=cif_dir,
                            incar_dir=incar_dir,
                            kpoints_dir=kpoints_dir,
                        )

                        errors.extend(errs)

                    print(
                        f"  → {found} new candidates",
                        flush=True,
                    )

                    # -------------------------------------------------
                    # Checkpoint
                    # -------------------------------------------------

                    if (
                        len(all_results)
                        - last_saved
                        >= SAVE_EVERY
                    ):

                        pd.DataFrame(
                            all_results
                        ).to_csv(
                            csv_path,
                            index=False,
                            encoding="utf-8-sig",
                        )

                        last_saved = len(
                            all_results
                        )

                        print(
                            f"  [CSV CHECKPOINT] "
                            f"{last_saved} records",
                            flush=True,
                        )

    # ---------------------------------------------------------
    # Final save
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SEARCH FINISHED")
    print("=" * 70)

    pd.DataFrame(
        all_results
    ).drop_duplicates(
        subset=["material_id"],
        keep="first",
    ).to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )

    # ---------------------------------------------------------
    # Final counts
    # ---------------------------------------------------------

    cif_count = len(
        list(cif_dir.glob("*.cif"))
    )

    incar_count = len(
        list(incar_dir.glob("*_INCAR"))
    )

    kpoints_count = len(
        list(kpoints_dir.glob("*_KPOINTS"))
    )

    print(
        f"Candidates : {len(all_results)}"
    )

    print(
        f"CIF files  : {cif_count}"
    )

    print(
        f"INCAR files: {incar_count}"
    )

    print(
        f"KPOINTS    : {kpoints_count}"
    )

    print(
        f"Errors     : {len(errors)}"
    )

    print(
        f"CSV        : {csv_path}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()

