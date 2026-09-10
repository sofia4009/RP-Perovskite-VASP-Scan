# RP Perovskite VASP Scan

Automated workflow for identifying RP-type perovskite candidates
from the Materials Project and preparing VASP SCAN calculations.

## 1. Overview

This project provides a reproducible workflow for:

- identifying candidate RP perovskite materials,
- retrieving required Materials Project data,
- preparing VASP input files,
- detecting magnetic transition-metal systems,
- generating SCAN relaxation and DOS calculation inputs,
- preparing batch submission scripts.

## 2. Workflow

The workflow is divided into several stages:

1. Materials Project search and candidate generation
2. VASP input preparation
3. Missing KPOINTS retrieval
4. Validation and tests
5. HPC submission

## 3. Repository Structure

```text
src/
tools/
scripts/
tests/
legacy/

## 4. Requirements

### Software

- Python 3
- VASP 6.3.0 or compatible VASP version
- Git

### Python packages

- pymatgen
- mp-api
- ASE
- pandas
- python-dotenv

### External services

A Materials Project API key is required for retrieving data from the
Materials Project API.

VASP calculations require a valid VASP installation and appropriate
pseudopotential files.

## 5. Materials Project

The workflow uses the Materials Project API to retrieve material
information and VASP-related input data.

An API key is required for API-based operations.

The API key should be provided through an environment variable or
`.env` file and must not be committed to the repository.

## 6. VASP

The generated calculation directories contain the standard VASP input
files required by the workflow, including:

- POSCAR
- INCAR
- KPOINTS
- POTCAR

POTCAR files are generated from the local pseudopotential library and
are intentionally excluded from version control.

## 7. Magnetic Systems

The workflow identifies structures containing magnetic transition
metals, including Fe, Mn, Co, Ni, and Cu.

For magnetic systems, the magnetic moments provided by the Materials
Project INCAR are preserved and used to construct the MAGMOM setting.

Non-magnetic systems are handled according to the selected strictness
mode.

## 8. SCAN Relaxation

The workflow generates SCAN-based VASP input files for geometry
relaxation.

The relaxation setup includes the SCAN meta-GGA functional and the
corresponding convergence, ionic relaxation, magnetic, and electronic
settings implemented in the Stage 02 input builder.

## 9. DOS Calculation

A separate static VASP calculation setup is generated for DOS
calculations.

The DOS setup uses the converged structure and charge density from the
optimization calculation and applies the DOS-specific INCAR settings
implemented in the workflow.

## 10. KPOINTS

The utility

tools/fetch_missing_kpoints.py

compares candidate material IDs with the existing KPOINTS files and
downloads only the missing KPOINTS files from the Materials Project.

The utility supports:

- CSV input
- optional material-ID files
- dry-run mode
- detection of already existing KPOINTS files

## 11. Testing

Basic repository integrity tests are provided under:

tests/

The tests verify that:

- forbidden hard-coded material IDs are not present in non-legacy code
- sensitive and generated files are covered by `.gitignore`
- repository-specific integrity checks pass when the test script is
  executed directly

## 12. Data and Generated Files

Large, generated, and sensitive computational files are not included
in version control.

The repository excludes files and directories such as:

- .env
- POTCAR
- WAVECAR
- CHGCAR
- OUTCAR
- Python cache files
- data_test/

Generated calculation data should be stored outside the Git repository.

## 13. Reproducibility

The workflow is organized into separate stages so that candidate
selection, input preparation, missing-file retrieval, and validation
can be executed independently.

Material IDs and input data should be generated through the provided
scripts rather than relying on manually modified calculation files.

## 14. Legacy Code

Original scripts are retained separately under:

legacy/

The legacy directory is preserved for reference and comparison with
the refactored workflow.

New development should use the non-legacy scripts under src/, tools/,
scripts/, and tests/.

## 15. License

License information will be added before the first public release.

## 16. Citation

If you use this software in research, please cite this repository.

Citation metadata will be provided in:

CITATION.cff

