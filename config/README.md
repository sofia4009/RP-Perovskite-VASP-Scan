# HPC configuration

Copy the template once:

```bash
cp config/hpc_config.example.sh config/hpc_config.sh
```

Edit `config/hpc_config.sh` for the target cluster. In particular set:

- `PYTHON_BIN`: Python executable or absolute path.
- `PP_ROOT`: real VASP PAW pseudopotential root. Never commit POTCAR files.
- `VASP_COMMAND`: command that launches VASP inside a compute job, e.g. `gerun vasp_std`.
- `QSUB_COMMAND`: scheduler submission command; the current implementation targets SGE.
- walltime, parallel environment, slot count, and optional queue for optimization and DOS.
- `SUBMIT_JOBS=false` for input-only/mock testing; this still performs Stage 1/2 validation but does not submit VASP jobs.

The real `hpc_config.sh` is ignored by Git. Do not place credentials in it.

The pipeline deliberately does not assume a particular cluster filesystem. All generated work is placed under `WORK_ROOT` unless you configure another path.
