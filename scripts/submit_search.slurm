#!/bin/bash -l

#$ -P Gold
#$ -A QMUL_GHASEMI
#$ -S /bin/bash
#$ -l h_rt=48:00:0
#$ -l mem=4G
#$ -pe mpi 120
#$ -N RP_search
#$ -cwd

set -e

echo "============================================================"
echo "RP MATERIALS PROJECT SEARCH"
echo "============================================================"

# ------------------------------------------------------------
# User-configurable paths
# ------------------------------------------------------------

PROJECT_ROOT="${PROJECT_ROOT:-/data/home/qp24582/Material_Project}"

OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/search_output}"

PYTHON_SCRIPT="${PYTHON_SCRIPT:-${PROJECT_ROOT}/src/01_search_rp_perovskites.py}"

# Optional:
# export MP_API_KEY="..."

# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

export OMP_NUM_THREADS=1

module unload -f compilers mpi
module load mpi/intel/2019/update5/intel
module load compilers/intel/2019/update5

# ------------------------------------------------------------
# Information
# ------------------------------------------------------------

echo "Project root : ${PROJECT_ROOT}"
echo "Python script: ${PYTHON_SCRIPT}"
echo "Output dir   : ${OUTPUT_DIR}"

mkdir -p "${OUTPUT_DIR}"

# ------------------------------------------------------------
# Run search
# ------------------------------------------------------------

python "${PYTHON_SCRIPT}" \
    --output-dir "${OUTPUT_DIR}"

echo "============================================================"
echo "SEARCH FINISHED"
echo "============================================================"
