#!/bin/bash
# Keep the public image immutable; install A100 additions in an external uv venv.
set -euo pipefail
: "${SLURM_JOB_ID:?Use a compute allocation}"
: "${PROJECT_ROOT:?Initialized checkout}"
: "${RUNTIME_ROOT:?New shared runtime directory}"
module load eth_proxy
uv=$(readlink -f "$(command -v "${UV_BIN:-uv}")")
umask 077
mkdir -m 700 "$RUNTIME_ROOT"
mkdir "$RUNTIME_ROOT/cache" "$RUNTIME_ROOT/tmp"
export APPTAINER_CACHEDIR="$RUNTIME_ROOT/cache"
# Many small extraction files belong on Slurm-provided node-local storage.
: "${TMPDIR:?Request local scratch with sbatch --tmp}"
export RUNTIME_LOCAL_TMP
RUNTIME_LOCAL_TMP=$(mktemp -d "$TMPDIR/edot-runtime.XXXXXX")
export APPTAINER_TMPDIR="$RUNTIME_LOCAL_TMP"
export APPTAINERENV_TMPDIR="$RUNTIME_LOCAL_TMP"
df -h "$RUNTIME_LOCAL_TMP" > "$RUNTIME_ROOT/local-storage.txt"
image=docker://slimerl/slime@sha256:6379b872c6cc2535fb8c0e073a79bb1f41e365ca4859dd308e99ba14eb87936d
printf '%s\n' "$image" > "$RUNTIME_ROOT/base-image.txt"
apptainer version > "$RUNTIME_ROOT/apptainer-version.txt"
if [ -n "${DISTILLATION_BASE_SIF:-}" ]; then
    base_sif=$(realpath -e "$DISTILLATION_BASE_SIF")
    test "$(cat "$(dirname "$base_sif")/base-image.txt")" = "$image"
    apptainer inspect "$base_sif" > "$RUNTIME_ROOT/reused-image-inspect.txt"
    sha256sum "$base_sif" > "$RUNTIME_ROOT/reused-image-sha256.txt"
    ln -s "$base_sif" "$RUNTIME_ROOT/base.sif"
else
    apptainer pull "$RUNTIME_ROOT/base.sif" "$image" 2>&1 | tee "$RUNTIME_ROOT/pull.log"
fi
export RUNTIME_ENV="$RUNTIME_ROOT/venv"
export UV_BIN="$uv"
apptainer exec --bind "$PROJECT_ROOT,$RUNTIME_ROOT,$RUNTIME_LOCAL_TMP,$uv:$uv:ro" \
    "$RUNTIME_ROOT/base.sif" bash "$PROJECT_ROOT/scripts/init-distillation-euler-venv.sh" \
    2>&1 | tee "$RUNTIME_ROOT/venv.log"
