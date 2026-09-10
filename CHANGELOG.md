# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-09-07

### Added

- Stage 1: Materials Project search for magnetic ABO RP-space-group candidates.
- Stage 2: Construction of VASP scan inputs.
- Magnetic transition-metal detection and MAGMOM generation.
- INCAR and KPOINTS handling.
- VASP optimization and DOS calculation directory generation.
- Optional POTCAR generation for HPC environments.
- Utility for downloading missing KPOINTS files.
- Automated output tests.
- Slurm submission script for Stage 1.
- Project documentation and citation metadata.

### Notes

- VASP pseudopotential files are not included in this repository.
- Large datasets and generated VASP calculation outputs are excluded from version control.
