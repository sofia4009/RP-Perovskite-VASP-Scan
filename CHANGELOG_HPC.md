## HPC pipeline addition

- Added configurable HPC settings for SGE, VASP, Materials Project credentials, and pseudopotential root.
- Added pre/post Stage 2 validation that correctly treats `dos/POSCAR` as a post-optimization artifact.
- Added `prepare_dos.py` to copy `optimization/CONTCAR` into `dos/POSCAR` and optionally carry forward `CHGCAR`.
- Added restart-safe one-command SGE submission orchestration with optimization, DOS-preparation, and DOS arrays.
