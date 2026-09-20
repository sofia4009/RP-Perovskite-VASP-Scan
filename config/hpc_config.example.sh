#!/usr/bin/env bash
# Copy to config/hpc_config.sh and edit for your HPC environment.
# Do not commit hpc_config.sh; it is ignored by Git.

PYTHON_BIN="python"
MP_API_KEY_FILE="${HOME}/.mp_api_key"
PP_ROOT="/path/to/potpaw_PBE.64"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${PROJECT_ROOT}/work"
STAGE1_OUTPUT="${WORK_ROOT}/stage1"
STAGE2_OUTPUT="${WORK_ROOT}/stage2"

# Scheduler / VASP. This project currently targets SGE by default.
VASP_COMMAND="gerun vasp_std"
QSUB_COMMAND="qsub"
SCHEDULER="sge"
SUBMIT_JOBS="true"
REBUILD_INPUTS="false"

# Optional environment setup. Leave empty if the login/compute environment is already ready.
MODULE_LOAD_CMD=""
CONDA_ACTIVATE_CMD=""

# SGE resource settings.
OPT_WALLTIME="48:00:00"
OPT_PE="mpi"
OPT_SLOTS="120"
OPT_QUEUE=""

PREP_WALLTIME="00:30:00"
PREP_PE="smp"
PREP_SLOTS="1"
PREP_QUEUE=""

DOS_WALLTIME="24:00:00"
DOS_PE="mpi"
DOS_SLOTS="120"
DOS_QUEUE=""

# Optional names for submitted jobs.
OPT_JOB_NAME="rp_scan_opt"
PREP_JOB_NAME="rp_scan_dosprep"
DOS_JOB_NAME="rp_scan_dos"
