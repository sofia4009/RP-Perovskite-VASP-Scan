#!/usr/bin/env bash
# One-command HPC pipeline launcher for the RP-Perovskite-VASP-Scan project.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/config/hpc_config.sh"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "ERROR: ${CONFIG_FILE} not found. Copy config/hpc_config.example.sh to config/hpc_config.sh and edit it." >&2
  exit 2
fi

# shellcheck disable=SC1090
source "${CONFIG_FILE}"

: "${PYTHON_BIN:=python}"
: "${MP_API_KEY_FILE:=${HOME}/.mp_api_key}"
: "${WORK_ROOT:=${PROJECT_ROOT}/work}"
: "${STAGE1_OUTPUT:=${WORK_ROOT}/stage1}"
: "${STAGE2_OUTPUT:=${WORK_ROOT}/stage2}"
: "${VASP_COMMAND:=gerun vasp_std}"
: "${QSUB_COMMAND:=qsub}"
: "${SCHEDULER:=sge}"
: "${SUBMIT_JOBS:=true}"
: "${REBUILD_INPUTS:=false}"

LOG_DIR="${WORK_ROOT}/logs"
JOB_DIR="${WORK_ROOT}/jobs"
mkdir -p "${LOG_DIR}" "${JOB_DIR}"
LOG_FILE="${WORK_ROOT}/pipeline.log"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(timestamp)] $*" | tee -a "${LOG_FILE}"; }
fail() { log "ERROR: $*"; exit 1; }

run_logged() {
  log "RUN: $*"
  "$@" 2>&1 | tee -a "${LOG_FILE}"
}

[[ -x "${PYTHON_BIN}" || -n "$(command -v "${PYTHON_BIN}" 2>/dev/null || true)" ]] || fail "Python not found: ${PYTHON_BIN}"
[[ -f "${PROJECT_ROOT}/src/01_search_magnetic_ABO_RP_spacegroup_candidates.py" ]] || fail "Stage 1 script missing"
[[ -f "${PROJECT_ROOT}/src/02_build_scan_vasp_inputs.py" ]] || fail "Stage 2 script missing"
[[ -f "${PROJECT_ROOT}/scripts/validate_stage2.py" ]] || fail "validate_stage2.py missing"
[[ -f "${PROJECT_ROOT}/scripts/prepare_dos.py" ]] || fail "prepare_dos.py missing"
[[ -f "${MP_API_KEY_FILE}" ]] || fail "Materials Project API key file not found: ${MP_API_KEY_FILE}"
[[ -s "${MP_API_KEY_FILE}" ]] || fail "Materials Project API key file is empty: ${MP_API_KEY_FILE}"
[[ -d "${PP_ROOT}" ]] || fail "PP_ROOT is not a directory: ${PP_ROOT}"

if [[ "${SCHEDULER}" != "sge" ]]; then
  fail "This implementation currently supports SGE only; set SCHEDULER=sge."
fi
if ! command -v "${QSUB_COMMAND}" >/dev/null 2>&1; then
  if [[ "${SUBMIT_JOBS}" == "true" ]]; then
    fail "Configured qsub command is not available: ${QSUB_COMMAND}"
  else
    log "WARNING: qsub not found; SUBMIT_JOBS=false so continuing in preparation-only mode."
  fi
fi

if [[ -n "${MODULE_LOAD_CMD:-}" ]]; then eval "${MODULE_LOAD_CMD}"; fi
if [[ -n "${CONDA_ACTIVATE_CMD:-}" ]]; then eval "${CONDA_ACTIVATE_CMD}"; fi

export MP_API_KEY="$(tr -d '[:space:]' < "${MP_API_KEY_FILE}")"
[[ -n "${MP_API_KEY}" ]] || fail "MP API key resolved to an empty value"
umask 077

log "Pipeline start"
log "Project root: ${PROJECT_ROOT}"
log "Work root: ${WORK_ROOT}"
log "Stage 1: ${STAGE1_OUTPUT}"
log "Stage 2: ${STAGE2_OUTPUT}"
log "PP_ROOT: ${PP_ROOT}"
log "SUBMIT_JOBS: ${SUBMIT_JOBS}"

