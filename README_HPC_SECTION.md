## HPC one-command pipeline

The repository can be run as a restartable SGE workflow after one-time HPC configuration.

```bash
git clone https://github.com/sofia4009/RP-Perovskite-VASP-Scan.git
cd RP-Perovskite-VASP-Scan
cp config/hpc_config.example.sh config/hpc_config.sh
# edit config/hpc_config.sh
bash scripts/run_pipeline.sh
```

The pipeline performs Materials Project search, Stage 1 validation, SCAN input generation, POTCAR validation, optimization submission, per-task `CONTCAR` detection, DOS preparation, and DOS submission. `dos/POSCAR` is intentionally absent immediately after Stage 2: it is created only from the relaxed `optimization/CONTCAR`. The pseudopotential library must already exist on the HPC and is selected through `PP_ROOT`; POTCAR files are never downloaded or committed.
