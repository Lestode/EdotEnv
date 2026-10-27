#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=00:30:00
set -euo pipefail
: "${PROJECT_ROOT:?}"
: "${BASELINE_MODEL:?}"
: "${BASELINE_DATA:?}"
: "${RUN_ROOT:?}"
: "${RUNTIME_IMAGE:?}"
module load apptainer/1.4.4
umask 077
mkdir "$RUN_ROOT"
srun apptainer exec --nv --bind "$PROJECT_ROOT,$BASELINE_MODEL,$BASELINE_DATA,$RUN_ROOT" \
    "$RUNTIME_IMAGE" bash "$PROJECT_ROOT/scripts/distillation-baseline-inner.sh"
