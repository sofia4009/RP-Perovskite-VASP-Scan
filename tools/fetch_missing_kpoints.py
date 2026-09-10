#!/usr/bin/env python3

"""
Fetch missing KPOINTS files from Materials Project.

This utility compares candidate material IDs against the existing
KPOINTS directory and fetches only the missing KPOINTS files.

Candidate IDs can come from either:
1. A CSV file containing a material_id column, or
2. A text/CSV IDs file supplied with --ids-file.

With --dry-run, the script only reports missing IDs and does not
download or write files.
"""

import argparse
import os
import time
from pathlib import Path

import pandas as pd

from dotenv import load_dotenv
from mp_api.client import MPRester
from pymatgen.io.vasp.sets import MPRelaxSet


# ============================================================
# Helper functions
# ============================================================

def load_material_ids_from_csv(csv_path: Path) -> list[str]:
    """Load unique material IDs from a CSV file."""

    df = pd.read_csv(csv_path)

    if "material_id" not in df.columns:
        raise ValueError(
            f"CSV does not contain a 'material_id' column: {csv_path}"
        )

    ids = (
        df["material_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return sorted(set(ids))

def load_ids_file(ids_file: Path) -> list[str]:
    """
    Load material IDs from either:
    - a plain text file: one material_id per line
    - a CSV file containing a material_id column
    """
    if ids_file.suffix.lower() == ".csv":
        return load_material_ids_from_csv(ids_file)

    ids = []

    with ids_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            material_id = line.strip()

            if not material_id:
                continue

            ids.append(material_id)

    return sorted(set(ids))

def load_ids_file(ids_file: Path) -> list[str]:
    """
    Load material IDs from either:
    - a plain text file: one material_id per line
    - a CSV file containing a material_id column
    """
    if ids_file.suffix.lower() == ".csv":
        return load_material_ids_from_csv(ids_file)

    ids = []

    with ids_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            material_id = line.strip()

            if not material_id:
                continue

            ids.append(material_id)

    return sorted(set(ids))

def load_ids_file(path: Path) -> list[str]:
    """
    Load material IDs from either:

    1. A plain text file with one material_id per line, or
    2. A CSV file containing a material_id column.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"IDs file does not exist: {path}"
        )

    # CSV input
    if path.suffix.lower() == ".csv":
        return load_material_ids_from_csv(path)

    # Plain text input
    ids = []

    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            material_id = line.strip()

            # Ignore empty lines
            if not material_id:
                continue

            # Ignore comment lines
            if material_id.startswith("#"):
                continue

            ids.append(material_id)

    return sorted(set(ids))


def get_existing_kpoints_ids(kpoints_dir: Path) -> set[str]:
    """Return material IDs for which KPOINTS files already exist."""

    existing = set()

    if not kpoints_dir.exists():
        return existing

    for path in kpoints_dir.glob("*_KPOINTS"):
        material_id = path.name.split("_")[0]
        existing.add(material_id)

    return existing


def download_file(
    material_id: str,
    kpoints_dir: Path,
    mpr: MPRester,
) -> Path:
    """
    Generate the Materials Project relaxation KPOINTS file
    for one material and save it to kpoints_dir.
    """

    docs = mpr.materials.summary.search(
        material_ids=[material_id],
        fields=["material_id", "structure"],
    )

    if not docs:
        raise ValueError(
            f"Material not found in Materials Project: {material_id}"
        )

    structure = docs[0].structure

    if structure is None:
        raise ValueError(
            f"No structure returned for material: {material_id}"
        )

    # Build the same MP relaxation input set used for KPOINTS generation.
    vis = MPRelaxSet(structure)

    kpoints = vis.kpoints

    output_path = kpoints_dir / f"{material_id}_KPOINTS"

    kpoints.write_file(str(output_path))

    return output_path


# ============================================================
# Argument parser
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch missing KPOINTS files from Materials Project."
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Candidate CSV containing a material_id column.",
    )

    parser.add_argument(
        "--kpoints-dir",
        required=True,
        help="Directory containing existing KPOINTS files.",
    )

    parser.add_argument(
        "--ids-file",
        default=None,
        help=(
            "Optional text file with one material_id per line, "
            "or CSV containing a material_id column."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Report missing KPOINTS without downloading "
            "or writing files."
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between API requests (default: 0.5).",
    )

    return parser.parse_args()

def fetch_kpoints(
    material_id: str,
    mpr: MPRester,
) -> str:
    """
    Fetch the MPRelaxSet KPOINTS text for one material.
    """
    structure = mpr.get_structure_by_material_id(material_id)

    if structure is None:
        raise ValueError(
            f"Structure not found for material_id: {material_id}"
        )

    vis = MPRelaxSet(structure)

    return vis.kpoints.__str__()


# ============================================================
# Main
# ============================================================

def main():
    args = parse_args()

    csv_path = Path(args.csv)
    kpoints_dir = Path(args.kpoints_dir)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file does not exist: {csv_path}"
        )

    kpoints_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Load candidate material IDs
    # ---------------------------------------------------------
    if args.ids_file:
        candidate_ids = load_ids_file(Path(args.ids_file))
    else:
        candidate_ids = load_material_ids_from_csv(csv_path)

    # ---------------------------------------------------------
    # Find existing KPOINTS
    # ---------------------------------------------------------
    existing_ids = get_existing_kpoints_ids(kpoints_dir)

    missing_ids = [
        material_id
        for material_id in candidate_ids
        if material_id not in existing_ids
    ]

    print("=" * 60)
    print("FETCH MISSING KPOINTS")
    print("=" * 60)

    print(f"Candidate material IDs : {len(candidate_ids)}")
    print(f"Existing KPOINTS       : {len(existing_ids)}")
    print(f"Missing KPOINTS        : {len(missing_ids)}")
    print(f"KPOINTS directory      : {kpoints_dir}")

    if not missing_ids:
        print("\nNo missing KPOINTS files.")
        return

    print("\nMissing material IDs:")
    for material_id in missing_ids:
        print(f"  {material_id}")

    # ---------------------------------------------------------
    # Dry run
    # ---------------------------------------------------------
    if args.dry_run:
        print("\nDry run enabled.")
        print("No files downloaded or written.")
        return

    # ---------------------------------------------------------
    # Materials Project API
    # ---------------------------------------------------------
    load_dotenv()

    api_key = os.getenv("MP_API_KEY")

    if not api_key:
        raise RuntimeError(
            "MP_API_KEY is not set in the environment."
        )

    # ---------------------------------------------------------
    # Download KPOINTS
    # ---------------------------------------------------------
    successful = 0
    failed = 0

    with MPRester(api_key) as mpr:

        for i, material_id in enumerate(missing_ids, start=1):

            print(
                f"\n[{i}/{len(missing_ids)}] "
                f"Fetching {material_id}"
            )

            try:
                kpoints_text = fetch_kpoints(
                    material_id,
                    mpr,
                )

                output_path = (
                    kpoints_dir
                    / f"{material_id}_KPOINTS"
                )

                output_path.write_text(
                    kpoints_text,
                    encoding="utf-8",
                )

                print(
                    f"  Saved: {output_path.name}"
                )

                successful += 1

                # Small delay to avoid unnecessary API pressure
                time.sleep(0.2)

            except Exception as exc:
                failed += 1

                print(
                    f"  ERROR: {material_id}: {exc}"
                )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"Candidates : {len(candidate_ids)}")
    print(f"Existing   : {len(existing_ids)}")
    print(f"Missing    : {len(missing_ids)}")
    print(f"Downloaded : {successful}")
    print(f"Failed     : {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()



def main(args):
    """
    Main workflow:

    1. Load candidate material IDs.
    2. Detect existing KPOINTS.
    3. Determine missing IDs.
    4. In dry-run mode, report them only.
    5. Otherwise fetch and write missing KPOINTS files.
    """

    csv_path = Path(args.csv)
    kpoints_dir = Path(args.kpoints_dir)

    # --------------------------------------------------------
    # Prepare output directory
    # --------------------------------------------------------

    kpoints_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Load candidate IDs
    # --------------------------------------------------------

    if args.ids_file:
        candidate_ids = load_ids_file(Path(args.ids_file))
    else:
        #candidate_ids = load_material_ids_from_csv(csv_path)
        candidate_ids = load_material_ids_from_csv(Path(args.csv))

    # --------------------------------------------------------
    # Find existing KPOINTS
    # --------------------------------------------------------

    existing_ids = get_existing_kpoints_ids(kpoints_dir)

    # --------------------------------------------------------
    # Find missing KPOINTS
    # --------------------------------------------------------

    missing_ids = [
        material_id
        for material_id in candidate_ids
        if material_id not in existing_ids
    ]

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print("=" * 60)
    print("FETCH MISSING KPOINTS")
    print("=" * 60)

    print(f"Candidate material IDs : {len(candidate_ids)}")
    print(f"Existing KPOINTS       : {len(existing_ids)}")
    print(f"Missing KPOINTS        : {len(missing_ids)}")
    print(f"KPOINTS directory      : {kpoints_dir}")
    print(f"Dry run                : {args.dry_run}")

    print("=" * 60)

    # --------------------------------------------------------
    # Nothing to download
    # --------------------------------------------------------

    if not missing_ids:
        print("No missing KPOINTS files.")
        print("Nothing to download.")
        return

    # --------------------------------------------------------
    # Show missing IDs
    # --------------------------------------------------------

    print("\nMissing material IDs:")
    for material_id in missing_ids:
        print(f"  {material_id}")

    # --------------------------------------------------------
    # Dry-run: stop here
    # --------------------------------------------------------

    if args.dry_run:
        print("\nDry-run enabled.")
        print("No files were downloaded or written.")
        return

    # --------------------------------------------------------
    # Load Materials Project API key
    # --------------------------------------------------------

    load_dotenv()

    api_key = os.getenv("MP_API_KEY")

    if not api_key:
        raise RuntimeError(
            "MP_API_KEY was not found in the environment."
        )

    # --------------------------------------------------------
    # Download missing KPOINTS
    # --------------------------------------------------------

    print("\nStarting download...")
    print("-" * 60)

    success_count = 0
    failed_count = 0

    with MPRester(api_key) as mpr:

        for index, material_id in enumerate(
            missing_ids,
            start=1,
        ):

            print(
                f"[{index}/{len(missing_ids)}] "
                f"{material_id}"
            )

            try:

                output_path = download_file(
                    material_id=material_id,
                    kpoints_dir=kpoints_dir,
                    mpr=mpr,
                )

                print(
                    f"  SUCCESS: {output_path.name}"
                )

                success_count += 1

            except Exception as exc:

                print(
                    f"  FAILED: {material_id}"
                )

                print(
                    f"  Reason: {exc}"
                )

                failed_count += 1

            # Avoid sending requests too rapidly.
            if index < len(missing_ids):
                time.sleep(args.delay)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"Candidate material IDs : {len(candidate_ids)}")
    print(f"Already existed        : {len(candidate_ids) - len(missing_ids)}")
    print(f"Missing before run     : {len(missing_ids)}")
    print(f"Downloaded successfully: {success_count}")
    print(f"Failed                  : {failed_count}")
    print(f"KPOINTS directory      : {kpoints_dir}")

    print("=" * 60)


# ============================================================
# Direct execution
# ============================================================

if __name__ == "__main__":
    args = parse_args()
    main(args)