find_stage1_dir() {
  local root="${STAGE1_OUTPUT}"
  local cif incar kpoints
  cif="${root}/structures/cif"
  incar="${root}/inputs/mprelax_incar"
  kpoints="${root}/inputs/mprelax_kpoints"
  if [[ -d "${cif}" && -d "${incar}" && -d "${kpoints}" ]]; then
    printf '%s\n' "${kpoints}"
    return 0
  fi
  # Compatibility fallback for older output layouts: locate the unique KPOINTS directory.
  mapfile -t candidates < <(find "${root}/inputs" -mindepth 1 -maxdepth 2 -type f -name '*_KPOINTS' -printf '%h\n' 2>/dev/null | sort -u)
  if (( ${#candidates[@]} == 1 )) && [[ -d "${cif}" && -d "${incar}" ]]; then
    printf '%s\n' "${candidates[0]}"
    return 0
  fi
  return 1
}

count_files() { find "$1" -maxdepth 1 -type f -name "$2" | wc -l; }

validate_stage1() {
  local cif_dir="${STAGE1_OUTPUT}/structures/cif"
  local incar_dir="${STAGE1_OUTPUT}/inputs/mprelax_incar"
  local kpoints_dir
  kpoints_dir="$(find_stage1_dir || true)"
  [[ -d "${cif_dir}" ]] || fail "Stage 1 CIF directory missing: ${cif_dir}"
  [[ -d "${incar_dir}" ]] || fail "Stage 1 INCAR directory missing: ${incar_dir}"
  [[ -n "${kpoints_dir}" && -d "${kpoints_dir}" ]] || fail "Stage 1 KPOINTS directory could not be located"

  local cif_count incar_count kp_count
  cif_count="$(count_files "${cif_dir}" '*.cif')"
  incar_count="$(count_files "${incar_dir}" '*_INCAR')"
  kp_count="$(count_files "${kpoints_dir}" '*_KPOINTS')"
  log "Stage 1 counts: CIF=${cif_count}, INCAR=${incar_count}, KPOINTS=${kp_count}"
  (( cif_count > 0 && cif_count == incar_count && incar_count == kp_count )) || fail "Stage 1 validation failed: counts must be equal and > 0"
  printf '%s\n%s\n%s\n' "${cif_dir}" "${incar_dir}" "${kpoints_dir}"
}

if [[ "${REBUILD_INPUTS}" != "true" && -d "${STAGE1_OUTPUT}" ]]; then
  log "Stage 1 output exists; validating/reusing because REBUILD_INPUTS=${REBUILD_INPUTS}."
  if ! mapfile -t STAGE1_PATHS < <(validate_stage1); then
    fail "Existing Stage 1 output is invalid. Set REBUILD_INPUTS=true to rebuild it."
  fi
else
  rm -rf "${STAGE1_OUTPUT}"
  mkdir -p "${STAGE1_OUTPUT}"
  run_logged "${PYTHON_BIN}" "${PROJECT_ROOT}/src/01_search_magnetic_ABO_RP_spacegroup_candidates.py" --output-dir "${STAGE1_OUTPUT}"
  mapfile -t STAGE1_PATHS < <(validate_stage1)
fi

CIF_DIR="${STAGE1_PATHS[0]}"
INCAR_DIR="${STAGE1_PATHS[1]}"
KPOINTS_DIR="${STAGE1_PATHS[2]}"

if [[ "${REBUILD_INPUTS}" != "true" && -d "${STAGE2_OUTPUT}" ]]; then
  log "Stage 2 output exists; validating/reusing because REBUILD_INPUTS=${REBUILD_INPUTS}."
else
  mkdir -p "${STAGE2_OUTPUT}"
  run_logged "${PYTHON_BIN}" "${PROJECT_ROOT}/src/02_build_scan_vasp_inputs.py" \
    --cif-dir "${CIF_DIR}" \
    --incar-dir "${INCAR_DIR}" \
    --kpoints-dir "${KPOINTS_DIR}" \
    --output-dir "${STAGE2_OUTPUT}" \
    --pp-root "${PP_ROOT}" \
    --strict
fi

run_logged "${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/validate_stage2.py" --stage2-dir "${STAGE2_OUTPUT}" --phase pre

MANIFEST="${STAGE2_OUTPUT}/structure_manifest.txt"
find "${STAGE2_OUTPUT}" -mindepth 2 -maxdepth 2 -type d -name '*_*/' >/dev/null 2>&1 || true
find "${STAGE2_OUTPUT}" -mindepth 2 -maxdepth 2 -type d -name 'optimization' -printf '%h\n' | sort > "${MANIFEST}"
[[ -s "${MANIFEST}" ]] || fail "No structures found for optimization"
STRUCTURE_COUNT="$(wc -l < "${MANIFEST}")"
log "Optimization manifest: ${STRUCTURE_COUNT} structures"

if [[ "${SUBMIT_JOBS}" != "true" ]]; then
  log "SUBMIT_JOBS=false: input generation and validation complete; no VASP jobs submitted."
  log "Pipeline preparation finished successfully."
  exit 0
fi

cat > "${JOB_DIR}/opt_array.sh" <<'JOB'
#!/usr/bin/env bash
set -u
set -o pipefail
MANIFEST="$1"
VASP_COMMAND="$2"
LOG_ROOT="$3"
TASK_ID="${SGE_TASK_ID:-1}"
STRUCTURE="$(sed -n "${TASK_ID}p" "$MANIFEST")"
STATUS_DIR="${LOG_ROOT}/status"
mkdir -p "$STATUS_DIR"
if [[ -z "$STRUCTURE" || ! -d "$STRUCTURE/optimization" ]]; then echo "invalid manifest task $TASK_ID" > "$STATUS_DIR/opt_${TASK_ID}.failed"; exit 1; fi
cd "$STRUCTURE/optimization" || exit 1
for f in POSCAR INCAR KPOINTS POTCAR; do [[ -s "$f" ]] || { echo "missing $f" > "$STATUS_DIR/opt_${TASK_ID}.failed"; exit 1; }; done
if [[ -s CONTCAR ]]; then echo "$STRUCTURE" > "$STATUS_DIR/opt_${TASK_ID}.success"; exit 0; fi
LOG="$STATUS_DIR/opt_${TASK_ID}.log"
eval "$VASP_COMMAND" >"$LOG" 2>&1
rc=$?
if [[ $rc -eq 0 && -s CONTCAR ]]; then echo "$STRUCTURE" > "$STATUS_DIR/opt_${TASK_ID}.success"; exit 0; fi
echo "VASP exit=$rc; valid CONTCAR not found" > "$STATUS_DIR/opt_${TASK_ID}.failed"
exit 1
JOB
chmod +x "${JOB_DIR}/opt_array.sh"

cat > "${JOB_DIR}/prepare_array.sh" <<'JOB'
#!/usr/bin/env bash
set -u
MANIFEST="$1"
PYTHON_BIN="$2"
PROJECT_ROOT="$3"
LOG_ROOT="$4"
TASK_ID="${SGE_TASK_ID:-1}"
STRUCTURE="$(sed -n "${TASK_ID}p" "$MANIFEST")"
mkdir -p "$LOG_ROOT/status"
if [[ -z "$STRUCTURE" ]]; then exit 1; fi
if [[ ! -s "$STRUCTURE/optimization/CONTCAR" ]]; then echo "$STRUCTURE" > "$LOG_ROOT/status/dosprep_${TASK_ID}.failed"; exit 1; fi
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/prepare_dos.py" --structure-dir "$STRUCTURE" > "$LOG_ROOT/status/dosprep_${TASK_ID}.log" 2>&1
rc=$?
if [[ $rc -eq 0 && -s "$STRUCTURE/dos/POSCAR" ]]; then echo "$STRUCTURE" > "$LOG_ROOT/status/dosprep_${TASK_ID}.success"; exit 0; fi
echo "$STRUCTURE" > "$LOG_ROOT/status/dosprep_${TASK_ID}.failed"
exit 1
JOB
chmod +x "${JOB_DIR}/prepare_array.sh"

cat > "${JOB_DIR}/dos_array.sh" <<'JOB'
#!/usr/bin/env bash
set -u
set -o pipefail
MANIFEST="$1"
VASP_COMMAND="$2"
LOG_ROOT="$3"
TASK_ID="${SGE_TASK_ID:-1}"
STRUCTURE="$(sed -n "${TASK_ID}p" "$MANIFEST")"
mkdir -p "$LOG_ROOT/status"
if [[ -z "$STRUCTURE" || ! -d "$STRUCTURE/dos" ]]; then echo "$STRUCTURE" > "$LOG_ROOT/status/dos_${TASK_ID}.failed"; exit 1; fi
cd "$STRUCTURE/dos" || exit 1
for f in POSCAR INCAR KPOINTS POTCAR; do [[ -s "$f" ]] || { echo "missing $f" > "$LOG_ROOT/status/dos_${TASK_ID}.failed"; exit 1; }; done
if [[ -s vasprun.xml || -s DOSCAR ]]; then echo "$STRUCTURE" > "$LOG_ROOT/status/dos_${TASK_ID}.success"; exit 0; fi
LOG="$LOG_ROOT/status/dos_${TASK_ID}.log"
eval "$VASP_COMMAND" >"$LOG" 2>&1
rc=$?
if [[ $rc -eq 0 && -s DOSCAR ]]; then echo "$STRUCTURE" > "$LOG_ROOT/status/dos_${TASK_ID}.success"; exit 0; fi
echo "VASP exit=$rc; DOSCAR not found" > "$LOG_ROOT/status/dos_${TASK_ID}.failed"
exit 1
JOB
chmod +x "${JOB_DIR}/dos_array.sh"

qsub_common=("${QSUB_COMMAND}" -cwd -terse)
qsub_resource_args() {
  local wall="$1" pe="$2" slots="$3" queue="$4"
  QARGS=(-l "h_rt=${wall}" -pe "${pe}" "${slots}")
  [[ -n "$queue" ]] && QARGS+=(-q "$queue")
}

qsub_resource_args "${OPT_WALLTIME}" "${OPT_PE}" "${OPT_SLOTS}" "${OPT_QUEUE}"
OPT_JOB_ID="$("${qsub_common[@]}" -N "${OPT_JOB_NAME}" -t "1-${STRUCTURE_COUNT}" "${QARGS[@]}" "${JOB_DIR}/opt_array.sh" "${MANIFEST}" "${VASP_COMMAND}" "${LOG_DIR}" | tail -n1 | tr -d '[:space:]')"
log "Optimization job submitted: ${OPT_JOB_ID}"

qsub_resource_args "${PREP_WALLTIME}" "${PREP_PE}" "${PREP_SLOTS}" "${PREP_QUEUE}"
PREP_JOB_ID="$("${qsub_common[@]}" -N "${PREP_JOB_NAME}" -hold_jid "${OPT_JOB_ID}" -t "1-${STRUCTURE_COUNT}" "${QARGS[@]}" "${JOB_DIR}/prepare_array.sh" "${MANIFEST}" "${PYTHON_BIN}" "${PROJECT_ROOT}" "${LOG_DIR}" | tail -n1 | tr -d '[:space:]')"
log "DOS preparation job submitted: ${PREP_JOB_ID} (holds on ${OPT_JOB_ID})"

qsub_resource_args "${DOS_WALLTIME}" "${DOS_PE}" "${DOS_SLOTS}" "${DOS_QUEUE}"
DOS_JOB_ID="$("${qsub_common[@]}" -N "${DOS_JOB_NAME}" -hold_jid "${PREP_JOB_ID}" -t "1-${STRUCTURE_COUNT}" "${QARGS[@]}" "${JOB_DIR}/dos_array.sh" "${MANIFEST}" "${VASP_COMMAND}" "${LOG_DIR}" | tail -n1 | tr -d '[:space:]')"
log "DOS job submitted: ${DOS_JOB_ID} (holds on ${PREP_JOB_ID})"

log "Pipeline submission complete. Monitor SGE jobs ${OPT_JOB_ID}, ${PREP_JOB_ID}, ${DOS_JOB_ID}."
