#!/bin/bash
# Prepare an owned A100 runtime; submit this inside a CPU Slurm allocation.
set -euo pipefail
: "${SLURM_JOB_ID:?Prepare the runtime in a compute allocation}"
: "${RUNTIME_ROOT:?New private directory on approved shared storage}"
umask 077
project=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime=$(realpath -m "$RUNTIME_ROOT")
uv=$(command -v "${UV_BIN:-uv}")
uv=$(readlink -f "$uv")
if [ -n "${APPTAINER_MODULE-apptainer/1.4.4}" ]; then
    module load "${APPTAINER_MODULE-apptainer/1.4.4}"
fi
command -v apptainer >/dev/null
mkdir -m 700 "$runtime"
mkdir "$runtime/cache" "$runtime/tmp"
export APPTAINER_CACHEDIR="$runtime/cache"
export APPTAINER_TMPDIR="$runtime/tmp"
image=docker://slimerl/slime@sha256:6379b872c6cc2535fb8c0e073a79bb1f41e365ca4859dd308e99ba14eb87936d
printf '%s\n' "$image" > "$runtime/base-image.txt"
apptainer version > "$runtime/apptainer-version.txt"
# A directory runtime avoids the expensive SIF compression step.
apptainer build --sandbox "$runtime/rootfs" "$image" \
    2>&1 | tee "$runtime/image-preparation.log"
mkdir -p "$runtime/rootfs/edot-project" "$runtime/rootfs/edot-runtime" \
    "$runtime/rootfs/edot-tools"
touch "$runtime/rootfs/edot-tools/uv"
export APPTAINERENV_UV_BIN=/edot-tools/uv
export APPTAINERENV_TMPDIR=/edot-runtime/tmp
export APPTAINERENV_UV_CACHE_DIR=/edot-runtime/cache/uv
export APPTAINERENV_RUNTIME_BUILD_RECORD=/edot-runtime/build
export APPTAINERENV_SLURM_JOB_ID="$SLURM_JOB_ID"
export APPTAINERENV_DISTILLATION_BUILD_JOBS=${DISTILLATION_BUILD_JOBS:-6}
apptainer exec --writable --no-home --pwd /edot-project \
    --bind "$project:/edot-project:ro,$runtime:/edot-runtime,$uv:/edot-tools/uv:ro" \
    "$runtime/rootfs" bash /edot-project/scripts/init-distillation-a100.sh \
    2>&1 | tee "$runtime/build.log"
printf 'Built runtime: %s/rootfs\nRun the GPU probe before using it for training.\n' "$runtime"
